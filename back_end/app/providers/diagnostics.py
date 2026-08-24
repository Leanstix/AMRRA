from __future__ import annotations

import asyncio
import json

from app.core.config import get_settings
from app.providers.base import AgentProviderError
from app.providers.groq import GroqProvider


async def diagnose() -> dict:
    settings = get_settings()
    try:
        provider = GroqProvider(settings)
    except AgentProviderError as exc:
        return {
            "configured": False,
            "provider": settings.llm_provider,
            "api_style": settings.llm_api_style,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "error": str(exc),
        }

    result = await provider.check_connection()
    return {
        "configured": True,
        "provider": provider.provider_name,
        "api_style": settings.llm_api_style,
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
