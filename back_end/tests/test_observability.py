from pathlib import Path

import pytest

from app.domain.schemas import StageName, StageStatus
from app.infrastructure.repository import RunRepository
from app.services.observability import TraceManager, stable_hash


def test_stable_hash_is_key_order_independent():
    assert stable_hash({"a": 1, "b": 2}) == stable_hash({"b": 2, "a": 1})


def test_failed_stage_is_persisted_with_error(tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'trace.db'}")
    repo.create_run(
        "r1",
        "q",
        {"query": "query", "sources": [{"kind": "text", "content": "abc"}], "top_k": 8},
    )
    with pytest.raises(RuntimeError):
        with TraceManager(repo).stage("r1", StageName.EXTRACTION, input_data={"x": 1}):
            raise RuntimeError("boom")
    traces = repo.list_traces("r1")
    assert traces[0].status == StageStatus.FAILED
    assert traces[0].error_code == "RuntimeError"
    assert traces[0].error_message == "boom"
    repo.close()
