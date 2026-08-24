from __future__ import annotations

import pytest

import app.providers.diagnostics as diagnostics_module
from app.core.config import Settings


class FakeProvider:
    provider_name = "groq"

    def __init__(self, settings):
        self.requested_model_name = settings.llm_model
        self.model_name = settings.llm_model
        self.model_migrated_from = None
        self.api_base = settings.llm_base_url.rstrip("/")
        self.key_fingerprint = "abc123def456"

    async def check_connection(self):
        return {
            "reachable": True,
            "authenticated": True,
            "model_available": True,
            "status_code": 200,
            "detail": None,
        }


@pytest.mark.asyncio
async def test_diagnose_returns_safe_provider_state(monkeypatch):
    monkeypatch.setattr(
        diagnostics_module,
        "get_settings",
        lambda: Settings(environment="test", LLM_API_KEY="secret"),
    )
    monkeypatch.setattr(diagnostics_module, "GroqProvider", FakeProvider)

    result = await diagnostics_module.diagnose()

    assert result["provider"] == "groq"
    assert result["api_style"] == "openai_chat"
    assert result["requested_model"] == "openai/gpt-oss-20b"
    assert result["model"] == "openai/gpt-oss-20b"
    assert result["model_migrated_from"] is None
    assert result["authenticated"] is True
    assert result["model_available"] is True
    assert result["key_fingerprint"] == "abc123def456"
    assert "secret" not in str(result)


@pytest.mark.asyncio
async def test_diagnose_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(
        diagnostics_module,
        "get_settings",
        lambda: Settings(environment="test", LLM_API_KEY=None),
    )

    result = await diagnostics_module.diagnose()

    assert result["configured"] is False
    assert result["provider"] == "groq"
    assert result["requested_model"] == "openai/gpt-oss-20b"
    assert "LLM_API_KEY" in result["error"]
