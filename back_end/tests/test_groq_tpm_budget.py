import httpx
import pytest
from pydantic import BaseModel

import app.providers.groq as groq_module
from app.core.config import Settings
from app.providers.groq import GroqProvider, _reduced_completion_cap


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body, status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.text = ""
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
            response = httpx.Response(
                self.status_code,
                request=request,
                json=self.body,
                headers=self.headers,
            )
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
        self.__class__.requests.append(json.copy())
        return self.__class__.responses.pop(0)


async def _noop(*args, **kwargs):
    return None


def _provider(retries=1):
    return GroqProvider(
        Settings(
            environment="test",
            LLM_API_KEY="secret",
            LLM_MODEL="openai/gpt-oss-20b",
            agent_max_retries=retries,
        )
    )


def test_tpm_cap_reduction_uses_provider_limit_and_safety_margin():
    assert _reduced_completion_cap(
        "tokens per minute (TPM): Limit 8000, Requested 8307",
        1000,
    ) == 309


@pytest.mark.asyncio
async def test_413_tpm_error_reduces_completion_reservation_and_retries(monkeypatch):
    FakeClient.responses = [
        FakeResponse(
            {
                "error": {
                    "message": (
                        "Request too large on tokens per minute (TPM): "
                        "Limit 8000, Requested 8307, please reduce your message size"
                    )
                }
            },
            status_code=413,
        ),
        FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]}),
    ]
    FakeClient.requests = []
    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(groq_module.asyncio, "sleep", _noop)

    result = await _provider().structured(
        system="system",
        user="user",
        schema=Payload,
        max_completion_tokens=1000,
    )

    assert result.answer == "ok"
    assert len(FakeClient.requests) == 2
    assert FakeClient.requests[0]["max_completion_tokens"] == 1000
    assert FakeClient.requests[1]["max_completion_tokens"] == 309
    assert FakeClient.requests[0]["reasoning_effort"] == "low"


@pytest.mark.asyncio
async def test_429_uses_groq_retry_after_header_with_safety_margin(monkeypatch):
    FakeClient.responses = [
        FakeResponse(
            {"error": {"message": "rate limit exceeded"}},
            status_code=429,
            headers={"retry-after": "12.5"},
        ),
        FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]}),
    ]
    FakeClient.requests = []
    sleeps = []

    async def capture_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(groq_module.asyncio, "sleep", capture_sleep)

    result = await _provider().structured(system="system", user="user", schema=Payload)

    assert result.answer == "ok"
    assert len(FakeClient.requests) == 2
    assert sleeps == [pytest.approx(13.25)]
