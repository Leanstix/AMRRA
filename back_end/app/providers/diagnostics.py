from __future__ import annotations

from dataclasses import asdict, dataclass

from app.providers.agentrouter import AgentRouterProvider


@dataclass(frozen=True)
class AgentRouterDiagnostic:
    reachable: bool
    authenticated: bool
    model_available: bool
    model: str
    key_fingerprint: str
    status_code: int | None = None
    detail: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


async def diagnose_agentrouter(provider: AgentRouterProvider) -> AgentRouterDiagnostic:
    result = await provider.check_connection()
    return AgentRouterDiagnostic(
        reachable=result["reachable"],
        authenticated=result["authenticated"],
        model_available=result["model_available"],
        model=provider.model_name,
        key_fingerprint=provider.key_fingerprint,
        status_code=result.get("status_code"),
        detail=result.get("detail"),
    )
