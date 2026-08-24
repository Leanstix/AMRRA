from __future__ import annotations

import pytest
from pydantic import BaseModel

import app.providers.agentrouter as agentrouter_module
from app.core.config import Settings
from app.providers.agentrouter import AgentProviderError, AgentRouterProvider


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body):
        self.body = body
        self.status_code = 200

    def raise_for_status(self):
        return None

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
        self.__class__.requests.append((url, headers, json))
        return self.__class__.responses.pop(0)


def provider():
    return AgentRouterProvider(
        Settings(
            environment="test",
            AGENTROUTER_API_KEY="secret",
            AGENTROUTER_MODEL="gpt-5.6-sol",
            agent_max_retries=0,
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
    url, _, payload = FakeClient.requests[0]
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
