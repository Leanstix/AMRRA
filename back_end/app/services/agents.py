from __future__ import annotations

import json
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.domain.schemas import (
    Citation,
    EvidenceChunk,
    ExperimentResult,
    ExtractionResult,
    Hypothesis,
    JudgeReport,
    Observation,
)
from app.providers.base import AgentProvider, AgentProviderError
from app.services.prompt_budget import compact_experiment, pack_evidence

_EXTRACTOR_EVIDENCE_CHAR_BUDGET = 10_000
_EXTRACTOR_CHUNK_CHAR_BUDGET = 1_200
_RECOVERY_EVIDENCE_CHAR_BUDGET = 5_000
_RECOVERY_CHUNK_CHAR_BUDGET = 1_100
_RECOVERY_MAX_COMPLETION_TOKENS = 700
_JUDGE_EVIDENCE_CHAR_BUDGET = 4_500
_JUDGE_CHUNK_CHAR_BUDGET = 650


class _ObservationPayload(BaseModel):
    name: str = Field(min_length=1)
    role: Literal["outcome", "predictor", "group", "count", "unknown"] = "unknown"
    value_type: Literal[
        "raw_numeric",
        "summary",
        "categorical_count",
        "binary",
        "unknown",
    ] = "unknown"
    group: str | None = None
    values: list[float] = Field(default_factory=list)
    mean: float | None = None
    sd: float | None = None
    n: int | None = None
    count: int | None = None
    category: str | None = None
    unit: str | None = None
    evidence_chunk_ids: list[str] = Field(min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class _HypothesisPayload(BaseModel):
    statement: str = Field(min_length=3)
    variables: list[str] = Field(default_factory=list)
    observations: list[_ObservationPayload] = Field(default_factory=list)
    evidence_chunk_ids: list[str] = Field(min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


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


EXTRACTOR_PROMPT_VERSION = "extractor-v2.6-grounded-recovery"
JUDGE_PROMPT_VERSION = "judge-v2.6-evidence-fallback"


def _ground_hypotheses(
    payload: _ExtractionPayload,
    allowed_ids: set[str],
) -> tuple[list[Hypothesis], dict[str, int]]:
    """Convert provider output into trusted hypotheses and explain every drop.

    Provider structured-output validation constrains the shape, but evidence IDs
    are runtime values and therefore still need grounding against the Retriever's
    actual chunk set. Keeping counters makes an empty extraction diagnosable
    rather than looking like a mysterious model failure.
    """
    hypotheses: list[Hypothesis] = []
    diagnostics = {
        "raw_hypotheses": len(payload.hypotheses),
        "grounded_hypotheses": 0,
        "raw_observations": 0,
        "grounded_observations": 0,
        "dropped_hypotheses_no_grounded_citation": 0,
        "dropped_observations_no_grounded_citation": 0,
        "dropped_observations_domain_validation": 0,
    }

    for item in payload.hypotheses:
        hypothesis_refs = list(
            dict.fromkeys(ref for ref in item.evidence_chunk_ids if ref in allowed_ids)
        )
        observations: list[Observation] = []

        for raw in item.observations:
            diagnostics["raw_observations"] += 1
            refs = list(
                dict.fromkeys(ref for ref in raw.evidence_chunk_ids if ref in allowed_ids)
            )
            if not refs:
                diagnostics["dropped_observations_no_grounded_citation"] += 1
                continue
            try:
                observations.append(
                    Observation.model_validate({**raw.model_dump(), "evidence_chunk_ids": refs})
                )
                diagnostics["grounded_observations"] += 1
            except ValidationError:
                diagnostics["dropped_observations_domain_validation"] += 1

        # A hypothesis may cite its evidence directly or inherit citations from
        # grounded observations. It does not need numeric observations to remain
        # a legitimate qualitative/descriptive research hypothesis.
        if not hypothesis_refs:
            hypothesis_refs = list(
                dict.fromkeys(ref for obs in observations for ref in obs.evidence_chunk_ids)
            )
        if not hypothesis_refs:
            diagnostics["dropped_hypotheses_no_grounded_citation"] += 1
            continue

        hypotheses.append(
            Hypothesis(
                hypothesis_id=str(uuid.uuid4()),
                statement=item.statement,
                variables=item.variables,
                observations=observations,
                evidence_chunk_ids=hypothesis_refs,
                confidence=item.confidence,
            )
        )

    diagnostics["grounded_hypotheses"] = len(hypotheses)
    return hypotheses, diagnostics


class ExtractorAgent:
    def __init__(self, provider: AgentProvider):
        self.provider = provider
        self.last_diagnostics: dict[str, Any] = {}

    async def run(self, query: str, evidence: list[EvidenceChunk]) -> ExtractionResult:
        self.last_diagnostics = {}
        evidence_payload, budget = pack_evidence(
            evidence,
            total_chars=_EXTRACTOR_EVIDENCE_CHAR_BUDGET,
            per_chunk_chars=_EXTRACTOR_CHUNK_CHAR_BUDGET,
        )
        allowed_ids = {item["chunk_id"] for item in evidence_payload}
        system = (
            "You are AMRRA's evidence extraction agent. Extract research hypotheses and observations only when "
            "they are supported by the supplied evidence. A hypothesis may be qualitative and does NOT need enough "
            "numeric data for an inferential statistical test. Never manufacture groups, raw observations, sample "
            "sizes, or statistical results. Every returned hypothesis and every returned observation MUST cite at "
            "least one exact supplied chunk_id. Use only these role values: outcome, predictor, group, count, unknown. "
            "Use only these value_type values: raw_numeric, summary, categorical_count, binary, unknown. If numeric "
            "evidence is insufficient, preserve a supported hypothesis with an empty observations list and explain "
            "the limitation in notes. Return hypotheses=[] only when none of the supplied chunks supports a claim "
            "relevant to the research question. Keep the response concise."
        )
        user = json.dumps(
            {
                "research_question": query,
                "allowed_chunk_ids": sorted(allowed_ids),
                "evidence": evidence_payload,
                "prompt_budget": budget,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        primary = await self.provider.structured(
            system=system,
            user=user,
            schema=_ExtractionPayload,
            max_completion_tokens=getattr(self.provider, "extractor_max_completion_tokens", 1400),
        )
        hypotheses, primary_diagnostics = _ground_hypotheses(primary, allowed_ids)

        recovery_attempted = False
        recovery_error: str | None = None
        recovery_diagnostics: dict[str, int] | None = None
        recovery_budget: dict[str, int] | None = None
        recovery_notes = ""

        # Structured generation can still legitimately choose an empty list, and
        # runtime citation grounding can remove provider output that references a
        # non-existent chunk. Before declaring the evidence unsupported, give the
        # model one focused pass over the highest-ranked evidence with a smaller
        # output reservation. This is deliberately not an automatic fabrication:
        # the recovery prompt is allowed to return an empty list again.
        if not hypotheses and evidence_payload:
            recovery_attempted = True
            recovery_source = evidence[: min(4, len(evidence))]
            recovery_payload, recovery_budget = pack_evidence(
                recovery_source,
                total_chars=_RECOVERY_EVIDENCE_CHAR_BUDGET,
                per_chunk_chars=_RECOVERY_CHUNK_CHAR_BUDGET,
            )
            recovery_allowed_ids = {item["chunk_id"] for item in recovery_payload}
            recovery_system = (
                "You are AMRRA's grounded extraction recovery agent. A previous extraction produced no usable "
                "grounded hypothesis. Re-evaluate ONLY the supplied high-ranked evidence. If any chunk supports a "
                "claim relevant to the research question, return one or more concise, assessable hypotheses and cite "
                "the exact chunk_id values. A hypothesis may be qualitative; do not require numerical observations. "
                "Do not invent measurements, sample sizes, causal claims, or statistics. Return hypotheses=[] only "
                "if the supplied evidence genuinely supports no relevant claim."
            )
            recovery_user = json.dumps(
                {
                    "research_question": query,
                    "allowed_chunk_ids": sorted(recovery_allowed_ids),
                    "evidence": recovery_payload,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            try:
                recovered = await self.provider.structured(
                    system=recovery_system,
                    user=recovery_user,
                    schema=_ExtractionPayload,
                    max_completion_tokens=min(
                        getattr(self.provider, "extractor_max_completion_tokens", 1400),
                        _RECOVERY_MAX_COMPLETION_TOKENS,
                    ),
                )
                hypotheses, recovery_diagnostics = _ground_hypotheses(
                    recovered,
                    recovery_allowed_ids,
                )
                recovery_notes = recovered.notes
            except AgentProviderError as exc:
                # Recovery is opportunistic. The primary extraction already
                # completed successfully, so a temporary rate/provider failure
                # here must not turn "insufficient evidence" into a crashed run.
                recovery_error = f"{exc.__class__.__name__}: {str(exc)[:300]}"

        notes_parts = [primary.notes.strip(), recovery_notes.strip()]
        if budget["chunks_packed"] < len(evidence):
            notes_parts.append(
                f"Primary extraction context used {budget['chunks_packed']} of {len(evidence)} ranked chunks."
            )
        if recovery_attempted and not hypotheses:
            notes_parts.append(
                "No evidence-backed hypothesis survived grounding after the focused recovery pass; "
                "the run will continue as an evidence-only assessment."
            )
        notes = " ".join(part for part in notes_parts if part).strip()

        self.last_diagnostics = {
            "primary_budget": budget,
            "primary": primary_diagnostics,
            "recovery_attempted": recovery_attempted,
            "recovery_budget": recovery_budget,
            "recovery": recovery_diagnostics,
            "recovery_error": recovery_error,
            "final_grounded_hypotheses": len(hypotheses),
        }
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
            "and cite only supplied evidence chunk IDs. If there are no experiments, produce an evidence-only "
            "assessment and state clearly that AMRRA could not support an inferential hypothesis/test from the "
            "available evidence. Never invent citations or results. Prefer a concise research assessment over "
            "repeating evidence verbatim."
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
