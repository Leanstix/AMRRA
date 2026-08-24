from __future__ import annotations

from fastapi import BackgroundTasks

from app.core.config import Settings


class DispatchError(RuntimeError):
    pass


def dispatch_run(run_id: str, background_tasks: BackgroundTasks, settings: Settings) -> str:
    """Dispatch a run to Celery in production and FastAPI background tasks locally."""
    if settings.celery_broker_url:
        try:
            from celery import Celery
        except ImportError as exc:  # pragma: no cover
            raise DispatchError("CELERY_BROKER_URL is configured but celery is not installed") from exc
        client = Celery("amrra-dispatch", broker=settings.celery_broker_url)
        try:
            client.send_task("amrra.run_pipeline", args=[run_id], queue="amrra")
        except Exception as exc:
            raise DispatchError(f"Could not dispatch agent run: {exc}") from exc
        return "celery"

    from app.api.runs import _execute_run

    background_tasks.add_task(_execute_run, run_id)
    return "background"
