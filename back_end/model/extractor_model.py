from __future__ import annotations
from typing import List, Dict, Any, Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field


# =========================================================
# Extraction Models
# =========================================================
class Evidence(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = None


class RetrievalOutput(BaseModel):
    query: str
    evidence_chunks: List[Evidence]  # pipeline must feed this
    provenance: Dict[str, Any]
    run_id: Optional[str] = None


class ExtractionOutput(BaseModel):
    run_id: str
    hypotheses: List[Dict[str, Any]]  # each dict: hypothesis + variables + evidence
    notes: Optional[str] = ""
    provenance: Optional[dict] = {}


class ExtractionError(BaseModel):
    error: str
    reason_code: str
    details: Optional[Dict[str, Any]] = None


class ReasonCode(str):
    MISSING_DATA = "missing_data"
    INVALID_FORMAT = "invalid_format"
    EXTRACTION_FAILED = "extraction_failed"


__all__ = [
    "Evidence",
    "RetrievalOutput",
    "ExtractionOutput",
    "ExtractionError",
    "ReasonCode",
]
