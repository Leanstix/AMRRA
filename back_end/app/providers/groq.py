from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.providers.base import AgentProviderError

T = TypeVar("T", bound=BaseModel)
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_RETRYABLE_HTTP_STATUS = {408, 409, 425, 429}


class GroqProvider:
    """Groq-backed OpenAI-compatible chat provider for all probabilistic AMRRA stages.

    `llama-3.1-8b-instant` supports Groq JSON Object Mode. AMRRA still treats
    every response as untrusted: the model is instructed with the target JSON
    schema and Pydantic validates it before the payload enters application state.
    """

    rerank_enabled = True

    def __init__(self, settings: Settings):
        if settings.llm_provider.strip().lower() != "groq":
            raise AgentProviderError("LLM_PROVIDER must be 'groq'")
        if settings.llm_api_style.strip().lower() != "openai_chat":
            raise AgentProviderError("LLM_API_STYLE must be 'openai_chat'")

        api_key = (settings.llm_api_key or "").strip().strip('"').strip("'")
        if not api_key:
            raise AgentProviderError("LLM_API_KEY is required")

        self.api_key = api_key
        self.api_base = settings.llm_base_url.strip().rstrip("/")
        self.model_name = settings.llm_model.strip()
        self.provider_name = "groq"
        self.timeout = settings.agent_timeout_seconds
        self.max_retries = settings.agent_max_retries
        self.max_completion_tokens = settings.llm_max_completion_tokens

    @property
    def key_fingerprint(self) -> str:
        return hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:12]

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AMRRA/1.0 (Groq OpenAI-compatible client)",
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
        return detail[:500]

    @staticmethod
    def _content_text(body: dict[str, Any]) -> str:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AgentProviderError("unexpected Groq chat-completions response") from exc

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                block["text"]
                for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ]
            if parts:
                return "".join(parts)
        raise AgentProviderError("Groq response did not contain text content")

    async def check_connection(self) -> dict[str, Any]:
        """Validate API authentication and model visibility without exposing the key."""
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
                "detail": self._safe_error_detail(response) or "Groq rejected the loaded API key",
            }
        if response.status_code >= 400:
            return {
                "reachable": True,
                "authenticated": False,
                "model_available": False,
                "status_code": response.status_code,
                "detail": self._safe_error_detail(response) or "Groq model discovery failed",
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
                "detail": f"Could not parse Groq model list: {exc}",
            }

        model_available = self.model_name in model_ids
        return {
            "reachable": True,
            "authenticated": True,
            "model_available": model_available,
            "status_code": response.status_code,
            "detail": None
            if model_available
            else f"Configured model '{self.model_name}' was not returned by /models",
        }

    async def structured(self, *, system: str, user: str, schema: type[T]) -> T:
        schema_json = json.dumps(
            schema.model_json_schema(), ensure_ascii=False, separators=(",", ":")
        )
        strict_system = (
            f"{system}\n\n"
            "You are operating as a JSON API. Return exactly one JSON object and no markdown or commentary. "
            "The object must satisfy this JSON Schema exactly. If evidence is insufficient, represent that "
            "honestly using the schema rather than inventing facts.\n"
            f"JSON Schema:\n{schema_json}"
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": strict_system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_completion_tokens": self.max_completion_tokens,
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
                    last_error = AgentProviderError(f"Groq returned HTTP {status}{suffix}")
                    retryable = status in _RETRYABLE_HTTP_STATUS or status >= 500
                    if not retryable:
                        raise last_error from exc
                except (httpx.HTTPError, json.JSONDecodeError, ValidationError, AgentProviderError) as exc:
                    last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 4))

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")
