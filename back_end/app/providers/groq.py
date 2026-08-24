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
_SCHEMA_NAME_RE = re.compile(r"[^A-Za-z0-9_-]+")
_TPM_LIMIT_RE = re.compile(r"Limit\s+([\d,]+),\s*Requested\s+([\d,]+)", re.IGNORECASE)
_RETRYABLE_HTTP_STATUS = {408, 409, 425, 429}
_DEPRECATED_MODEL_REPLACEMENTS = {"llama-3.1-8b-instant": "openai/gpt-oss-20b"}
_MIN_COMPLETION_TOKENS = 192
_TPM_SAFETY_MARGIN = 384
_MAX_RATE_LIMIT_SLEEP_SECONDS = 65.0


def _strictify_schema(value: Any) -> Any:
    """Convert Pydantic JSON Schema into Groq strict-mode compatible schema."""
    if isinstance(value, list):
        return [_strictify_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: _strictify_schema(item) for key, item in value.items() if key != "default"}
    properties = result.get("properties")
    if isinstance(properties, dict):
        result["required"] = list(properties.keys())
        result["additionalProperties"] = False
    return result


def _schema_name(schema: type[BaseModel]) -> str:
    name = _SCHEMA_NAME_RE.sub("_", schema.__name__).strip("_")
    return (name or "amrra_response")[:64]


def _reduced_completion_cap(detail: str, current_cap: int) -> int | None:
    """Reduce output reservation when a request cannot fit Groq's TPM ceiling."""
    if "TPM" not in detail.upper() and "TOKENS PER MINUTE" not in detail.upper():
        return None
    match = _TPM_LIMIT_RE.search(detail)
    if not match:
        fallback = max(_MIN_COMPLETION_TOKENS, current_cap // 2)
        return fallback if fallback < current_cap else None
    limit = int(match.group(1).replace(",", ""))
    requested = int(match.group(2).replace(",", ""))
    overflow = max(0, requested - limit)
    target = max(_MIN_COMPLETION_TOKENS, current_cap - overflow - _TPM_SAFETY_MARGIN)
    return target if target < current_cap else None


def _retry_after_seconds(response: httpx.Response, attempt: int) -> float:
    """Prefer Groq's rate-limit reset hint over blind exponential retries."""
    raw = response.headers.get("retry-after")
    if raw:
        try:
            return min(_MAX_RATE_LIMIT_SLEEP_SECONDS, max(0.25, float(raw)))
        except ValueError:
            pass
    return float(min(2**attempt, 8))


class GroqProvider:
    """Groq-backed OpenAI-compatible provider for AMRRA's probabilistic stages."""

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
        self.requested_model_name = settings.llm_model.strip()
        self.model_name = _DEPRECATED_MODEL_REPLACEMENTS.get(self.requested_model_name, self.requested_model_name)
        self.model_migrated_from = self.requested_model_name if self.model_name != self.requested_model_name else None
        self.provider_name = "groq"
        self.timeout = settings.agent_timeout_seconds
        self.max_retries = settings.agent_max_retries
        self.max_completion_tokens = settings.llm_max_completion_tokens
        self.rerank_max_completion_tokens = settings.llm_rerank_max_completion_tokens
        self.extractor_max_completion_tokens = settings.llm_extractor_max_completion_tokens
        self.judge_max_completion_tokens = settings.llm_judge_max_completion_tokens
        self.reasoning_effort = settings.llm_reasoning_effort.strip().lower()
        if self.reasoning_effort not in {"low", "medium", "high"}:
            raise AgentProviderError("LLM_REASONING_EFFORT must be low, medium, or high")

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
        return detail.replace(self.api_key, "<redacted>").strip()[:500]

    @staticmethod
    def _content_text(body: dict[str, Any]) -> str:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AgentProviderError("unexpected Groq chat-completions response") from exc
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [block["text"] for block in content if isinstance(block, dict) and isinstance(block.get("text"), str)]
            if parts:
                return "".join(parts)
        raise AgentProviderError("Groq response did not contain text content")

    async def check_connection(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base}/models", headers=self.headers)
        except httpx.HTTPError as exc:
            return {"reachable": False, "authenticated": False, "model_available": False, "status_code": None, "detail": f"{exc.__class__.__name__}: {exc}"}
        if response.status_code in {401, 403}:
            return {"reachable": True, "authenticated": False, "model_available": False, "status_code": response.status_code, "detail": self._safe_error_detail(response) or "Groq rejected the loaded API key"}
        if response.status_code >= 400:
            return {"reachable": True, "authenticated": False, "model_available": False, "status_code": response.status_code, "detail": self._safe_error_detail(response) or "Groq model discovery failed"}
        try:
            body = response.json()
            data = body.get("data", []) if isinstance(body, dict) else []
            model_ids = {str(item.get("id")) for item in data if isinstance(item, dict) and item.get("id")}
        except Exception as exc:
            return {"reachable": True, "authenticated": True, "model_available": False, "status_code": response.status_code, "detail": f"Could not parse Groq model list: {exc}"}
        model_available = self.model_name in model_ids
        return {
            "reachable": True,
            "authenticated": True,
            "model_available": model_available,
            "status_code": response.status_code,
            "detail": None if model_available else f"Configured model '{self.model_name}' was not returned by /models",
        }

    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        max_completion_tokens: int | None = None,
    ) -> T:
        strict_schema = _strictify_schema(schema.model_json_schema())
        completion_cap = max(_MIN_COMPLETION_TOKENS, int(max_completion_tokens or self.max_completion_tokens))
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": f"{system}\n\nReturn only the requested structured object. Never invent evidence or values. If evidence is insufficient, encode that honestly in the provided fields."},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_schema", "json_schema": {"name": _schema_name(schema), "strict": True, "schema": strict_schema}},
            "temperature": 0,
            "reasoning_effort": self.reasoning_effort,
            "max_completion_tokens": completion_cap,
        }

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                retry_delay: float | None = None
                try:
                    response = await client.post(f"{self.api_base}/chat/completions", headers=self.headers, json=payload)
                    response.raise_for_status()
                    content = _JSON_FENCE_RE.sub("", self._content_text(response.json()).strip()).strip()
                    return schema.model_validate_json(content)
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    detail = self._safe_error_detail(exc.response)
                    suffix = f": {detail}" if detail else ""
                    last_error = AgentProviderError(f"Groq returned HTTP {status}{suffix}")

                    if status == 413 and attempt < self.max_retries:
                        reduced_cap = _reduced_completion_cap(detail, int(payload["max_completion_tokens"]))
                        if reduced_cap is not None:
                            payload["max_completion_tokens"] = reduced_cap
                            await asyncio.sleep(0.25)
                            continue

                    retryable = status in _RETRYABLE_HTTP_STATUS or status >= 500
                    if not retryable:
                        raise last_error from exc
                    if status == 429:
                        retry_delay = _retry_after_seconds(exc.response, attempt)
                except (httpx.HTTPError, json.JSONDecodeError, ValidationError, AgentProviderError) as exc:
                    last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(retry_delay if retry_delay is not None else min(2**attempt, 4))

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")
