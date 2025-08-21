# retriever.py
import os
import uuid
import pickle
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

from utils import chunk_text
from model.extractor_model import Evidence, RetrievalOutput

# Optional embeddings
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import CohereEmbeddings

# ---------------- ENV + CONFIG ----------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
PERSIST_DIR = os.getenv("RETRIEVER_PERSIST_DIR", "./persist")
os.makedirs(PERSIST_DIR, exist_ok=True)
EPS = 1e-12

# ---------------- DATA STRUCT ----------------
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    meta: Dict[str, Any]
    vector: Optional[np.ndarray] = None
    tokens: Optional[List[str]] = None
    score_bm25: float = 0.0
    score_vec: float = 0.0
    score_hybrid: float = 0.0

# ---------------- RETRIEVER ----------------
class RetrieverEngine:
    SOURCES = ("pdf", "url")

    def __init__(self):
        if OPENAI_API_KEY:
            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        elif COHERE_API_KEY:
            self._embeddings = CohereEmbeddings(model=EMBED_MODEL, cohere_api_key=COHERE_API_KEY)
            logging.warning("Using Cohere embeddings as fallback.")
        else:
            raise RuntimeError("No API key found for OpenAI or Cohere embeddings.")

        self.dim = len(self._embeddings.embed_query("dimension-check-phrase"))
        self.faiss_indices: Dict[str, faiss.IndexFlatIP] = {src: faiss.IndexFlatIP(self.dim) for src in self.SOURCES}

        self.chunks: Dict[str, List[Chunk]] = {src: [] for src in self.SOURCES}
        self._bm25: Dict[str, Optional[BM25Okapi]] = {src: None for src in self.SOURCES}
        self._texts_for_bm25: Dict[str, List[List[str]]] = {src: [] for src in self.SOURCES}

        self._load_meta()

    # ---------------- Persistence ----------------
    def save(self):
        meta = {"chunks": {src: [c.__dict__ for c in self.chunks[src]] for src in self.SOURCES}}
        with open(os.path.join(PERSIST_DIR, "meta.pkl"), "wb") as f:
            pickle.dump(meta, f)
        logging.info("Retriever state saved.")

    def _load_meta(self):
        path = os.path.join(PERSIST_DIR, "meta.pkl")
        if not os.path.exists(path):
            logging.warning("No retriever state found.")
            return
        try:
            with open(path, "rb") as f:
                meta = pickle.load(f)
            for src in self.SOURCES:
                self.chunks[src] = []
                for c in meta.get("chunks", {}).get(src, []):
                    chunk = Chunk(**c)
                    if chunk.vector is not None:
                        chunk.vector = np.array(chunk.vector, dtype=np.float32)
                        self.faiss_indices[src].add(chunk.vector.reshape(1, -1))
                    if chunk.tokens:
                        self._texts_for_bm25[src].append(chunk.tokens)
                    self.chunks[src].append(chunk)
                if self._texts_for_bm25[src]:
                    self._bm25[src] = BM25Okapi(self._texts_for_bm25[src])
            logging.info("Retriever metadata loaded.")
        except Exception as e:
            logging.exception(f"Failed to load retriever metadata: {e}")

    # ---------------- Utilities ----------------
    @staticmethod
    def _tokenize(text: str):
        return text.lower().split()

    @staticmethod
    def _normalize_vector(v: np.ndarray):
        norm = np.linalg.norm(v)
        return v / (norm + EPS)

    # ---------------- Ingest ----------------
    def ingest_batch(self, items: List[Dict[str, Any]], source_type: str, chunk_size=500, chunk_overlap=100):
        if source_type not in self.SOURCES:
            raise ValueError(f"Invalid source_type: {source_type}")

        existing_ids = {c.doc_id for c in self.chunks[source_type]}
        items = [it for it in items if it["doc_id"] not in existing_ids]
        if not items:
            return {"added_docs": 0, "added_chunks": 0, "chunks_total": len(self.chunks[source_type])}

        new_chunks: List[Chunk] = []
        texts = []

        for it in items:
            chunk_data = chunk_text(it["text"], chunk_size, chunk_overlap, it["doc_id"], it.get("title"), it.get("meta", {}))
            for c in chunk_data:
                chunk = Chunk(**c)
                chunk.tokens = self._tokenize(chunk.text)
                texts.append(chunk.text)
                new_chunks.append(chunk)

        # Embeddings
        embeddings = self._embeddings.embed_documents(texts)
        for i, vec in enumerate(embeddings):
            new_chunks[i].vector = self._normalize_vector(np.array(vec, dtype=np.float32))
            self.faiss_indices[source_type].add(new_chunks[i].vector.reshape(1, -1))

        # Add chunks
        self.chunks[source_type].extend(new_chunks)

        # Rebuild BM25
        self._texts_for_bm25[source_type] = [c.tokens for c in self.chunks[source_type]]
        self._bm25[source_type] = BM25Okapi(self._texts_for_bm25[source_type])

        return {
            "added_docs": len(items),
            "added_chunks": len(new_chunks),
            "chunks_total": len(self.chunks[source_type]),
        }

    # ---------------- Retrieval ----------------
    def retrieve(self, query: str, k=5, alpha=0.5, source_type="pdf"):
        if source_type not in self.SOURCES or not self.chunks[source_type]:
            return []

        n_docs = len(self.chunks[source_type])
        qv = self._normalize_vector(np.array(self._embeddings.embed_query(query), dtype=np.float32)).reshape(1, -1)
        top_n = min(max(k * 5, 50), n_docs)

        # FAISS
        D, I = self.faiss_indices[source_type].search(qv, top_n)
        vec_idx, vec_scores = I[0], D[0]
        valid = vec_idx < n_docs
        vec_idx, vec_scores = vec_idx[valid], vec_scores[valid]

        # BM25
        bm25_scores = np.array(self._bm25[source_type].get_scores(self._tokenize(query)))
        bm25_idx = np.argsort(-bm25_scores)[:top_n]

        # Hybrid scoring
        cand_idx = np.unique(np.concatenate([vec_idx, bm25_idx]))
        v = np.array([vec_scores[list(vec_idx).index(idx)] if idx in vec_idx else 0.0 for idx in cand_idx])
        b = np.array([bm25_scores[idx] if idx in bm25_idx else 0.0 for idx in cand_idx])
        hybrid_scores = alpha * v + (1 - alpha) * b
        order = np.argsort(-hybrid_scores)[:min(k, len(cand_idx))]

        results = []
        for idx_pos in order:
            idx = int(cand_idx[idx_pos])
            chunk = self.chunks[source_type][idx]
            results.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "text": chunk.text,
                "score_hybrid": float(hybrid_scores[idx_pos]),
                "meta": chunk.meta,
            })
        return results

    # ---------------- Format for extractor ----------------
    def format_for_extractor(self, query: str, source_type: str, run_id: str = None, k=5, alpha=0.5):
        hits = self.retrieve(query, k=k, alpha=alpha, source_type=source_type)
        if not hits:
            return None

        evidence_chunks = [
            Evidence(
                chunk_id=h["chunk_id"],
                doc_id=h["doc_id"],
                text=h["text"],
                title=h.get("title"),
                meta=h.get("meta", {}),
            )
            for h in hits
        ]

        return RetrievalOutput(
            run_id=run_id or str(uuid.uuid4()),
            query=query,
            evidence_chunks=evidence_chunks,
            provenance={
                "alpha": alpha,
                "k": k,
                "embedding_model": EMBED_MODEL,
                "source_type": source_type,
                "chunks_indexed": len(self.chunks[source_type]),
            },
        )

# ---------------- Singleton ----------------
engine = RetrieverEngine()
