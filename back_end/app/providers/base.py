from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AgentProviderError(RuntimeError):
    """Raised when the configured production LLM provider cannot satisfy a request."""


class AgentProvider(Protocol):
    model_name: str
    provider_name: str
    rerank_enabled: bool

    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        max_completion_tokens: int | None = None,
    ) -> T: ...


class FakeProvider:
    """Deterministic provider used only by tests and offline evaluations."""

    model_name = "fake-agent"
    provider_name = "fake"

    def __init__(
        self,
        structured_responses: list[Any] | None = None,
        *,
        rerank_enabled: bool = False,
    ):
        self.responses = list(structured_responses or [])
        self.rerank_enabled = rerank_enabled
        self.calls: list[dict[str, Any]] = []

    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        max_completion_tokens: int | None = None,
    ) -> T:
        self.calls.append(
            {
                "system": system,
                "user": user,
                "schema": schema,
                "max_completion_tokens": max_completion_tokens,
            }
        )
        if not self.responses:
            raise AgentProviderError("no fake provider response configured")
        value = self.responses.pop(0)
        payload = value.model_dump() if isinstance(value, BaseModel) else value
        return schema.model_validate(payload)
