import os
import pickle
import numpy as np
from .config import PERSIST_DIR
from .schema import Chunk


class RetrieverPersistence:

    @staticmethod
    def _get_file_path(doc_id: str, source_type: str):
        """
        Ensure unique file naming by including source_type.
        Example: <persist_dir>/<doc_id>__<source_type>.pkl
        """
        os.makedirs(PERSIST_DIR, exist_ok=True)
        return os.path.join(PERSIST_DIR, f"{doc_id}__{source_type}.pkl")

    @staticmethod
    def save_chunk(chunk: Chunk, doc_id: str, source_type: str):
        """
        Save a chunk into its corresponding file.
        """
        path = RetrieverPersistence._get_file_path(doc_id, source_type)

        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
        else:
            data = {"chunks": []}

        data["chunks"].append(chunk.__dict__)

        with open(path, "wb") as f:
            pickle.dump(data, f)

    @staticmethod
    def load_doc(doc_id: str, source_type: str):
        """
        Load all chunks for a given (doc_id, source_type).
        """
        path = RetrieverPersistence._get_file_path(doc_id, source_type)
        if not os.path.exists(path):
            return []

        with open(path, "rb") as f:
            data = pickle.load(f)

        chunks = []
        for c in data.get("chunks", []):
            chunk = Chunk(**c)
            if chunk.vector is not None:
                chunk.vector = np.array(chunk.vector, dtype=np.float32)
            chunks.append(chunk)
        return chunks
