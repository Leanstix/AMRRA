from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_RETRYABLE_HTTP_STATUS = {408, 409, 425, 429}


class AgentProviderError(RuntimeError):
    pass


class AgentProvider(Protocol):
    model_name: str
    rerank_enabled: bool

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T: ...


class AgentRouterProvider:
    """OpenAI-compatible GPT provider routed exclusively through AgentRouter.

    AMRRA calls AgentRouter directly over HTTP. No request is sent to api.openai.com,
    and provider responses are treated as untrusted until Pydantic validates them.
    """

    rerank_enabled = True

    def __init__(self, settings: Settings):
        api_key = (settings.agentrouter_api_key or "").strip()
        if not api_key:
            raise AgentProviderError("AGENTROUTER_API_KEY is required")
        self.api_key = api_key
        self.api_base = settings.agentrouter_base_url.strip().rstrip("/")
        self.model_name = settings.agentrouter_model.strip()
        self.timeout = settings.agent_timeout_seconds
        self.max_retries = settings.agent_max_retries

    @property
    def key_fingerprint(self) -> str:
        """Non-secret identifier useful for detecting stale worker configuration."""
        return hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:12]

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AMRRA/agentrouter",
        }

    def _safe_error_detail(self, response: httpx.Response) -> str:
        detail = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                error = body.get("error")
                if isinstance(error, dict):
                    detail = str(error.get("message") or error.get("detail") or "")
                elif error:
                    detail = str(error)
                if not detail:
                    detail = str(body.get("message") or body.get("detail") or "")
        except Exception:
            detail = response.text or ""
        detail = detail.replace(self.api_key, "<redacted>").strip()
        return detail[:300]

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

    async def check_connection(self) -> dict[str, Any]:
        """Validate the loaded key and configured model without exposing the secret."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base}/models", headers=self.headers)
        except httpx.HTTPError as exc:
            return {
                "reachable": False,
                "authenticated": False,
                "model_available": False,
                "status_code": None,
                "detail": f"{exc.__class__.__name__}: {exc}",
            }

        if response.status_code in {401, 403}:
            return {
                "reachable": True,
                "authenticated": False,
                "model_available": False,
                "status_code": response.status_code,
                "detail": self._safe_error_detail(response) or "AgentRouter rejected the loaded API key",
            }
        if response.status_code >= 400:
            return {
                "reachable": True,
                "authenticated": False,
                "model_available": False,
                "status_code": response.status_code,
                "detail": self._safe_error_detail(response) or "AgentRouter model discovery failed",
            }

        try:
            body = response.json()
            data = body.get("data", []) if isinstance(body, dict) else []
            model_ids = {
                str(item.get("id"))
                for item in data
                if isinstance(item, dict) and item.get("id")
            }
        except Exception as exc:
            return {
                "reachable": True,
                "authenticated": True,
                "model_available": False,
                "status_code": response.status_code,
                "detail": f"Could not parse AgentRouter model list: {exc}",
            }

        return {
            "reachable": True,
            "authenticated": True,
            "model_available": self.model_name in model_ids,
            "status_code": response.status_code,
            "detail": None if self.model_name in model_ids else f"Configured model '{self.model_name}' was not returned by /models",
        }

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
                    status = exc.response.status_code
                    detail = self._safe_error_detail(exc.response)
                    suffix = f": {detail}" if detail else ""
                    last_error = AgentProviderError(f"AgentRouter returned HTTP {status}{suffix}")
                    retryable = status in _RETRYABLE_HTTP_STATUS or status >= 500
                    if not retryable:
                        raise last_error from exc
                except (httpx.HTTPError, json.JSONDecodeError, ValidationError, AgentProviderError) as exc:
                    last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 4))

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")


class FakeProvider:
    """Deterministic provider used only by tests and offline evaluations."""

    model_name = "fake-agent"

    def __init__(
        self,
        structured_responses: list[Any] | None = None,
        *,
        rerank_enabled: bool = False,
    ):
        self.responses = list(structured_responses or [])
        self.rerank_enabled = rerank_enabled

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        if not self.responses:
            raise AgentProviderError("no fake provider response configured")
        value = self.responses.pop(0)
        payload = value.model_dump() if isinstance(value, BaseModel) else value
        return schema.model_validate(payload)
