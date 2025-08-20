from __future__ import annotations

from models import Evidence, ExtractionError, ExtractionOutput, ReasonCode, RetrievalOutput
from extractor import run_extraction


def _mk_ev(text: str, source: str, locator: str) -> Evidence:
    return Evidence(text=text, source=source, locator=locator)


def test_happy_path_returns_extraction_output():
    retrieval = RetrievalOutput(
        run_id="run-1",
        evidence_chunks=[
            _mk_ev("Treatment A improves recovery rate compared to baseline.", "paperA", "p.1"),
            _mk_ev("Recovery rate measured as percentage.", "paperB", "p.2"),
            _mk_ev("Control group had lower mean recovery.", "paperA", "p.3"),
            _mk_ev("Variance appears equal across groups.", "paperC", "p.4"),
        ],
    )

    result = run_extraction(retrieval)

    assert isinstance(result, ExtractionOutput)
    assert result.hypothesis and len(result.hypothesis) <= 200
    assert len(result.variables) >= 2
    assert len(result.methods) >= 1
    assert len(result.evidence_refs) >= 2
    # refs must be valid indices
    assert all(0 <= i < len(retrieval.evidence_chunks) for i in result.evidence_refs)


def test_low_diversity_or_insufficient_evidence():
    retrieval = RetrievalOutput(
        run_id="run-2",
        evidence_chunks=[
            _mk_ev("Some effect mentioned.", "one_source", "p.1"),
            _mk_ev("Another effect.", "one_source", "p.2"),
            _mk_ev("More details.", "one_source", "p.3"),
        ],
    )

    result = run_extraction(retrieval)
    assert isinstance(result, ExtractionError)
    assert result.reason_code in {ReasonCode.LOW_DIVERSITY, ReasonCode.INSUFFICIENT_EVIDENCE}


def test_insufficient_evidence():
    retrieval = RetrievalOutput(
        run_id="run-3",
        evidence_chunks=[
            _mk_ev("Only one chunk.", "s1", "p.1"),
            _mk_ev("Second but still insufficient?", "s1", "p.2"),
        ],
    )

    result = run_extraction(retrieval)
    assert isinstance(result, ExtractionError)
    assert result.reason_code == ReasonCode.INSUFFICIENT_EVIDENCE


