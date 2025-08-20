from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# -------------- Ingestion --------------
class IngestItem(BaseModel):
    doc_id: str
    title: Optional[str] = None
    text: Optional[str] = None        # direct text
    url: Optional[str] = None         # web links
    file_path: Optional[str] = None   # PDFs, reports
    meta: Optional[dict] = None       # extra metadata (author, year, etc.)

class IngestRequest(BaseModel):
    items: List[IngestItem]

# Optional extended request for text chunking
class IngestTextRequest(BaseModel):
    items: List[IngestItem]
    chunk_size: int = 900
    chunk_overlap: int = 120

# -------------- Retrieval --------------
class RetrieveRequest(BaseModel):
    query: str
    k: int = 5
    alpha: float = 0.5  # weight for vector score vs BM25 (0..1)
    section_filter: Optional[str] = None

class ChunkOut(BaseModel):
    chunk_id: str
    doc_id: str
    title: Optional[str] = None
    text: str
    score_bm25: float
    score_vec: float
    score_hybrid: float
    meta: Dict[str, Any] = Field(default_factory=dict)

class RetrieveResponse(BaseModel):
    query: str
    results: List[ChunkOut]
    provenance: Dict[str, Any]
