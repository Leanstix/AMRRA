from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

import app.providers.groq as groq_module
from app.core.config import Settings
from app.providers.groq import GroqProvider, _retry_after_seconds


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body, status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}
        self.text = ""

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
        self.__class__.requests.append((url, headers, json))
        return self.__class__.responses.pop(0)


def provider(*, retries=0):
    return GroqProvider(
        Settings(
            environment="test",
            LLM_API_KEY="secret",
            LLM_MODEL="openai/gpt-oss-20b",
            agent_max_retries=retries,
        )
    )


def _rate_limit_body(wait="24.2625s"):
    return {
        "error": {
            "message": (
                "Rate limit reached for model `openai/gpt-oss-20b` on tokens per minute (TPM): "
                "Limit 8000, Used 7289, Requested 3946. "
                f"Please try again in {wait}."
            )
        }
    }


@pytest.mark.asyncio
async def test_429_uses_body_reset_hint_when_retry_after_header_is_missing(monkeypatch):
    FakeClient.responses = [
        FakeResponse(_rate_limit_body(), status_code=429),
        FakeResponse({"choices": [{"message": {"content": '{"answer":"ok"}'}}]}),
    ]
    FakeClient.requests = []
    sleeps = []

    async def capture_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(groq_module.asyncio, "sleep", capture_sleep)

    result = await provider(retries=0).structured(system="system", user="json", schema=Payload)

    assert result.answer == "ok"
    assert len(FakeClient.requests) == 2
    assert sleeps == [pytest.approx(25.0125)]


def test_retry_hint_prefers_safest_groq_token_reset_signal():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(
        429,
        request=request,
        headers={"retry-after": "10.5", "x-ratelimit-reset-tokens": "18.2s"},
    )

    delay = _retry_after_seconds(
        response,
        "Please try again in 24.2625s.",
        attempt=0,
    )

    assert delay == pytest.approx(25.0125)


@pytest.mark.asyncio
async def test_rate_limit_retries_do_not_consume_schema_repair_budget(monkeypatch):
    FakeClient.responses = [
        FakeResponse(
            {
                "error": {
                    "message": "Generated JSON does not match the expected schema. Error: jsonschema mismatch",
                    "failed_generation": '{"wrong":"shape"}',
                }
            },
            status_code=400,
        ),
        FakeResponse(_rate_limit_body("0.5s"), status_code=429),
        FakeResponse({"choices": [{"message": {"content": '{"wrong":"shape"}'}}]}),
        FakeResponse(_rate_limit_body("0.5s"), status_code=429),
        FakeResponse({"choices": [{"message": {"content": '{"answer":"repaired"}'}}]}),
    ]
    FakeClient.requests = []
    sleeps = []

    async def capture_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(groq_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(groq_module.asyncio, "sleep", capture_sleep)

    result = await provider(retries=1).structured(system="system", user="json", schema=Payload)

    assert result.answer == "repaired"
    assert len(FakeClient.requests) == 5
    assert FakeClient.requests[1][2]["response_format"] == {"type": "json_object"}
    assert FakeClient.requests[4][2]["response_format"] == {"type": "json_object"}
    assert sleeps[0] == pytest.approx(1.25)
    assert sleeps[-1] == pytest.approx(1.25)
