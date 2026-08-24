import app.api.health as health_module
from app.core.config import Settings


class Repo:
    def __init__(self, ok):
        self.ok = ok

    def ping(self):
        return self.ok


def test_health_is_ok_when_db_and_provider_are_ready(monkeypatch):
    monkeypatch.setattr(health_module, "get_repository", lambda: Repo(True))
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(environment="test", AGENTROUTER_API_KEY="key"),
    )
    result = health_module.health()
    assert result.status == "ok"
    assert health_module.ready() == {"ready": True}


def test_health_is_degraded_without_provider_key(monkeypatch):
    monkeypatch.setattr(health_module, "get_repository", lambda: Repo(True))
    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: Settings(environment="test", AGENTROUTER_API_KEY=None),
    )
    assert health_module.health().status == "degraded"
