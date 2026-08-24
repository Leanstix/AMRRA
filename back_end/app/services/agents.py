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
from app.services.prompt_budget import compact_experiment, pack_evidence

_EXTRACTOR_EVIDENCE_CHAR_BUDGET = 10_000
_EXTRACTOR_CHUNK_CHAR_BUDGET = 1_200
_JUDGE_EVIDENCE_CHAR_BUDGET = 4_500
_JUDGE_CHUNK_CHAR_BUDGET = 650


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


EXTRACTOR_PROMPT_VERSION = "extractor-v2.5-groq-budgeted"
JUDGE_PROMPT_VERSION = "judge-v2.5-groq-budgeted"


class ExtractorAgent:
    def __init__(self, provider: AgentProvider):
        self.provider = provider

    async def run(self, query: str, evidence: list[EvidenceChunk]) -> ExtractionResult:
        evidence_payload, budget = pack_evidence(
            evidence,
            total_chars=_EXTRACTOR_EVIDENCE_CHAR_BUDGET,
            per_chunk_chars=_EXTRACTOR_CHUNK_CHAR_BUDGET,
        )
        allowed_ids = {item["chunk_id"] for item in evidence_payload}
        system = (
            "You are AMRRA's evidence extraction agent. Extract only claims and numerical observations that are "
            "explicitly supported by supplied evidence. Never manufacture groups, raw observations, sample sizes, "
            "or statistical results. Every hypothesis and observation must cite one or more supplied chunk_id values. "
            "If the evidence is not sufficient for a statistical experiment, preserve the hypothesis but leave "
            "unsupported numeric fields empty and explain the limitation in notes. Keep the response concise."
        )
        user = json.dumps(
            {
                "research_question": query,
                "evidence": evidence_payload,
                "prompt_budget": budget,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        payload = await self.provider.structured(
            system=system,
            user=user,
            schema=_ExtractionPayload,
            max_completion_tokens=getattr(self.provider, "extractor_max_completion_tokens", 1400),
        )

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

        notes = payload.notes
        if budget["chunks_packed"] < len(evidence):
            notes = (
                f"{notes} Evidence context was budgeted to {budget['chunks_packed']} of {len(evidence)} "
                "ranked chunks for this extraction pass."
            ).strip()
        return ExtractionResult(hypotheses=hypotheses, notes=notes)


class JudgeAgent:
    def __init__(self, provider: AgentProvider):
        self.provider = provider

    async def run(
        self,
        query: str,
        evidence: list[EvidenceChunk],
        experiments: list[ExperimentResult],
    ) -> JudgeReport:
        referenced_ids = {
            chunk_id
            for experiment in experiments
            for chunk_id in experiment.evidence_chunk_ids
        }
        relevant_evidence = [chunk for chunk in evidence if chunk.chunk_id in referenced_ids]
        if not relevant_evidence:
            relevant_evidence = evidence[:4]

        evidence_payload, budget = pack_evidence(
            relevant_evidence,
            total_chars=_JUDGE_EVIDENCE_CHAR_BUDGET,
            per_chunk_chars=_JUDGE_CHUNK_CHAR_BUDGET,
        )
        allowed_ids = {item["chunk_id"] for item in evidence_payload}
        experiment_payload = [compact_experiment(result) for result in experiments]

        system = (
            "You are AMRRA's judging agent. Synthesize immutable deterministic experiment results without changing "
            "their numbers. Distinguish statistical significance from practical importance, identify limitations, "
            "and cite only supplied evidence chunk IDs. If experiments are insufficient, say so explicitly. Never "
            "invent citations or results. Prefer a concise research assessment over repeating evidence verbatim."
        )
        user = json.dumps(
            {
                "research_question": query,
                "evidence": evidence_payload,
                "experiments": experiment_payload,
                "prompt_budget": budget,
            },
            default=str,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        payload = await self.provider.structured(
            system=system,
            user=user,
            schema=_JudgePayload,
            max_completion_tokens=getattr(self.provider, "judge_max_completion_tokens", 1000),
        )
        citations = [item for item in payload.citations if item.chunk_id in allowed_ids]
        return JudgeReport(
            title=payload.title,
            summary=payload.summary,
            conclusion=payload.conclusion,
            confidence=max(0.0, min(1.0, payload.confidence)),
            limitations=payload.limitations,
            citations=citations,
        )
