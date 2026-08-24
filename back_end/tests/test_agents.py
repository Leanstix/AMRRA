import pytest

from app.domain.schemas import EvidenceChunk, ExperimentResult
from app.providers.base import FakeProvider
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
async def test_extractor_recovers_when_primary_returns_no_hypothesis():
    provider = FakeProvider([
        {"hypotheses": [], "notes": "Primary pass was too conservative."},
        {
            "hypotheses": [
                {
                    "statement": "The documented intervention is associated with improved recovery.",
                    "variables": ["intervention", "recovery"],
                    "observations": [],
                    "evidence_chunk_ids": ["c1"],
                    "confidence": 0.72,
                }
            ],
            "notes": "Recovered a qualitative evidence-backed hypothesis.",
        },
    ])
    evidence = [
        EvidenceChunk(
            chunk_id="c1",
            source_id="s1",
            text="Patients receiving the intervention recovered sooner in the reported cohort.",
        )
    ]

    agent = ExtractorAgent(provider)
    result = await agent.run("Does the intervention improve recovery?", evidence)

    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].evidence_chunk_ids == ["c1"]
    assert result.hypotheses[0].observations == []
    assert agent.last_diagnostics["recovery_attempted"] is True
    assert agent.last_diagnostics["final_grounded_hypotheses"] == 1
    assert len(provider.calls) == 2
    assert provider.calls[0]["max_completion_tokens"] == 1400
    assert provider.calls[1]["max_completion_tokens"] == 700


@pytest.mark.asyncio
async def test_extractor_returns_empty_result_instead_of_crashing_when_recovery_is_empty():
    provider = FakeProvider([
        {"hypotheses": [], "notes": "No supported claim."},
        {"hypotheses": [], "notes": "Recovery also found no supported claim."},
    ])
    evidence = [
        EvidenceChunk(
            chunk_id="c1",
            source_id="s1",
            text="The source contains background information but no claim responsive to the question.",
        )
    ]

    agent = ExtractorAgent(provider)
    result = await agent.run("Is the proposed effect supported?", evidence)

    assert result.hypotheses == []
    assert agent.last_diagnostics["recovery_attempted"] is True
    assert agent.last_diagnostics["final_grounded_hypotheses"] == 0
    assert "evidence-only assessment" in result.notes


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


@pytest.mark.asyncio
async def test_judge_can_produce_evidence_only_report_without_experiments():
    provider = FakeProvider([{
        "title": "Evidence-only assessment",
        "summary": "The available evidence is relevant but does not support an inferential test.",
        "conclusion": "More structured observations are required.",
        "confidence": 0.55,
        "limitations": ["no grounded statistical hypothesis"],
        "citations": [{"chunk_id": "c1", "claim": "relevant background evidence"}],
    }])
    evidence = [EvidenceChunk(chunk_id="c1", source_id="s1", text="Relevant background evidence")]

    report = await JudgeAgent(provider).run("query", evidence, [])

    assert report.title == "Evidence-only assessment"
    assert report.citations[0].chunk_id == "c1"
    assert provider.calls[0]["max_completion_tokens"] == 1000
