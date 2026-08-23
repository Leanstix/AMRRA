from __future__ import annotations

import asyncio
import json
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)


class AgentProviderError(RuntimeError):
    pass


class AgentProvider(Protocol):
    model_name: str

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T: ...
    async def embed(self, texts: list[str], *, input_type: str) -> list[list[float]]: ...


class CohereProvider:
    """Minimal Cohere v2 provider with schema-constrained JSON output.

    We call the HTTP API directly so the backend does not depend on the Cohere SDK's
    release cadence. Provider responses are treated as untrusted until Pydantic validates them.
    """

    api_base = "https://api.cohere.com"

    def __init__(self, settings: Settings):
        if not settings.cohere_api_key:
            raise AgentProviderError("COHERE_API_KEY is required for the cohere provider")
        self.api_key = settings.cohere_api_key
        self.model_name = settings.cohere_chat_model
        self.embed_model = settings.cohere_embed_model
        self.timeout = settings.agent_timeout_seconds
        self.max_retries = settings.agent_max_retries

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_object",
                "schema": schema.model_json_schema(),
            },
        }

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(f"{self.api_base}/v2/chat", headers=self.headers, json=payload)
                    response.raise_for_status()
                    body = response.json()
                    content = body["message"]["content"][0]["text"]
                    return schema.model_validate_json(content)
                except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValidationError) as exc:
                    last_error = exc
                    if attempt < self.max_retries:
                        await asyncio.sleep(min(2 ** attempt, 4))

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")

    async def embed(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []
        payload = {
            "model": self.embed_model,
            "texts": texts,
            "input_type": input_type,
            "embedding_types": ["float"],
            "truncate": "END",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.api_base}/v2/embed", headers=self.headers, json=payload)
            response.raise_for_status()
            body = response.json()
            try:
                return body["embeddings"]["float"]
            except (KeyError, TypeError) as exc:
                raise AgentProviderError("unexpected embedding response") from exc


class FakeProvider:
    """Deterministic test provider. Never selected by production configuration."""

    model_name = "fake-agent"

    def __init__(self, structured_responses: list[Any] | None = None):
        self.responses = list(structured_responses or [])

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        if not self.responses:
            raise AgentProviderError("no fake provider response configured")
        value = self.responses.pop(0)
        payload = value.model_dump() if isinstance(value, BaseModel) else value
        return schema.model_validate(payload)

    async def embed(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [[float(len(t)), float(sum(map(ord, t)) % 997)] for t in texts]
