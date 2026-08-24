from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class AgentProviderError(RuntimeError):
    pass


class AgentProvider(Protocol):
    model_name: str

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T: ...


class AgentRouterProvider:
    """OpenAI-compatible GPT provider routed exclusively through AgentRouter.

    AMRRA calls AgentRouter directly over HTTP. No request is sent to api.openai.com,
    and provider responses are treated as untrusted until Pydantic validates them.
    """

    def __init__(self, settings: Settings):
        if not settings.agentrouter_api_key:
            raise AgentProviderError("AGENTROUTER_API_KEY is required")
        self.api_key = settings.agentrouter_api_key
        self.api_base = settings.agentrouter_base_url.rstrip("/")
        self.model_name = settings.agentrouter_model
        self.timeout = settings.agent_timeout_seconds
        self.max_retries = settings.agent_max_retries

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _content_text(body: dict[str, Any]) -> str:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AgentProviderError("unexpected AgentRouter chat-completions response") from exc

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            if parts:
                return "".join(parts)
        raise AgentProviderError("AgentRouter response did not contain text content")

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
        strict_system = (
            f"{system}\n\n"
            "Return exactly one JSON object and no markdown or commentary. "
            "The object must satisfy this JSON Schema exactly:\n"
            f"{schema_json}"
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": strict_system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    content = self._content_text(response.json()).strip()
                    content = _JSON_FENCE_RE.sub("", content).strip()
                    return schema.model_validate_json(content)
                except httpx.HTTPStatusError as exc:
                    last_error = AgentProviderError(
                        f"AgentRouter returned HTTP {exc.response.status_code}"
                    )
                except (httpx.HTTPError, json.JSONDecodeError, ValidationError, AgentProviderError) as exc:
                    last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 4))

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")


class FakeProvider:
    """Deterministic provider used only by tests and offline evaluations."""

    model_name = "fake-agent"

    def __init__(self, structured_responses: list[Any] | None = None):
        self.responses = list(structured_responses or [])

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        if not self.responses:
            raise AgentProviderError("no fake provider response configured")
        value = self.responses.pop(0)
        payload = value.model_dump() if isinstance(value, BaseModel) else value
        return schema.model_validate(payload)
