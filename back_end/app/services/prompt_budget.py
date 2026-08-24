from __future__ import annotations

import math
from typing import Any, Iterable

from app.domain.schemas import EvidenceChunk, ExperimentResult


def clip_text(text: str, limit: int) -> str:
    """Bound prompt text without pretending truncated text is complete evidence."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    if limit <= 1:
        return normalized[:limit]
    return normalized[: max(0, limit - 1)].rstrip() + "…"


def estimate_tokens_from_chars(*values: str) -> int:
    """Conservative provider-independent token estimate used for observability.

    GPT-family tokenization is not a fixed chars/token ratio. Using three
    characters per token intentionally overestimates typical English prose so
    prompt packing stays comfortably below provider rate ceilings.
    """
    return sum(math.ceil(len(value) / 3) for value in values if value)


def pack_evidence(
    evidence: Iterable[EvidenceChunk],
    *,
    total_chars: int,
    per_chunk_chars: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Pack ranked evidence into a bounded prompt while preserving citations."""
    packed: list[dict[str, Any]] = []
    used = 0
    considered = 0

    for chunk in evidence:
        considered += 1
        remaining = total_chars - used
        if remaining <= 0:
            break
        text_budget = min(per_chunk_chars, remaining)
        text = clip_text(chunk.text, text_budget)
        if not text:
            continue
        packed.append(
            {
                "chunk_id": chunk.chunk_id,
                "title": clip_text(chunk.source_title, 180),
                "text": text,
            }
        )
        used += len(text)

    return packed, {
        "chunks_considered": considered,
        "chunks_packed": len(packed),
        "evidence_chars": used,
        "evidence_char_budget": total_chars,
    }


def compact_experiment(result: ExperimentResult) -> dict[str, Any]:
    """Give the Judge immutable statistical facts without redundant payload."""
    estimate = result.estimate
    if isinstance(estimate, list) and len(estimate) > 16:
        estimate = estimate[:16]

    return {
        "hypothesis_id": result.hypothesis_id,
        "test_used": result.test_used,
        "status": result.status,
        "statistic": result.statistic,
        "p_value": result.p_value,
        "effect_size": result.effect_size,
        "confidence_interval": result.confidence_interval,
        "estimate": estimate,
        "degrees_of_freedom": result.degrees_of_freedom,
        "conclusion": clip_text(result.conclusion, 900),
        "quality_flags": result.quality_flags[:12],
        "method_notes": clip_text(result.method_notes, 700),
        "evidence_chunk_ids": result.evidence_chunk_ids,
    }
