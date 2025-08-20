import os
import uuid
import pickle
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv

from utils import chunk_text, extract_pdf_text, fetch_and_clean_url

load_dotenv()
logging.basicConfig(level=logging.INFO)

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
PERSIST_DIR = os.getenv("RETRIEVER_PERSIST_DIR", "./persist")
os.makedirs(PERSIST_DIR, exist_ok=True)
EPS = 1e-12

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    meta: Dict[str, Any]
    score_bm25: float = 0.0
    score_vec: float = 0.0
    score_hybrid: float = 0.0

class RetrieverEngine:
    def __init__(self):
        if not COHERE_API_KEY:
            raise RuntimeError("COHERE_API_KEY env var is required")
        self.embeddings = CohereEmbeddings(model=EMBED_MODEL, cohere_api_key=COHERE_API_KEY)
        self.dim = len(self.embeddings.embed_query("test"))

        # Separate FAISS indices and BM25 lists per source type
        self.faiss_indices = {
            "pdf": faiss.IndexFlatIP(self.dim),
            "url": faiss.IndexFlatIP(self.dim),
            "text": faiss.IndexFlatIP(self.dim),
        }
        self.chunks: Dict[str, List[Chunk]] = {"pdf": [], "url": [], "text": []}
        self._texts_for_bm25: Dict[str, List[str]] = {"pdf": [], "url": [], "text": []}
        self._bm25: Dict[str, BM25Okapi] = {"pdf": None, "url": None, "text": None}

    # ---------------- Persistence ----------------
    def save(self):
        for src in ["pdf", "url", "text"]:
            faiss.write_index(self.faiss_indices[src], os.path.join(PERSIST_DIR, f"faiss_{src}.index"))
        with open(os.path.join(PERSIST_DIR, "meta.pkl"), "wb") as f:
            pickle.dump({"chunks": self.chunks, "texts_for_bm25": self._texts_for_bm25}, f)
        logging.info("Retriever state saved.")

    def load(self) -> bool:
        loaded = False
        for src in ["pdf", "url", "text"]:
            idx_path = os.path.join(PERSIST_DIR, f"faiss_{src}.index")
        meta_path = os.path.join(PERSIST_DIR, "meta.pkl")
        if os.path.exists(idx_path) and os.path.exists(meta_path):
            for src in ["pdf", "url", "text"]:
                self.faiss_indices[src] = faiss.read_index(os.path.join(PERSIST_DIR, f"faiss_{src}.index"))
            with open(meta_path, "rb") as f:
                meta = pickle.load(f)
                self.chunks = meta.get("chunks", {"pdf": [], "url": [], "text": []})
                self._texts_for_bm25 = meta.get("texts_for_bm25", {"pdf": [], "url": [], "text": []})
            for src in ["pdf", "url", "text"]:
                if self._texts_for_bm25[src]:
                    self._bm25[src] = BM25Okapi([self._tokenize(t) for t in self._texts_for_bm25[src]])
            logging.info("Retriever state loaded.")
            loaded = True
        return loaded

    # ---------------- Utilities ----------------
    @staticmethod
    def _tokenize(text: str):
        return text.lower().split()

    @staticmethod
    def _normalize_matrix(vectors: np.ndarray):
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + EPS
        return vectors / norms

    # ---------------- Ingestion ----------------
    def ingest_items(self, doc_id: str, title: str, text: str, meta: Dict[str, Any], chunk_size=500, chunk_overlap=100):
        source_type = meta.get("source_type")
        if source_type not in ["pdf", "url", "text"]:
            raise ValueError("meta.source_type must be 'pdf', 'url', or 'text'")

        # Avoid duplicate doc_id in same source
        if any(c.doc_id == doc_id for c in self.chunks[source_type]):
            return {"added": 0, "chunks_total": len(self.chunks[source_type])}

        chunks_data = chunk_text(text, chunk_size, chunk_overlap, doc_id, title, meta)
        chunks_objs = [Chunk(**c) for c in chunks_data]
        texts_for_bm25 = [c["text"] for c in chunks_data]

        # Embeddings
        embed_texts = [c.text for c in chunks_objs]
        vecs = np.array(self.embeddings.embed_documents(embed_texts), dtype=np.float32)
        self._add_chunks(source_type, chunks_objs, vecs, texts_for_bm25)
        return {"added": len(chunks_objs), "chunks_total": len(self.chunks[source_type])}

    def _add_chunks(self, source_type: str, chunks: List[Chunk], vecs: np.ndarray, texts_for_bm25: List[str]):
        if not chunks:
            return
        vecs = self._normalize_matrix(vecs)
        self.faiss_indices[source_type].add(vecs.astype("float32"))

        self.chunks[source_type].extend(chunks)
        self._texts_for_bm25[source_type].extend(texts_for_bm25)
        self._bm25[source_type] = BM25Okapi([self._tokenize(t) for t in self._texts_for_bm25[source_type]])

    # ---------------- Retrieval ----------------
    def retrieve(self, query: str, k=5, alpha=0.5, source_type="url"):
        if source_type not in ["pdf", "url", "text"]:
            raise ValueError("source_type must be 'pdf', 'url', or 'text'")

        if not self.chunks[source_type]:
            return []

        qv = np.array(self.embeddings.embed_query(query), dtype=np.float32).reshape(1, -1)
        qv /= np.linalg.norm(qv) + EPS

        top_n = min(max(k * 5, 50), len(self.chunks[source_type]))
        D, I = self.faiss_indices[source_type].search(qv.astype("float32"), top_n)
        vec_idx, vec_scores = I[0], D[0]
        vec_idx, vec_scores = vec_idx[vec_idx >= 0], vec_scores[vec_idx >= 0]

        bm25_scores = np.zeros(len(self.chunks[source_type]), dtype=np.float32)
        if self._bm25[source_type]:
            bm25_scores = np.array(self._bm25[source_type].get_scores(self._tokenize(query)), dtype=np.float32)
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:top_n]

        cand_idx = np.unique(np.concatenate([vec_idx, top_bm25_idx]))
        if cand_idx.size == 0:
            return []

        v, b = np.zeros(len(self.chunks[source_type])), np.zeros(len(self.chunks[source_type]))
        if vec_idx.size:
            v_scaled = (vec_scores - vec_scores.min()) / (vec_scores.max() - vec_scores.min() + EPS)
            v[vec_idx] = v_scaled
        if bm25_scores.size:
            b_scaled = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + EPS)
            b = b_scaled

        hybrid = alpha * v[cand_idx] + (1 - alpha) * b[cand_idx]
        order = np.argsort(-hybrid)

        results, seen_docs = [], set()
        for idx_pos in order:
            if len(results) >= k:
                break
            idx = int(cand_idx[idx_pos])
            chunk = self.chunks[source_type][idx]
            seen_docs.add(chunk.doc_id)
            results.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "text": chunk.text,
                "score_bm25": float(b[idx]),
                "score_vec": float(v[idx]),
                "score_hybrid": float(hybrid[idx_pos]),
                "meta": chunk.meta or {}
            })
        return results

    # ---------------- Helpers ----------------
    def wipe(self, source_type=None):
        if source_type in ["pdf", "url", "text"]:
            self.faiss_indices[source_type] = faiss.IndexFlatIP(self.dim)
            self.chunks[source_type].clear()
            self._texts_for_bm25[source_type].clear()
            self._bm25[source_type] = None
        else:
            for src in ["pdf", "url", "text"]:
                self.faiss_indices[src] = faiss.IndexFlatIP(self.dim)
                self.chunks[src].clear()
                self._texts_for_bm25[src].clear()
                self._bm25[src] = None

# ---------------- Initialize ----------------
engine = RetrieverEngine()
try:
    engine.load()
except Exception:
    logging.warning("Failed to load existing retriever state, starting fresh.")
