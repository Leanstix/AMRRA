from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, Field

class ResultData(BaseModel):
    hypothesis: str
    variables: Optional[List[str]] = Field(default=None, description="Variables involved in the test")
    evidence: Optional[List[str]] = Field(default=None, description="Supporting evidence or observations")
    test_used: str
    p_value: Optional[float] = Field(default=None, ge=0, le=1, description="P-value of the test")
    effect_size: Optional[float] = Field(default=None, description="Effect size measure")
    confidence_interval: Optional[List[Tuple[float, float]]] = Field(default=None, description="Confidence interval ranges")
    estimate: Optional[List[float]] = Field(default=None, description="Point estimates or means")
    df: Optional[List[int]] = Field(default=None, description="Degrees of freedom for the test")
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1, description="Calibrated confidence score")
    confidence_explanation: Optional[str] = Field(default=None, description="Explanation for confidence score")
    method_notes: Optional[str] = Field(default=None, description="Additional method details or caveats")
    conclusion: str
    quality_flags: Optional[List[str]] = Field(default=None, description="Quality checks or flags")
    plots: Optional[Any] = Field(default=None, description="Plot data or visualization objects")

class ExperimentData(BaseModel):
    status: str
    result: ResultData
    explanation: Optional[str] = Field(default=None, description="High-level explanation of the experiment outcome")
