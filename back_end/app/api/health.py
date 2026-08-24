from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.domain.schemas import HealthResponse
from app.factory import get_repository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    database_ok = get_repository().ping()
    provider_ok = bool(
        (settings.llm_api_key or "").strip()
        and settings.llm_provider.strip().lower() == "groq"
        and settings.llm_api_style.strip().lower() == "openai_chat"
        and settings.llm_model.strip()
    )
    return HealthResponse(
        status="ok" if database_ok and provider_ok else "degraded",
        database=database_ok,
        agent_provider_configured=provider_ok,
    )


@router.get("/ready")
def ready():
    database_ok = get_repository().ping()
    return {"ready": database_ok}
