import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

EPS = 1e-12


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


# External models (already in model/extractor_model)
from model.extractor_model import Evidence, RetrievalOutput
