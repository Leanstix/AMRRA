from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import faiss
import numpy as np


class HybridIndex:
    def __init__(self, dim: int):
        # Vector index
        self.dim = dim
        self.faiss_index = faiss.IndexFlatIP(dim) # cosine via normalized vectors
        self.vec_ids: List[int] = []
        self.vec_meta: List[Dict[str, Any]] = []
        # BM25 index
        self.bm25 = None
        self.bm25_corpus_tokens: List[List[str]] = []
        self.bm25_meta: List[Dict[str, Any]] = []
        # book-keeping
        self._next_id = 0

    def _tokenize(self, text: str) -> List[str]:
        return [t.lower() for t in text.split()]

    def add(self, embeddings: np.ndarray, metas: List[Dict[str, Any]], texts: List[str]):
        # normalize embeddings for cosine similarity via inner product
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        normed = embeddings / norms
        self.faiss_index.add(normed.astype('float32'))
        start_id = self._next_id
        n = embeddings.shape[0]
        self.vec_ids.extend(list(range(start_id, start_id + n)))
        self.vec_meta.extend(metas)
        self._next_id += n
        # BM25
        tokens = [self._tokenize(t) for t in texts]
        self.bm25_corpus_tokens.extend(tokens)
        self.bm25_meta.extend(metas)
        self.bm25 = BM25Okapi(self.bm25_corpus_tokens)

    def search(self, query: str, k: int, alpha: float = 0.5) -> List[Tuple[int, float, float, Dict[str, Any]]]:
        # BM25 scores
        q_tokens = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(q_tokens) if self.bm25 else []
        # Vector scores
        # We'll need the query embedding from caller, so this method only merges; see retriever.py
        raise NotImplementedError("Use search_with_query_embedding")

    def search_with_query_embedding(self, query_vec: np.ndarray, k: int, alpha: float = 0.5):
        # normalize
        q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
        D, I = self.faiss_index.search(q.astype('float32').reshape(1, -1), k=max(k, 50))
        vec_scores = D[0] # inner products in [-1,1]
        vec_idx = I[0]
        # Collect BM25 for all corpus
        if self.bm25 is None:
            return []
        bm25_scores = np.array(self.bm25.get_scores(self.bm25._tokenizer(" "))) # placeholder; not used
            # We'll combine by re-scoring the **union** of top-k vector and all bm25 top-k
            # Simpler approach: compute bm25 over subset: use titles/text stored in meta
            # For speed, we approximate by computing bm25 over all stored tokens and taking top candidates
            # Prepare candidate set
        bm25_all = np.array(self.bm25.get_scores(self.bm25._tokenizer("dummy")))
            # The above hack isn't ideal; instead expose a method that returns bm25 scores directly
        raise NotImplementedError