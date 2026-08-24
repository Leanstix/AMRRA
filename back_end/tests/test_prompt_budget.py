import json

import pytest

from app.domain.schemas import EvidenceChunk, ExperimentResult, SourceInput
from app.providers.base import FakeProvider
from app.services.agents import ExtractorAgent, JudgeAgent
from app.services.prompt_budget import compact_experiment, pack_evidence
from app.services.retrieval import Retriever


def _evidence(count: int, size: int = 2000):
    return [
        EvidenceChunk(
            chunk_id=f"c{index}",
            source_id="s1",
            source_title="A long source title",
            text=(f"chunk {index} evidence " + ("x" * size)),
            score=1.0 - (index * 0.01),
        )
        for index in range(count)
    ]


def test_pack_evidence_honours_total_and_per_chunk_budgets():
    packed, metadata = pack_evidence(_evidence(20), total_chars=3000, per_chunk_chars=700)
    assert packed
    assert metadata["evidence_chars"] <= 3000
    assert all(len(item["text"]) <= 700 for item in packed)
    assert metadata["chunks_packed"] < 20


def test_compact_experiment_bounds_large_estimate_arrays():
    result = ExperimentResult(
        hypothesis_id="h1",
        test_used="regression",
        status="completed",
        estimate=list(range(100)),
        conclusion="done",
        evidence_chunk_ids=["c1"],
    )
    compact = compact_experiment(result)
    assert len(compact["estimate"]) == 16


@pytest.mark.asyncio
async def test_extractor_uses_bounded_context_and_stage_completion_cap():
    provider = FakeProvider([
        {
            "hypotheses": [],
            "notes": "not enough structured evidence",
        }
    ])
    await ExtractorAgent(provider).run("Does the intervention work?", _evidence(20))

    call = provider.calls[0]
    payload = json.loads(call["user"])
    assert call["max_completion_tokens"] == 1400
    assert payload["prompt_budget"]["evidence_chars"] <= 10_000
    assert len(payload["evidence"]) < 20


@pytest.mark.asyncio
async def test_judge_uses_only_referenced_compact_evidence_and_small_output_cap():
    provider = FakeProvider([
        {
            "title": "Assessment",
            "summary": "Summary",
            "conclusion": "Conclusion",
            "confidence": 0.8,
            "limitations": [],
            "citations": [{"chunk_id": "c1", "claim": "supported"}],
        }
    ])
    evidence = _evidence(8)
    experiment = ExperimentResult(
        hypothesis_id="h1",
        test_used="Welch t-test",
        status="completed",
        p_value=0.03,
        conclusion="significant",
        evidence_chunk_ids=["c1"],
    )

    await JudgeAgent(provider).run("question", evidence, [experiment])

    call = provider.calls[0]
    payload = json.loads(call["user"])
    assert call["max_completion_tokens"] == 1000
    assert [item["chunk_id"] for item in payload["evidence"]] == ["c1"]
    assert payload["prompt_budget"]["evidence_chars"] <= 4500
    assert "text" not in payload["experiments"][0]


@pytest.mark.asyncio
async def test_retriever_reranker_uses_bounded_candidate_context_and_small_output_cap():
    provider = FakeProvider([
        {
            "rankings": [
                {"chunk_id": "source-1-chunk-1", "relevance": 0.9, "reason": "direct"}
            ]
        }
    ], rerank_enabled=True)
    long_source = SourceInput(kind="text", title="paper", content="research evidence " * 5000)

    await Retriever(provider).retrieve("research evidence", [long_source], top_k=8)

    call = provider.calls[0]
    payload = json.loads(call["user"])
    assert call["max_completion_tokens"] == 512
    assert payload["prompt_budget"]["evidence_chars"] <= 8000
