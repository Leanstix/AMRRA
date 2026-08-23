from pathlib import Path

from app.domain.schemas import RunStatus
from app.infrastructure.repository import RunRepository


def test_repository_round_trip(tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'test.db'}")
    repo.create_run(
        "r1",
        "query",
        {"query": "query", "sources": [{"kind": "text", "content": "abc"}], "top_k": 8},
    )
    assert repo.snapshot("r1").status == RunStatus.QUEUED
    repo.patch_state("r1", plans=[])
    repo.set_status("r1", RunStatus.RUNNING)
    snapshot = repo.snapshot("r1")
    assert snapshot.status == RunStatus.RUNNING
    assert snapshot.plans == []
    repo.close()
