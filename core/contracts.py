from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    text: str = Field(min_length=1)
    source: str = Field(min_length=1)
    locator: str = Field(min_length=1, description="Page, URL locator, or position")
    score_sem: Optional[float] = None
    score_bm25: Optional[float] = None


class RetrievalOutput(BaseModel):
    run_id: str = Field(min_length=1)
    evidence_chunks: List[Evidence] = Field(default_factory=list)


class ReasonCode(str, Enum):
    NO_TESTABLE_RELATION = "NO_TESTABLE_RELATION"
    LOW_DIVERSITY = "LOW_DIVERSITY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    TOO_VAGUE = "TOO_VAGUE"


class ExtractionOutput(BaseModel):
    run_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1, max_length=200)
    variables: List[str] = Field(min_length=2)
    var_types: List[str] = Field(description="numeric|categorical|binary per variable")
    methods: List[str] = Field(description="ranked methods compatible with var types")
    assumptions: List[str] = Field(default_factory=list)
    evidence_refs: List[int] = Field(min_length=2)
    notes: Optional[str] = None

    @field_validator("var_types")
    @classmethod
    def _validate_var_types(cls, v, info):
        if not v:
            raise ValueError("var_types cannot be empty")
        allowed = {"numeric", "categorical", "binary"}
        for t in v:
            if t not in allowed:
                raise ValueError("var_types must be one of numeric|categorical|binary")
        return v

    @field_validator("variables")
    @classmethod
    def _validate_variables(cls, v):
        if len(v) < 2:
            raise ValueError("At least two variables required")
        return v

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence_refs(cls, v):
        if len(v) < 2:
            raise ValueError("At least two evidence_refs required")
        return v


class ExtractionError(BaseModel):
    run_id: str = Field(min_length=1)
    reason_code: ReasonCode
    message: str


