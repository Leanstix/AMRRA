from __future__ import annotations

import hashlib
import json
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from app.domain.schemas import StageName, StageStatus, TraceEvent
from app.infrastructure.repository import RunRepository


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TraceManager:
    def __init__(self, repository: RunRepository):
        self.repository = repository

    @contextmanager
    def stage(
        self,
        run_id: str,
        stage: StageName,
        *,
        input_data: Any = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        event_id = str(uuid.uuid4())
        started = time.time()
        mutable: dict[str, Any] = {"output": None, "metadata": {}, "retry_count": 0}
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)
        try:
            yield mutable
        except Exception as exc:
            ended_at = datetime.now(timezone.utc)
            event = TraceEvent(
                event_id=event_id,
                run_id=run_id,
                stage=stage,
                status=StageStatus.FAILED,
                started_at=started_at,
                ended_at=ended_at,
                latency_ms=int((time.time() - started) * 1000),
                model=model,
                prompt_version=prompt_version,
                input_hash=stable_hash(input_data) if input_data is not None else None,
                retry_count=mutable.get("retry_count", 0),
                error_code=exc.__class__.__name__,
                error_message=str(exc)[:2000],
                metadata=mutable.get("metadata", {}),
            )
            self.repository.append_trace(event)
            raise
        else:
            ended_at = datetime.now(timezone.utc)
            output = mutable.get("output")
            event = TraceEvent(
                event_id=event_id,
                run_id=run_id,
                stage=stage,
                status=StageStatus.COMPLETED,
                started_at=started_at,
                ended_at=ended_at,
                latency_ms=int((time.time() - started) * 1000),
                model=model,
                prompt_version=prompt_version,
                input_hash=stable_hash(input_data) if input_data is not None else None,
                output_hash=stable_hash(output) if output is not None else None,
                retry_count=mutable.get("retry_count", 0),
                metadata=mutable.get("metadata", {}),
            )
            self.repository.append_trace(event)
