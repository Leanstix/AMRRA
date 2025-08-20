from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class GroupRaw(BaseModel):
    name: str
    values: List[float]

class GroupSummary(BaseModel):
    name: str
    mean: float
    sd: float
    n: int

class TwoSampleInput(BaseModel):
    hypothesis: str
    variables: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    test: Literal["ttest", "chi2", "anova", "regression", "logistic"] = "ttest"
    groups_raw: Optional[List[GroupRaw]] = None
    groups_summary: Optional[List[GroupSummary]] = None
    contingency: Optional[List[List[int]]] = None
    alpha: float = Field(0.05, ge=1e-6, le=0.5)
    allow_simulation: bool = True

class ExperimentOutput(BaseModel):
    # High-level context
    hypothesis: str
    variables: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    # Core statistical results
    test_used: str
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    estimate: Optional[float] = None
    df: Optional[float] = None
    confidence_score: float = 0.0 

    # Metadata
    method_notes: Optional[str] = None
    conclusion: str
    quality_flags: List[str] = []
    plots: Optional[List[str]] = None
