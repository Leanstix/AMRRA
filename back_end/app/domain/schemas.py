from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StageName(str, Enum):
    INGESTION = "ingestion"
    RETRIEVAL = "retrieval"
    EXTRACTION = "extraction"
    PLANNING = "planning"
    EXPERIMENTATION = "experimentation"
    JUDGING = "judging"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceInput(BaseModel):
    kind: Literal["text", "url"]
    title: str = ""
    content: str | None = None
    url: str | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.kind == "text" and not (self.content and self.content.strip()):
            raise ValueError("text sources require non-empty content")
        if self.kind == "url" and not self.url:
            raise ValueError("url sources require a url")
        return self


class RunRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    sources: list[SourceInput] = Field(min_length=1, max_length=12)
    top_k: int = Field(default=8, ge=3, le=20)


class EvidenceChunk(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str = ""
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    name: str
    role: Literal["outcome", "predictor", "group", "count", "unknown"] = "unknown"
    value_type: Literal["raw_numeric", "summary", "categorical_count", "binary", "unknown"] = "unknown"
    group: str | None = None
    values: list[float] = Field(default_factory=list)
    mean: float | None = None
    sd: float | None = None
    n: int | None = Field(default=None, ge=1)
    count: int | None = Field(default=None, ge=0)
    category: str | None = None
    unit: str | None = None
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("evidence_chunk_ids")
    @classmethod
    def unique_evidence_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str = Field(min_length=3)
    variables: list[str] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    notes: str = ""


class ExperimentPlan(BaseModel):
    hypothesis_id: str
    test: Literal["welch_ttest", "anova", "chi_square", "linear_regression", "descriptive"]
    rationale: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    evidence_chunk_ids: list[str] = Field(default_factory=list)


class ExperimentResult(BaseModel):
    hypothesis_id: str
    test_used: str
    status: Literal["completed", "insufficient_data", "failed"]
    statistic: float | None = None
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    effect_size: float | None = None
    confidence_interval: list[float] | None = None
    estimate: float | list[float] | None = None
    degrees_of_freedom: float | list[float] | None = None
    conclusion: str
    quality_flags: list[str] = Field(default_factory=list)
    method_notes: str = ""
    evidence_chunk_ids: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    chunk_id: str
    claim: str


class JudgeReport(BaseModel):
    title: str
    summary: str
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class TraceEvent(BaseModel):
    event_id: str
    run_id: str
    stage: StageName
    status: StageStatus
    started_at: datetime
    ended_at: datetime | None = None
    latency_ms: int | None = None
    model: str | None = None
    prompt_version: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    retry_count: int = 0
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    run_id: str
    query: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None
    error_message: str | None = None
    evidence: list[EvidenceChunk] = Field(default_factory=list)
    extraction: ExtractionResult | None = None
    plans: list[ExperimentPlan] = Field(default_factory=list)
    experiments: list[ExperimentResult] = Field(default_factory=list)
    report: JudgeReport | None = None
    traces: list[TraceEvent] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: bool
    agent_provider_configured: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
