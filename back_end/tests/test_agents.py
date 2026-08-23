import pytest

from app.domain.schemas import EvidenceChunk, ExperimentResult
from app.providers.cohere import FakeProvider
from app.services.agents import ExtractorAgent, JudgeAgent


@pytest.mark.asyncio
async def test_extractor_drops_hallucinated_evidence_references():
    provider = FakeProvider([{
        "hypotheses": [
            {
                "statement": "Treatment improves recovery",
                "variables": ["recovery"],
                "evidence_chunk_ids": ["c1", "made-up"],
                "confidence": 0.9,
                "observations": [
                    {
                        "name": "recovery",
                        "role": "outcome",
                        "value_type": "raw_numeric",
                        "group": "A",
                        "values": [1, 2, 3],
                        "evidence_chunk_ids": ["made-up"],
                        "confidence": 0.9,
                    }
                ],
            }
        ],
        "notes": "",
    }])
    evidence = [EvidenceChunk(chunk_id="c1", source_id="s1", text="Treatment improved recovery.")]
    result = await ExtractorAgent(provider).run("Does treatment help?", evidence)
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].evidence_chunk_ids == ["c1"]
    assert result.hypotheses[0].observations == []


@pytest.mark.asyncio
async def test_judge_filters_unknown_citations_and_preserves_result_numbers():
    provider = FakeProvider([{
        "title": "Result",
        "summary": "The deterministic test was significant.",
        "conclusion": "Supported with limitations.",
        "confidence": 0.8,
        "limitations": ["small sample"],
        "citations": [
            {"chunk_id": "c1", "claim": "source claim"},
            {"chunk_id": "fake", "claim": "invented"},
        ],
    }])
    evidence = [EvidenceChunk(chunk_id="c1", source_id="s1", text="Evidence")]
    experiment = ExperimentResult(
        hypothesis_id="h1",
        test_used="Welch two-sample t-test",
        status="completed",
        p_value=0.01,
        effect_size=0.7,
        conclusion="significant",
        evidence_chunk_ids=["c1"],
    )
    report = await JudgeAgent(provider).run("query", evidence, [experiment])
    assert [c.chunk_id for c in report.citations] == ["c1"]
    assert report.confidence == 0.8
