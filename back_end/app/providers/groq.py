from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.providers.base import AgentProviderError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_SCHEMA_NAME_RE = re.compile(r"[^A-Za-z0-9_-]+")
_TPM_LIMIT_RE = re.compile(r"Limit\s+([\d,]+),\s*Requested\s+([\d,]+)", re.IGNORECASE)
_RETRY_IN_RE = re.compile(
    r"try\s+again\s+in\s+([0-9]+(?:\.[0-9]+)?)\s*(ms|milliseconds?|s|sec(?:ond)?s?|m|min(?:ute)?s?)?",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(
    r"^\s*(?:(?P<minutes>[0-9]+(?:\.[0-9]+)?)m)?\s*(?:(?P<seconds>[0-9]+(?:\.[0-9]+)?)s)?\s*$",
    re.IGNORECASE,
)
_RETRYABLE_HTTP_STATUS = {408, 409, 425}
_DEPRECATED_MODEL_REPLACEMENTS = {"llama-3.1-8b-instant": "openai/gpt-oss-20b"}
_MIN_COMPLETION_TOKENS = 192
_TPM_SAFETY_MARGIN = 384
_MAX_RATE_LIMIT_SLEEP_SECONDS = 65.0
_MAX_RATE_LIMIT_RETRIES = 6
_RATE_LIMIT_SAFETY_SECONDS = 0.75
_SCHEMA_HINT_MAX_CHARS = 8_000


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


def _duration_seconds(raw: str | None) -> float | None:
    """Parse Groq reset durations such as `24.2s`, `1m2.4s`, or plain seconds."""
    if not raw:
        return None
    value = raw.strip().lower()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    if value.endswith("ms"):
        try:
            return max(0.0, float(value[:-2].strip()) / 1000.0)
        except ValueError:
            return None
    match = _DURATION_RE.match(value)
    if not match or not any(match.groupdict().values()):
        return None
    minutes = float(match.group("minutes") or 0.0)
    seconds = float(match.group("seconds") or 0.0)
    return max(0.0, minutes * 60.0 + seconds)


def _body_retry_seconds(detail: str) -> float | None:
    match = _RETRY_IN_RE.search(detail or "")
    if not match:
        return None
    amount = float(match.group(1))
    unit = (match.group(2) or "s").lower()
    if unit.startswith("ms") or unit.startswith("millisecond"):
        return amount / 1000.0
    if unit.startswith("m") and not unit.startswith("ms"):
        return amount * 60.0
    return amount


def _retry_after_seconds(response: httpx.Response, detail: str, attempt: int) -> float:
    """Use every Groq reset hint and wait for the safest advertised token window."""
    hints: list[float] = []
    retry_after = _duration_seconds(response.headers.get("retry-after"))
    if retry_after is not None:
        hints.append(retry_after)
    token_reset = _duration_seconds(response.headers.get("x-ratelimit-reset-tokens"))
    if token_reset is not None:
        hints.append(token_reset)
    body_retry = _body_retry_seconds(detail)
    if body_retry is not None:
        hints.append(body_retry)

    if hints:
        wait = max(hints) + _RATE_LIMIT_SAFETY_SECONDS
        return min(_MAX_RATE_LIMIT_SLEEP_SECONDS, max(0.25, wait))
    return float(min(2**attempt, 8))


def _is_schema_generation_error(status: int, detail: str) -> bool:
    """Recognize Groq's provider-side structured-generation validation failure."""
    if status != 400:
        return False
    lowered = detail.lower()
    return (
        "does not match the expected schema" in lowered
        or "jsonschema" in lowered
        or "failed_generation" in lowered
    )


def _validation_feedback(exc: ValidationError) -> str:
    """Return a bounded repair hint without dumping arbitrary model output."""
    issues: list[str] = []
    for error in exc.errors(include_input=False)[:8]:
        location = ".".join(str(part) for part in error.get("loc", ())) or "root"
        issues.append(f"{location}: {error.get('msg', 'invalid value')}")
    return "; ".join(issues)[:1200]


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
                    failed_generation = error.get("failed_generation")
                    if failed_generation and "failed_generation" not in detail.lower():
                        detail = f"{detail} failed_generation={failed_generation}"
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

    def _structured_payload(
        self,
        *,
        system: str,
        user: str,
        strict_schema: dict[str, Any],
        schema: type[BaseModel],
        completion_cap: int,
        json_object_fallback: bool,
        validation_feedback: str | None,
    ) -> dict[str, Any]:
        system_content = (
            f"{system}\n\n"
            "Return only the requested structured object. Never invent evidence or values. "
            "If evidence is insufficient, encode that honestly in the provided fields."
        )
        if json_object_fallback:
            schema_hint = json.dumps(strict_schema, separators=(",", ":"), ensure_ascii=False)
            if len(schema_hint) > _SCHEMA_HINT_MAX_CHARS:
                schema_hint = schema_hint[:_SCHEMA_HINT_MAX_CHARS]
            system_content += (
                "\n\nGroq strict-schema compatibility recovery is active. Return exactly one JSON object, "
                "with no markdown or commentary. Match the requested schema as closely as possible; fields with "
                "application defaults may be omitted, but all semantic required fields and enum values must be valid. "
                f"Schema contract: {schema_hint}"
            )
            if validation_feedback:
                system_content += f"\nPrevious local validation issues to repair: {validation_feedback}"

        response_format: dict[str, Any]
        if json_object_fallback:
            response_format = {"type": "json_object"}
        else:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": _schema_name(schema),
                    "strict": True,
                    "schema": strict_schema,
                },
            }

        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user},
            ],
            "response_format": response_format,
            "temperature": 0,
            "reasoning_effort": self.reasoning_effort,
            "max_completion_tokens": completion_cap,
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
        generation_retries_remaining = self.max_retries
        generation_retry_attempt = 0
        rate_limit_retries_remaining = _MAX_RATE_LIMIT_RETRIES
        rate_limit_attempt = 0
        json_object_fallback = False
        validation_feedback: str | None = None
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                retry_delay: float | None = None
                payload = self._structured_payload(
                    system=system,
                    user=user,
                    strict_schema=strict_schema,
                    schema=schema,
                    completion_cap=completion_cap,
                    json_object_fallback=json_object_fallback,
                    validation_feedback=validation_feedback,
                )
                try:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    content = _JSON_FENCE_RE.sub("", self._content_text(response.json()).strip()).strip()
                    try:
                        return schema.model_validate_json(content)
                    except ValidationError as exc:
                        validation_feedback = _validation_feedback(exc)
                        last_error = AgentProviderError(
                            f"Groq returned JSON that failed local schema validation: {validation_feedback}"
                        )
                        if not json_object_fallback:
                            json_object_fallback = True
                            logger.warning(
                                "Groq strict output passed HTTP validation but failed local Pydantic validation; "
                                "switching to JSON Object compatibility recovery for schema=%s",
                                schema.__name__,
                            )
                            continue
                        if generation_retries_remaining <= 0:
                            break
                        generation_retries_remaining -= 1
                        generation_retry_attempt += 1
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    detail = self._safe_error_detail(exc.response)
                    suffix = f": {detail}" if detail else ""
                    last_error = AgentProviderError(f"Groq returned HTTP {status}{suffix}")

                    if _is_schema_generation_error(status, detail) and not json_object_fallback:
                        json_object_fallback = True
                        logger.warning(
                            "Groq strict structured generation failed; switching to JSON Object compatibility "
                            "recovery for schema=%s",
                            schema.__name__,
                        )
                        continue

                    if status == 413:
                        reduced_cap = _reduced_completion_cap(detail, completion_cap)
                        if reduced_cap is not None:
                            completion_cap = reduced_cap
                            await asyncio.sleep(0.25)
                            continue

                    if status == 429:
                        if rate_limit_retries_remaining <= 0:
                            raise last_error from exc
                        rate_limit_retries_remaining -= 1
                        retry_delay = _retry_after_seconds(exc.response, detail, rate_limit_attempt)
                        rate_limit_attempt += 1
                        logger.warning(
                            "Groq rate limit reached for schema=%s; waiting %.2fs before retry (%d/%d). "
                            "This wait does not consume the structured-generation retry budget.",
                            schema.__name__,
                            retry_delay,
                            rate_limit_attempt,
                            _MAX_RATE_LIMIT_RETRIES,
                        )
                        await asyncio.sleep(retry_delay)
                        continue

                    retryable = status in _RETRYABLE_HTTP_STATUS or status >= 500
                    if not retryable:
                        raise last_error from exc
                    if generation_retries_remaining <= 0:
                        break
                    generation_retries_remaining -= 1
                    generation_retry_attempt += 1
                except (httpx.HTTPError, json.JSONDecodeError, AgentProviderError) as exc:
                    last_error = exc
                    if generation_retries_remaining <= 0:
                        break
                    generation_retries_remaining -= 1
                    generation_retry_attempt += 1

                await asyncio.sleep(
                    retry_delay
                    if retry_delay is not None
                    else min(2 ** max(0, generation_retry_attempt - 1), 4)
                )

        raise AgentProviderError(f"structured generation failed after retries: {last_error}")
