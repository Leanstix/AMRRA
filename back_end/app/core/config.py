from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AMRRA"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./amrra.db"

    # One production LLM provider: Groq's OpenAI-compatible Chat Completions API.
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    llm_api_style: str = Field(default="openai_chat", alias="LLM_API_STYLE")
    llm_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="llama-3.1-8b-instant", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_max_completion_tokens: int = Field(default=4096, alias="LLM_MAX_COMPLETION_TOKENS")

    agent_timeout_seconds: float = 45.0
    agent_max_retries: int = 2
    max_upload_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 100
    max_source_chars: int = 250_000
    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    execute_inline: bool = Field(default=False, alias="EXECUTE_INLINE")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    @property
    def is_test(self) -> bool:
        return self.environment.lower() == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


ROOT_DIR = Path(__file__).resolve().parents[3]
