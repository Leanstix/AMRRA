from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

from app.domain.schemas import EvidenceChunk, SourceInput
from app.providers.cohere import AgentProvider

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


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


def cosine(a: list[float], b: list[float]) -> float:
    av = np.asarray(a, dtype=float)
    bv = np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom == 0:
        return 0.0
    return float(np.dot(av, bv) / denom)


class Retriever:
    def __init__(self, provider: AgentProvider | None = None):
        self.provider = provider

    async def retrieve(self, query: str, sources: list[SourceInput], top_k: int) -> list[EvidenceChunk]:
        candidates: list[EvidenceChunk] = []
        for source_index, source in enumerate(sources):
            if source.kind != "text" or not source.content:
                continue
            source_id = f"source-{source_index + 1}"
            for index, text in enumerate(chunk_text(source.content)):
                candidates.append(
                    EvidenceChunk(
                        chunk_id=f"{source_id}-chunk-{index + 1}",
                        source_id=source_id,
                        source_title=source.title,
                        text=text,
                        score=lexical_score(query, text),
                        metadata={"chunk_index": index},
                    )
                )

        if not candidates:
            return []

        if self.provider:
            try:
                query_vec = (await self.provider.embed([query], input_type="search_query"))[0]
                doc_vecs = await self.provider.embed([item.text for item in candidates], input_type="search_document")
                for item, vec in zip(candidates, doc_vecs, strict=True):
                    semantic = cosine(query_vec, vec)
                    item.score = (0.35 * item.score) + (0.65 * semantic)
                    item.metadata["semantic_score"] = semantic
            except Exception as exc:
                for item in candidates:
                    item.metadata["embedding_fallback"] = exc.__class__.__name__

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[: min(top_k, len(candidates))]
