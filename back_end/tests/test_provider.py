from __future__ import annotations

import pytest
from pydantic import BaseModel

import app.providers.cohere as cohere_module
from app.core.config import Settings
from app.providers.cohere import CohereProvider


class Payload(BaseModel):
    answer: str


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class FakeClient:
    responses = []

    def __init__(self, *args, **kwargs):
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, headers=None, json=None):
        self.requests.append((url, json))
        return self.responses.pop(0)


def provider():
    return CohereProvider(Settings(environment="test", COHERE_API_KEY="secret", agent_max_retries=0))


@pytest.mark.asyncio
async def test_structured_provider_validates_cohere_json(monkeypatch):
    FakeClient.responses = [FakeResponse({"message": {"content": [{"text": '{"answer":"ok"}'}]}})]
    monkeypatch.setattr(cohere_module.httpx, "AsyncClient", FakeClient)
    result = await provider().structured(system="system", user="Generate JSON", schema=Payload)
    assert result.answer == "ok"
    assert provider().headers["Authorization"] == "Bearer secret"


@pytest.mark.asyncio
async def test_embed_provider_extracts_float_vectors(monkeypatch):
    FakeClient.responses = [FakeResponse({"embeddings": {"float": [[1.0, 2.0], [3.0, 4.0]]}})]
    monkeypatch.setattr(cohere_module.httpx, "AsyncClient", FakeClient)
    vectors = await provider().embed(["a", "b"], input_type="search_document")
    assert vectors == [[1.0, 2.0], [3.0, 4.0]]
    assert await provider().embed([], input_type="search_document") == []
