import uuid
import numpy as np
import faiss
from rank_bm25 import BM25Okapi

from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import CohereEmbeddings

from model.extractor_model import Evidence, RetrievalOutput
from .schema import Chunk
from .utils import RetrieverUtils,chunk_text
from .store import RetrieverPersistence
from .config import OPENAI_API_KEY, COHERE_API_KEY, EMBED_MODEL

class RetrieverEngine:
    SOURCES = ("pdf", "url")

    def __init__(self):
        if OPENAI_API_KEY:
            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        elif COHERE_API_KEY:
            self._embeddings = CohereEmbeddings(model=EMBED_MODEL, cohere_api_key=COHERE_API_KEY)
        else:
            raise RuntimeError("No API key found for embeddings.")

        self.dim = len(self._embeddings.embed_query("dimension-check-phrase"))
        self.faiss_indices = {src: faiss.IndexFlatIP(self.dim) for src in self.SOURCES}
        self.chunks = {src: [] for src in self.SOURCES}
        self._bm25 = {src: None for src in self.SOURCES}
        self._texts_for_bm25 = {src: [] for src in self.SOURCES}

        RetrieverPersistence.load(self.chunks, self.faiss_indices, self._bm25, self._texts_for_bm25, self.SOURCES)

    # -------- Persistence --------
    def save(self):
        RetrieverPersistence.save(self.chunks, self.SOURCES)

    # -------- Ingest --------
    def ingest_batch(self, items, source_type: str, chunk_size=500, chunk_overlap=100):
        if source_type not in self.SOURCES:
            raise ValueError(f"Invalid source_type: {source_type}")

        existing_ids = {c.doc_id for c in self.chunks[source_type]}
        items = [it for it in items if it["doc_id"] not in existing_ids]
        if not items:
            return {"added_docs": 0, "added_chunks": 0, "chunks_total": len(self.chunks[source_type])}

        new_chunks, texts = [], []

        for it in items:
            chunk_data = chunk_text(it["text"], chunk_size, chunk_overlap, it["doc_id"], it.get("title"), it.get("meta", {}))
            for c in chunk_data:
                c["text"] = RetrieverUtils.filter_irrelevant_numbers(c["text"])
                if not c["text"]:
                    continue
                chunk = Chunk(**c)
                chunk.tokens = RetrieverUtils.tokenize(chunk.text)
                texts.append(chunk.text)
                new_chunks.append(chunk)

        embeddings = self._embeddings.embed_documents(texts)
        for i, vec in enumerate(embeddings):
            new_chunks[i].vector = RetrieverUtils.normalize_vector(np.array(vec, dtype=np.float32))
            self.faiss_indices[source_type].add(new_chunks[i].vector.reshape(1, -1))

        self.chunks[source_type].extend(new_chunks)
        self._texts_for_bm25[source_type] = [c.tokens for c in self.chunks[source_type]]
        self._bm25[source_type] = BM25Okapi(self._texts_for_bm25[source_type])

        return {
            "added_docs": len(items),
            "added_chunks": len(new_chunks),
            "chunks_total": len(self.chunks[source_type]),
        }

    # -------- Retrieval --------
    def retrieve(self, query: str, k=5, alpha=0.5, source_type="pdf", doc_ids=None):
        if source_type not in self.SOURCES or not self.chunks[source_type]:
            return []

        candidates = [c for c in self.chunks[source_type] if not doc_ids or c.doc_id in doc_ids]
        if not candidates:
            return []

        n_docs = len(candidates)
        qv = RetrieverUtils.normalize_vector(np.array(self._embeddings.embed_query(query), dtype=np.float32)).reshape(1, -1)
        top_n = min(max(k * 5, 50), n_docs)

        bm25 = BM25Okapi([c.tokens for c in candidates])
        bm25_scores = np.array(bm25.get_scores(RetrieverUtils.tokenize(query)))
        bm25_idx = np.argsort(-bm25_scores)[:top_n]

        if not doc_ids:
            D, I = self.faiss_indices[source_type].search(qv, top_n)
            vec_idx, vec_scores = I[0], D[0]
            valid = vec_idx < len(self.chunks[source_type])
            vec_idx, vec_scores = vec_idx[valid], vec_scores[valid]
            cand_idx = np.unique(np.concatenate([vec_idx, bm25_idx]))
            v = np.array([vec_scores[list(vec_idx).index(idx)] if idx in vec_idx else 0.0 for idx in cand_idx])
            b = np.array([bm25_scores[idx] if idx in bm25_idx else 0.0 for idx in cand_idx])
        else:
            cand_idx = bm25_idx
            v, b = np.zeros(len(cand_idx)), bm25_scores[cand_idx]

        hybrid_scores = alpha * v + (1 - alpha) * b
        order = np.argsort(-hybrid_scores)[:min(k, len(cand_idx))]

        results = []
        for idx_pos in order:
            idx = int(cand_idx[idx_pos])
            chunk = candidates[idx]
            clean_text = RetrieverUtils.filter_irrelevant_numbers(chunk.text)
            if not clean_text:
                continue
            results.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "text": clean_text,
                "score_hybrid": float(hybrid_scores[idx_pos]),
                "meta": chunk.meta,
            })
        return results

    # -------- Format for extractor --------
    def format_for_extractor(self, query: str, source_type: str, run_id: str = None, k=5, alpha=0.5, doc_ids=None):
        hits = self.retrieve(query, k=k, alpha=alpha, source_type=source_type, doc_ids=doc_ids)
        if not hits:
            return None

        evidence_chunks = []
        for h in hits:
            clean_text = RetrieverUtils.filter_irrelevant_numbers(h["text"])
            if not clean_text:
                continue
            evidence_chunks.append(Evidence(
                chunk_id=h["chunk_id"],
                doc_id=h["doc_id"],
                text=clean_text,
                title=h.get("title"),
                meta=h.get("meta", {}),
            ))

        if len(evidence_chunks) < 3:
            return None

        import re
        numeric_tokens = re.findall(r"\d+(\.\d+)?", " ".join([c.text for c in evidence_chunks]))
        provenance = {
            "alpha": alpha,
            "k": k,
            "embedding_model": EMBED_MODEL,
            "source_type": source_type,
            "chunks_indexed": len(self.chunks[source_type]),
            "chunks_used": len(evidence_chunks),
        }
        if len(set(numeric_tokens)) < 2:
            provenance["force_test"] = "descriptive"

        return RetrievalOutput(
            run_id=run_id or str(uuid.uuid4()),
            query=query,
            evidence_chunks=evidence_chunks,
            provenance=provenance,
        )
engine = RetrieverEngine()