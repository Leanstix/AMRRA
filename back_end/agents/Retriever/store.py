import os
import pickle
import numpy as np
import logging
from rank_bm25 import BM25Okapi
from .config import PERSIST_DIR
from .schema import Chunk

class RetrieverPersistence:

    @staticmethod
    def save(chunks, sources):
        meta = {"chunks": {src: [c.__dict__ for c in chunks[src]] for src in sources}}
        with open(os.path.join(PERSIST_DIR, "meta.pkl"), "wb") as f:
            pickle.dump(meta, f)
        logging.info("Retriever state saved.")

    @staticmethod
    def load(chunks, faiss_indices, bm25, texts_for_bm25, sources):
        path = os.path.join(PERSIST_DIR, "meta.pkl")
        if not os.path.exists(path):
            logging.warning("No retriever state found.")
            return

        with open(path, "rb") as f:
            meta = pickle.load(f)

        for src in sources:
            chunks[src] = []
            for c in meta.get("chunks", {}).get(src, []):
                chunk = Chunk(**c)
                if chunk.vector is not None:
                    chunk.vector = np.array(chunk.vector, dtype=np.float32)
                    faiss_indices[src].add(chunk.vector.reshape(1, -1))
                if chunk.tokens:
                    texts_for_bm25[src].append(chunk.tokens)
                chunks[src].append(chunk)
            if texts_for_bm25[src]:
                bm25[src] = BM25Okapi(texts_for_bm25[src])
        logging.info("Retriever metadata loaded.")
