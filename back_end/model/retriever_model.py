from __future__ import annotations
from typing import List, Optional, Dict, Any, TypedDict, Union
from pydantic import BaseModel, Field


# =========================================================
# Ingestion Models
# =========================================================
class IngestItem(BaseModel):
    doc_id: str
    title: Optional[str] = None
    
    url: Optional[str] = None         # web links
    file_path: Optional[str] = None   # PDFs, reports
    meta: Optional[dict] = None       # extra metadata (author, year, etc.)


class IngestRequest(BaseModel):
    items: List[IngestItem]


class IngestTextRequest(BaseModel):
    items: List[IngestItem]
    chunk_size: int = 900
    chunk_overlap: int = 120


# =========================================================
# Retrieval Models
# =========================================================
class RetrieveRequest(BaseModel):
    query: str
    k: int = 5
    alpha: float = 0.5
    section_filter: Union[str, List[str]] = "pdf"  # <-- accept str or list
    source_type: Optional[str] = None
    # NEW: allow direct evidence injection
    pdfs: Optional[List[Dict[str, str]]] = None   # [{"doc_id":.., "title":.., "content":..}]
    urls: Optional[List[Dict[str, str]]] = None   # [{"doc_id":.., "title":.., "content":..}]


class ChunkOut(BaseModel):
    chunk_id: str
    doc_id: str
    title: Optional[str] = None
    text: str
    meta: Dict[str, Any] = Field(default_factory=dict)

    # Retrieval-specific scores
    score_bm25: Optional[float] = None
    score_vec: Optional[float] = None
    score_hybrid: Optional[float] = None


class RetrieveResponse(BaseModel):
    query: str
    results: List[ChunkOut]  # This will be converted to Evidence in pipeline
    provenance: Dict[str, Any]


# =========================================================
# Variable Specification (Schemas, Configs)
# =========================================================
class VariableSpec(TypedDict, total=False):
    name: str
    type: str  # numeric | categorical | binary


__all__ = [
    # Ingestion
    "IngestItem",
    "IngestRequest",
    "IngestTextRequest",
    # Retrieval
    "RetrieveRequest",
    "ChunkOut",
    "RetrieveResponse",
    # Extra Specs
    "VariableSpec",
]
