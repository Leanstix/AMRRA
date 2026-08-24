from __future__ import annotations

import asyncio
import logging

from celery import Celery

from app.core.config import get_settings
from app.factory import build_orchestrator
from app.providers.groq import GroqProvider

logger = logging.getLogger(__name__)
settings = get_settings()
if not settings.celery_broker_url:
    raise RuntimeError("CELERY_BROKER_URL is required to start the AMRRA worker")

provider_config = GroqProvider(settings)
logger.info(
    "LLM configured provider=%s base=%s model=%s key_fingerprint=%s",
    provider_config.provider_name,
    provider_config.api_base,
    provider_config.model_name,
    provider_config.key_fingerprint,
)

celery_app = Celery(
    "amrra",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)
celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=840,
    task_time_limit=900,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)


@celery_app.task(
    name="amrra.run_pipeline",
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_pipeline_task(self, run_id: str) -> None:
    asyncio.run(build_orchestrator().run(run_id))
