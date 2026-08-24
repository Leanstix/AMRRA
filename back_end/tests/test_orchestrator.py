from pathlib import Path

import pytest

from app.core.config import Settings
from app.domain.schemas import RunRequest, RunStatus, SourceInput
from app.infrastructure.repository import RunRepository
from app.providers.agentrouter import FakeProvider
from app.services.ingestion import SourceIngestor
from app.services.orchestrator import AgentOrchestrator


@pytest.mark.asyncio
async def test_full_agent_workflow_persists_traceable_results(tmp_path: Path):
    extraction = {
        "hypotheses": [{
            "statement": "Group A has a lower outcome than Group B",
            "variables": ["outcome"],
            "confidence": 0.95,
            "evidence_chunk_ids": ["source-1-chunk-1"],
            "observations": [
                {"name": "outcome", "role": "outcome", "value_type": "raw_numeric", "group": "A", "values": [1, 2, 3, 4, 5], "evidence_chunk_ids": ["source-1-chunk-1"], "confidence": 0.95},
                {"name": "outcome", "role": "outcome", "value_type": "raw_numeric", "group": "B", "values": [8, 9, 10, 11, 12], "evidence_chunk_ids": ["source-1-chunk-1"], "confidence": 0.95},
            ],
        }],
        "notes": "",
    }
    judgement = {
        "title": "Reproducibility assessment",
        "summary": "Group B is higher under the deterministic test.",
        "conclusion": "The reported evidence supports a difference.",
        "confidence": 0.9,
        "limitations": ["single extracted source"],
        "citations": [{"chunk_id": "source-1-chunk-1", "claim": "reported values"}],
    }
    provider = FakeProvider([extraction, judgement])
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'run.db'}",
        AGENTROUTER_API_KEY="test",
    )
    repo = RunRepository(settings.database_url)
    request = RunRequest(
        query="Does Group A differ from Group B?",
        sources=[
            SourceInput(
                kind="text",
                title="paper",
                content=("Group A outcomes were 1 2 3 4 5. Group B outcomes were 8 9 10 11 12. " * 30),
            )
        ],
        top_k=3,
    )
    repo.create_run("run-1", request.query, request.model_dump(mode="json"))
    orchestrator = AgentOrchestrator(
        repository=repo,
        provider=provider,
        ingestor=SourceIngestor(settings),
    )
    await orchestrator.run("run-1")

    snapshot = repo.snapshot("run-1")
    assert snapshot.status == RunStatus.COMPLETED
    assert snapshot.extraction and len(snapshot.extraction.hypotheses) == 1
    assert snapshot.plans[0].test == "welch_ttest"
    assert snapshot.experiments[0].status == "completed"
    assert snapshot.experiments[0].p_value < 0.05
    assert snapshot.report and snapshot.report.citations[0].chunk_id == "source-1-chunk-1"
    assert [trace.stage.value for trace in snapshot.traces] == [
        "ingestion",
        "retrieval",
        "extraction",
        "planning",
        "experimentation",
        "judging",
    ]
    repo.close()


@pytest.mark.asyncio
async def test_agent_failure_marks_run_failed_and_keeps_failed_trace(tmp_path: Path):
    provider = FakeProvider([])
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'fail.db'}",
        AGENTROUTER_API_KEY="test",
    )
    repo = RunRepository(settings.database_url)
    request = RunRequest(
        query="What is supported?",
        sources=[SourceInput(kind="text", content="Evidence text " * 400)],
        top_k=3,
    )
    repo.create_run("failed-run", request.query, request.model_dump(mode="json"))
    orchestrator = AgentOrchestrator(
        repository=repo,
        provider=provider,
        ingestor=SourceIngestor(settings),
    )
    with pytest.raises(Exception):
        await orchestrator.run("failed-run")
    snapshot = repo.snapshot("failed-run")
    assert snapshot.status == RunStatus.FAILED
    assert snapshot.error_code == "AGENTPROVIDERERROR"
    extraction_trace = next(trace for trace in snapshot.traces if trace.stage.value == "extraction")
    assert extraction_trace.status.value == "failed"
    repo.close()
