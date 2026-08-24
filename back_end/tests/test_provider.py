from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

import app.providers.groq as groq_module
from app.core.config import Settings
from app.providers.base import AgentProviderError
from app.providers.groq import GroqProvider


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body, status_code=200, text=None):
        self.body = body
        self.status_code = status_code
        self.text = text if text is not None else ""

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
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


def provider(*, key="secret", retries=0, provider_name="groq", api_style="openai_chat"):
    return GroqProvider(
        Settings(
            environment="test",
            LLM_PROVIDER=provider_name,
            LLM_API_STYLE=api_style,
            LLM_API_KEY=key,
            LLM_MODEL="llama-3.1-8b-instant",
            agent_max_retries=retries,
        )
    )


@pytest.mark.asyncio
async def test_structured_provider_uses_groq_openai_compatible_api(monkeypatch):
    FakeClient.responses = [
        FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]})
    ]
    FakeClient.requests = []
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)

    client = provider()
    result = await client.structured(system="system", user="Generate JSON", schema=Payload)

    assert result.answer == "ok"
    assert client.provider_name == "groq"
    assert client.headers["Authorization"] == "Bearer secret"
    _, url, _, payload = FakeClient.requests[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert payload["model"] == "llama-3.1-8b-instant"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["temperature"] == 0
    assert payload["max_completion_tokens"] == 4096


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
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    result = await provider().structured(system="system", user="json", schema=Payload)
    assert result.answer == "ok"


@pytest.mark.asyncio
async def test_schema_validation_failure_is_retried(monkeypatch):
    FakeClient.responses = [
        FakeResponse({"choices": [{"message": {"content": '{"wrong":"shape"}'}}]}),
        FakeResponse({"choices": [{"message": {"content": '{"answer":"fixed"}'}}]}),
    ]
    FakeClient.requests = []
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(groq_module.asyncio, "sleep", lambda *args, **kwargs: _noop())

    result = await provider(retries=1).structured(system="system", user="json", schema=Payload)

    assert result.answer == "fixed"
    assert len(FakeClient.requests) == 2


async def _noop():
    return None


@pytest.mark.asyncio
async def test_provider_rejects_unstructured_response(monkeypatch):
    FakeClient.responses = [FakeResponse({"choices": [{"message": {"content": "not-json"}}]})]
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    with pytest.raises(AgentProviderError):
        await provider().structured(system="system", user="json", schema=Payload)


def test_provider_requires_llm_key():
    with pytest.raises(AgentProviderError, match="LLM_API_KEY"):
        GroqProvider(Settings(environment="test", LLM_API_KEY=None))


def test_provider_rejects_wrong_provider_or_api_style():
    with pytest.raises(AgentProviderError, match="LLM_PROVIDER"):
        provider(provider_name="other")
    with pytest.raises(AgentProviderError, match="LLM_API_STYLE"):
        provider(api_style="responses")


def test_provider_strips_accidental_key_whitespace_and_quotes():
    client = provider(key='  "secret"\n')
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
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)

    with pytest.raises(AgentProviderError) as exc_info:
        await provider(key=secret, retries=3).structured(system="system", user="json", schema=Payload)

    assert "HTTP 401" in str(exc_info.value)
    assert secret not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)
    assert len(FakeClient.requests) == 1


@pytest.mark.asyncio
async def test_connection_check_confirms_auth_and_model(monkeypatch):
    FakeClient.responses = [
        FakeResponse({"object": "list", "data": [{"id": "llama-3.1-8b-instant"}]})
    ]
    FakeClient.requests = []
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)

    result = await provider().check_connection()

    assert result == {
        "reachable": True,
        "authenticated": True,
        "model_available": True,
        "status_code": 200,
        "detail": None,
    }
    assert FakeClient.requests[0][1] == "https://api.groq.com/openai/v1/models"


@pytest.mark.asyncio
async def test_connection_check_reports_missing_model(monkeypatch):
    FakeClient.responses = [FakeResponse({"object": "list", "data": [{"id": "other-model"}]})]
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)

    result = await provider().check_connection()

    assert result["authenticated"] is True
    assert result["model_available"] is False
    assert "llama-3.1-8b-instant" in result["detail"]


@pytest.mark.asyncio
async def test_connection_check_reports_unauthorized_without_secret(monkeypatch):
    secret = "temporary-secret"
    FakeClient.responses = [
        FakeResponse({"error": {"message": f"invalid key {secret}"}}, status_code=401)
    ]
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)

    result = await provider(key=secret).check_connection()

    assert result["reachable"] is True
    assert result["authenticated"] is False
    assert result["status_code"] == 401
    assert secret not in result["detail"]
