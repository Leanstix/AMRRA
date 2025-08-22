from ast import Add
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field

class Config:
    allow_population_by_field_name = True

class GroupRaw(BaseModel):
    name: str
    values: List[float] = Field(..., alias="data")

    model_config = {
        "populate_by_name": True,
        "alias_generator": None
    }

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

    # For chi-square goodness-of-fit
    data: Optional[List[int]] = None
    expected: Optional[List[int]] = None

    # For regression analysis
    independent_variable: Optional[List[float]] = None
    dependent_variable: Optional[List[float]] = None

    allow_simulation: bool = True

    model_config = {
        "populate_by_name": True
    }

    # validation for regression
    def validate_regression(self):
        if self.test == "regression":
            if not self.independent_variable or not self.dependent_variable:
                raise ValueError("Both independent_variable and dependent_variable must be provided for regression.")
            if len(self.independent_variable) != len(self.dependent_variable):
                raise ValueError("Independent and dependent variables must have the same length.")

class ExperimentOutput(BaseModel):
    # High-level context
    hypothesis: str
    variables: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    # Core statistical results
    test_used: str
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[Union[List[List[float]], List[float]]] = None
    estimate: Optional[Union[List[float], float]] = None
    df: Optional[Union[float, List[int]]] = None
    confidence_score: float = 0.0

    # Metadata
    method_notes: Optional[str] = None
    conclusion: str
    quality_flags: List[str] = []
    plots: Optional[List[str]] = None
    gpt5_explanation: Optional[str] = None
    summary: Optional[str] = None
