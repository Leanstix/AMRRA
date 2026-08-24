from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.domain.schemas import RunSnapshot, RunStatus, TraceEvent


class Base(DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    state_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TraceRecord(Base):
    __tablename__ = "trace_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunRepository:
    def __init__(self, database_url: str):
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(self.engine, expire_on_commit=False, class_=Session)
        if database_url.startswith("sqlite"):
            Base.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def ping(self) -> bool:
        try:
            with self.SessionLocal() as session:
                session.execute(select(1))
            return True
        except Exception:
            return False

    def create_run(self, run_id: str, query: str, payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        with self.SessionLocal.begin() as session:
            session.add(
                RunRecord(
                    run_id=run_id,
                    query=query,
                    status=RunStatus.QUEUED.value,
                    payload_json=json.dumps(payload),
                    state_json=json.dumps({}),
                    created_at=now,
                    updated_at=now,
                )
            )

    def get_payload(self, run_id: str) -> dict[str, Any]:
        with self.SessionLocal() as session:
            record = session.get(RunRecord, run_id)
            if not record:
                raise KeyError(run_id)
            return json.loads(record.payload_json)

    def get_state(self, run_id: str) -> dict[str, Any]:
        with self.SessionLocal() as session:
            record = session.get(RunRecord, run_id)
            if not record:
                raise KeyError(run_id)
            return json.loads(record.state_json or "{}")

    def patch_state(self, run_id: str, **updates: Any) -> None:
        with self.SessionLocal.begin() as session:
            record = session.get(RunRecord, run_id)
            if not record:
                raise KeyError(run_id)
            state = json.loads(record.state_json or "{}")
            state.update(updates)
            record.state_json = json.dumps(state)
            record.updated_at = datetime.now(timezone.utc)

    def set_status(
        self,
        run_id: str,
        status: RunStatus,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.SessionLocal.begin() as session:
            record = session.get(RunRecord, run_id)
            if not record:
                raise KeyError(run_id)
            record.status = status.value
            record.error_code = error_code
            record.error_message = error_message
            record.updated_at = datetime.now(timezone.utc)

    def append_trace(self, event: TraceEvent) -> None:
        with self.SessionLocal.begin() as session:
            session.add(
                TraceRecord(
                    event_id=event.event_id,
                    run_id=event.run_id,
                    payload_json=event.model_dump_json(),
                    created_at=event.started_at,
                )
            )

    def list_traces(self, run_id: str) -> list[TraceEvent]:
        with self.SessionLocal() as session:
            rows = session.execute(
                select(TraceRecord).where(TraceRecord.run_id == run_id).order_by(TraceRecord.created_at.asc())
            ).scalars()
            return [TraceEvent.model_validate_json(row.payload_json) for row in rows]

    def snapshot(self, run_id: str) -> RunSnapshot:
        with self.SessionLocal() as session:
            record = session.get(RunRecord, run_id)
            if not record:
                raise KeyError(run_id)
            state = json.loads(record.state_json or "{}")
            return RunSnapshot.model_validate(
                {
                    "run_id": record.run_id,
                    "query": record.query,
                    "status": record.status,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "error_code": record.error_code,
                    "error_message": record.error_message,
                    **state,
                    "traces": [trace.model_dump(mode="json") for trace in self.list_traces(run_id)],
                }
            )
