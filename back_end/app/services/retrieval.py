from __future__ import annotations

import json
import math
import re
from collections import Counter

from pydantic import BaseModel, Field

from app.domain.schemas import EvidenceChunk, SourceInput
from app.providers.base import AgentProvider
from app.services.prompt_budget import pack_evidence

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_RERANK_EVIDENCE_CHAR_BUDGET = 8_000
_RERANK_CHUNK_CHAR_BUDGET = 550
RETRIEVER_PROMPT_VERSION = "retriever-v2.5-groq-budgeted"


class _RerankItem(BaseModel):
    chunk_id: str
    relevance: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class _RerankPayload(BaseModel):
    rankings: list[_RerankItem] = Field(default_factory=list)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def chunk_text(text: str, *, size: int = 220, overlap: int = 40) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + size]).strip()
        if piece:
            chunks.append(piece)
        if start + size >= len(words):
            break
    return chunks


def lexical_score(query: str, text: str) -> float:
    q = Counter(tokenize(query))
    d = Counter(tokenize(text))
    if not q or not d:
        return 0.0
    intersection = sum(min(q[t], d[t]) for t in q)
    norm = math.sqrt(sum(v * v for v in q.values()) * sum(v * v for v in d.values()))
    return float(intersection / norm) if norm else 0.0


class Retriever:
    """Deterministic candidate generation followed by bounded LLM reranking."""

    def __init__(self, provider: AgentProvider | None = None):
        self.provider = provider

    async def retrieve(self, query: str, sources: list[SourceInput], top_k: int) -> list[EvidenceChunk]:
        candidates: list[EvidenceChunk] = []
        for source_index, source in enumerate(sources):
            if source.kind != "text" or not source.content:
                continue
            source_id = f"source-{source_index + 1}"
            for index, text in enumerate(chunk_text(source.content)):
                lexical = lexical_score(query, text)
                candidates.append(
                    EvidenceChunk(
                        chunk_id=f"{source_id}-chunk-{index + 1}",
                        source_id=source_id,
                        source_title=source.title,
                        text=text,
                        score=lexical,
                        metadata={"chunk_index": index, "lexical_score": lexical},
                    )
                )

        if not candidates:
            return []

        candidates.sort(key=lambda item: item.score, reverse=True)
        shortlist_size = min(len(candidates), max(top_k * 3, top_k))
        shortlist = candidates[:shortlist_size]

        if self.provider and getattr(self.provider, "rerank_enabled", True) and len(shortlist) > 1:
            packed, budget = pack_evidence(
                shortlist,
                total_chars=_RERANK_EVIDENCE_CHAR_BUDGET,
                per_chunk_chars=_RERANK_CHUNK_CHAR_BUDGET,
            )
            lexical_by_id = {
                item.chunk_id: float(item.metadata["lexical_score"])
                for item in shortlist
            }
            rerank_candidates = [
                {**item, "lexical_score": lexical_by_id[item["chunk_id"]]}
                for item in packed
            ]
            system = (
                "You are AMRRA's retrieval reranking agent. Score how directly each supplied evidence chunk helps "
                "answer the research question. Use only supplied chunk_id values. Do not infer new facts, rewrite "
                "evidence, or include unknown IDs. Relevance is 0 to 1. Keep reasons short."
            )
            user = json.dumps(
                {
                    "research_question": query,
                    "candidates": rerank_candidates,
                    "prompt_budget": budget,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            try:
                reranked = await self.provider.structured(
                    system=system,
                    user=user,
                    schema=_RerankPayload,
                    max_completion_tokens=getattr(self.provider, "rerank_max_completion_tokens", 512),
                )
                allowed = {item.chunk_id: item for item in shortlist}
                packed_ids = {item["chunk_id"] for item in packed}
                seen: set[str] = set()
                for rank, result in enumerate(reranked.rankings, start=1):
                    item = allowed.get(result.chunk_id)
                    if item is None or result.chunk_id not in packed_ids or result.chunk_id in seen:
                        continue
                    seen.add(result.chunk_id)
                    lexical = float(item.metadata["lexical_score"])
                    item.score = (0.25 * lexical) + (0.75 * result.relevance)
                    item.metadata.update(
                        {
                            "agent_relevance": result.relevance,
                            "agent_reason": result.reason,
                            "agent_rank": rank,
                            "rerank_context_chars": budget["evidence_chars"],
                        }
                    )
            except Exception as exc:
                for item in shortlist:
                    item.metadata["rerank_fallback"] = exc.__class__.__name__

        shortlist.sort(key=lambda item: item.score, reverse=True)
        return shortlist[: min(top_k, len(shortlist))]
