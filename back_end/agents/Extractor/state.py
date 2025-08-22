from dataclasses import dataclass, field
from typing import List, Dict
from model.extractor_model import Evidence

@dataclass
class ExtractionState:
    run_id: str
    evidence_chunks: List[Evidence]
    usable: List[Evidence] = field(default_factory=list)
    structured_hypotheses: List[Dict] = field(default_factory=list)
