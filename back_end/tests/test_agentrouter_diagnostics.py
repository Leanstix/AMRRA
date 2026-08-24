from __future__ import annotations

import pytest

import app.providers.diagnostics as diagnostics_module
from app.core.config import Settings


class FakeProvider:
    def __init__(self, settings):
        self.model_name = settings.agentrouter_model
        self.api_base = settings.agentrouter_base_url.rstrip("/")
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
        lambda: Settings(environment="test", AGENTROUTER_API_KEY="secret"),
    )
    monkeypatch.setattr(diagnostics_module, "AgentRouterProvider", FakeProvider)

    result = await diagnostics_module.diagnose()

    assert result["authenticated"] is True
    assert result["model_available"] is True
    assert result["key_fingerprint"] == "abc123def456"
    assert "secret" not in str(result)


@pytest.mark.asyncio
async def test_diagnose_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(
        diagnostics_module,
        "get_settings",
        lambda: Settings(environment="test", AGENTROUTER_API_KEY=None),
    )

    result = await diagnostics_module.diagnose()

    assert result["configured"] is False
    assert "AGENTROUTER_API_KEY" in result["error"]
