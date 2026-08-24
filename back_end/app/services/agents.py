from __future__ import annotations

import json
import uuid

from pydantic import BaseModel, Field

from app.domain.schemas import (
    Citation,
    EvidenceChunk,
    ExperimentResult,
    ExtractionResult,
    Hypothesis,
    JudgeReport,
    Observation,
)
from app.providers.base import AgentProvider


class _ObservationPayload(BaseModel):
    name: str
    role: str = "unknown"
    value_type: str = "unknown"
    group: str | None = None
    values: list[float] = Field(default_factory=list)
    mean: float | None = None
    sd: float | None = None
    n: int | None = None
    count: int | None = None
    category: str | None = None
    unit: str | None = None
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class _HypothesisPayload(BaseModel):
    statement: str
    variables: list[str] = Field(default_factory=list)
    observations: list[_ObservationPayload] = Field(default_factory=list)
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class _ExtractionPayload(BaseModel):
    hypotheses: list[_HypothesisPayload] = Field(default_factory=list)
    notes: str = ""


class _JudgePayload(BaseModel):
    title: str
    summary: str
    conclusion: str
    confidence: float
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


EXTRACTOR_PROMPT_VERSION = "extractor-v2.4-groq-gptoss20b"
JUDGE_PROMPT_VERSION = "judge-v2.4-groq-gptoss20b"


class ExtractorAgent:
    def __init__(self, provider: AgentProvider):
        self.provider = provider

    async def run(self, query: str, evidence: list[EvidenceChunk]) -> ExtractionResult:
        allowed_ids = {chunk.chunk_id for chunk in evidence}
        evidence_payload = [
            {"chunk_id": chunk.chunk_id, "title": chunk.source_title, "text": chunk.text}
            for chunk in evidence
        ]
        system = (
            "You are AMRRA's evidence extraction agent. Extract only claims and numerical observations that are "
            "explicitly supported by supplied evidence. Never manufacture groups, raw observations, sample sizes, "
            "or statistical results. Every hypothesis and observation must cite one or more supplied chunk_id values. "
            "If the evidence is not sufficient for a statistical experiment, preserve the hypothesis but leave "
            "unsupported numeric fields empty and explain the limitation in notes."
        )
        user = f"Research question: {query}\nEvidence:\n{json.dumps(evidence_payload, ensure_ascii=False)}"
        payload = await self.provider.structured(system=system, user=user, schema=_ExtractionPayload)

        hypotheses: list[Hypothesis] = []
        for item in payload.hypotheses:
            hypothesis_refs = [ref for ref in item.evidence_chunk_ids if ref in allowed_ids]
            observations: list[Observation] = []
            for raw in item.observations:
                refs = [ref for ref in raw.evidence_chunk_ids if ref in allowed_ids]
                if not refs:
                    continue
                try:
                    observations.append(
                        Observation.model_validate({**raw.model_dump(), "evidence_chunk_ids": refs})
                    )
                except Exception:
                    continue
            if not hypothesis_refs:
                hypothesis_refs = list(dict.fromkeys(ref for obs in observations for ref in obs.evidence_chunk_ids))
            if not hypothesis_refs:
                continue
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=str(uuid.uuid4()),
                    statement=item.statement,
                    variables=item.variables,
                    observations=observations,
                    evidence_chunk_ids=hypothesis_refs,
                    confidence=max(0.0, min(1.0, item.confidence)),
                )
            )

        return ExtractionResult(hypotheses=hypotheses, notes=payload.notes)


class JudgeAgent:
    def __init__(self, provider: AgentProvider):
        self.provider = provider

    async def run(
        self,
        query: str,
        evidence: list[EvidenceChunk],
        experiments: list[ExperimentResult],
    ) -> JudgeReport:
        allowed_ids = {chunk.chunk_id for chunk in evidence}
        system = (
            "You are AMRRA's judging agent. Synthesize deterministic experiment results without changing their "
            "numbers. Distinguish statistical significance from practical importance, identify limitations, and "
            "cite only supplied evidence chunk IDs. If experiments are insufficient, say so explicitly. Never "
            "invent citations or results."
        )
        user = json.dumps(
            {
                "research_question": query,
                "evidence": [chunk.model_dump() for chunk in evidence],
                "experiments": [result.model_dump() for result in experiments],
            },
            default=str,
        )
        payload = await self.provider.structured(system=system, user=user, schema=_JudgePayload)
        citations = [item for item in payload.citations if item.chunk_id in allowed_ids]
        return JudgeReport(
            title=payload.title,
            summary=payload.summary,
            conclusion=payload.conclusion,
            confidence=max(0.0, min(1.0, payload.confidence)),
            limitations=payload.limitations,
            citations=citations,
        )
