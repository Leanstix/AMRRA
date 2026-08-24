from __future__ import annotations

import asyncio
import json

from app.core.config import get_settings
from app.providers.agentrouter import AgentProviderError, AgentRouterProvider


async def diagnose() -> dict:
    settings = get_settings()
    try:
        provider = AgentRouterProvider(settings)
    except AgentProviderError as exc:
        return {
            "configured": False,
            "model": settings.agentrouter_model,
            "base_url": settings.agentrouter_base_url,
            "error": str(exc),
        }

    result = await provider.check_connection()
    return {
        "configured": True,
        "model": provider.model_name,
        "base_url": provider.api_base,
        "key_fingerprint": provider.key_fingerprint,
        **result,
    }


def main() -> None:
    result = asyncio.run(diagnose())
    print(json.dumps(result, indent=2))
    if not result.get("authenticated") or not result.get("model_available"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
