from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.infrastructure.repository import RunRepository
from app.providers.cohere import CohereProvider
from app.services.ingestion import SourceIngestor
from app.services.orchestrator import AgentOrchestrator


@lru_cache
def get_repository() -> RunRepository:
    return RunRepository(get_settings().database_url)


def build_orchestrator(
    settings: Settings | None = None,
    repository: RunRepository | None = None,
) -> AgentOrchestrator:
    settings = settings or get_settings()
    repository = repository or get_repository()
    if settings.agent_provider != "cohere":
        raise RuntimeError(f"unsupported production agent provider: {settings.agent_provider}")
    provider = CohereProvider(settings)
    return AgentOrchestrator(
        repository=repository,
        provider=provider,
        ingestor=SourceIngestor(settings),
    )
