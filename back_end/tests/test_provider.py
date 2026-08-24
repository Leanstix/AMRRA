from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

import app.providers.agentrouter as agentrouter_module
from app.core.config import Settings
from app.providers.agentrouter import AgentProviderError, AgentRouterProvider


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body, status_code=200, text=None):
        self.body = body
        self.status_code = status_code
        self.text = text if text is not None else ""

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://co.agentrouter.org/v1/chat/completions")
            response = httpx.Response(self.status_code, request=request, json=self.body)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self):
        return self.body


class FakeClient:
    responses = []
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, headers=None, json=None):
        self.__class__.requests.append(("POST", url, headers, json))
        return self.__class__.responses.pop(0)

    async def get(self, url, headers=None):
        self.__class__.requests.append(("GET", url, headers, None))
        return self.__class__.responses.pop(0)


def provider(*, key="secret", retries=0):
    return AgentRouterProvider(
        Settings(
            environment="test",
            AGENTROUTER_API_KEY=key,
            AGENTROUTER_MODEL="gpt-5.6-sol",
            agent_max_retries=retries,
        )
    )


@pytest.mark.asyncio
async def test_structured_provider_uses_agentrouter_openai_compatible_api(monkeypatch):
    FakeClient.responses = [
        FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]})
    ]
    FakeClient.requests = []
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)

    client = provider()
    result = await client.structured(system="system", user="Generate JSON", schema=Payload)

    assert result.answer == "ok"
    assert client.headers["Authorization"] == "Bearer secret"
    _, url, _, payload = FakeClient.requests[0]
    assert url == "https://co.agentrouter.org/v1/chat/completions"
    assert payload["model"] == "gpt-5.6-sol"
    assert payload["response_format"] == {"type": "json_object"}
    assert "api.openai.com" not in url


@pytest.mark.asyncio
async def test_provider_accepts_json_fences_and_content_blocks(monkeypatch):
    FakeClient.responses = [
        FakeResponse(
            {
                "choices": [
                    {"message": {"content": [{"text": '```json\n{"answer":"ok"}\n```'}]}}
                ]
            }
        )
    ]
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)
    result = await provider().structured(system="system", user="json", schema=Payload)
    assert result.answer == "ok"


@pytest.mark.asyncio
async def test_provider_rejects_unstructured_response(monkeypatch):
    FakeClient.responses = [FakeResponse({"choices": [{"message": {"content": "not-json"}}]})]
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)
    with pytest.raises(AgentProviderError):
        await provider().structured(system="system", user="json", schema=Payload)


def test_provider_requires_agentrouter_key():
    with pytest.raises(AgentProviderError):
        AgentRouterProvider(Settings(environment="test", AGENTROUTER_API_KEY=None))


def test_provider_strips_accidental_key_whitespace():
    client = provider(key="  secret\n")
    assert client.api_key == "secret"
    assert client.headers["Authorization"] == "Bearer secret"
    assert len(client.key_fingerprint) == 12


@pytest.mark.asyncio
async def test_401_fails_immediately_without_retrying_and_redacts_key(monkeypatch):
    secret = "temporary-secret"
    FakeClient.responses = [
        FakeResponse({"error": {"message": f"invalid key {secret}"}}, status_code=401)
    ]
    FakeClient.requests = []
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)

    with pytest.raises(AgentProviderError) as exc_info:
        await provider(key=secret, retries=3).structured(system="system", user="json", schema=Payload)

    assert "HTTP 401" in str(exc_info.value)
    assert secret not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)
    assert len(FakeClient.requests) == 1


@pytest.mark.asyncio
async def test_connection_check_confirms_auth_and_model(monkeypatch):
    FakeClient.responses = [
        FakeResponse({"object": "list", "data": [{"id": "gpt-5.6-sol"}, {"id": "claude-opus-5"}]})
    ]
    FakeClient.requests = []
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)

    result = await provider().check_connection()

    assert result == {
        "reachable": True,
        "authenticated": True,
        "model_available": True,
        "status_code": 200,
        "detail": None,
    }
    assert FakeClient.requests[0][1] == "https://co.agentrouter.org/v1/models"


@pytest.mark.asyncio
async def test_connection_check_reports_unauthorized_without_secret(monkeypatch):
    secret = "temporary-secret"
    FakeClient.responses = [
        FakeResponse({"error": {"message": f"invalid key {secret}"}}, status_code=401)
    ]
    monkeypatch.setattr(agentrouter_module.httpx, "AsyncClient", FakeClient)

    result = await provider(key=secret).check_connection()

    assert result["reachable"] is True
    assert result["authenticated"] is False
    assert result["status_code"] == 401
    assert secret not in result["detail"]
