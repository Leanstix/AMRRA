from typing import Any, List, Optional
from pydantic import BaseModel, Field

class ResultData(BaseModel):
    hypothesis: str
    variables: Optional[List[str]] = None
    evidence: Optional[List[str]] = None
    test_used: str
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[List[List[float]]] = None
    estimate: Optional[List[float]] = None
    df: Optional[List[int]] = None
    confidence_score: Optional[float] = None
    method_notes: Optional[str] = None
    conclusion: str
    quality_flags: Optional[List[str]] = None
    plots: Optional[Any] = None

class ExperimentData(BaseModel):
    status: str
    result: ResultData
    explanation: Optional[str] = None