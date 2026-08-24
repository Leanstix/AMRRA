from __future__ import annotations

import asyncio

from app.domain.schemas import RunRequest, RunStatus, StageName
from app.infrastructure.repository import RunRepository
from app.providers.base import AgentProvider
from app.services.agents import EXTRACTOR_PROMPT_VERSION, JUDGE_PROMPT_VERSION, ExtractorAgent, JudgeAgent
from app.services.ingestion import SourceIngestor
from app.services.observability import TraceManager
from app.services.planning import ExperimentPlanner
from app.services.retrieval import RETRIEVER_PROMPT_VERSION, Retriever
from app.services.statistics import StatisticalToolbox


class PipelineError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class AgentOrchestrator:
    def __init__(
        self,
        *,
        repository: RunRepository,
        provider: AgentProvider,
        ingestor: SourceIngestor,
    ):
        self.repository = repository
        self.provider = provider
        self.ingestor = ingestor
        self.retriever = Retriever(provider)
        self.extractor = ExtractorAgent(provider)
        self.planner = ExperimentPlanner()
        self.toolbox = StatisticalToolbox()
        self.judge = JudgeAgent(provider)
        self.traces = TraceManager(repository)

    async def run(self, run_id: str) -> None:
        self.repository.set_status(run_id, RunStatus.RUNNING)
        try:
            payload = self.repository.get_payload(run_id)
            request = RunRequest.model_validate(payload)

            with self.traces.stage(run_id, StageName.INGESTION, input_data=payload["sources"]) as trace:
                sources = await self.ingestor.materialize(request.sources)
                trace["output"] = [
                    {"kind": item.kind, "title": item.title, "chars": len(item.content or "")}
                    for item in sources
                ]

            with self.traces.stage(
                run_id,
                StageName.RETRIEVAL,
                input_data={"query": request.query, "sources": trace["output"]},
                model=self.provider.model_name,
                prompt_version=RETRIEVER_PROMPT_VERSION,
            ) as retrieval_trace:
                evidence = await self.retriever.retrieve(request.query, sources, request.top_k)
                if not evidence:
                    raise PipelineError("INSUFFICIENT_EVIDENCE", "No readable evidence chunks were retrieved")
                self.repository.patch_state(run_id, evidence=[item.model_dump(mode="json") for item in evidence])
                retrieval_trace["output"] = [item.model_dump(mode="json") for item in evidence]
                retrieval_trace["metadata"] = {
                    "provider": self.provider.provider_name,
                    "chunks": len(evidence),
                    "reranked": sum("agent_relevance" in item.metadata for item in evidence),
                }

            with self.traces.stage(
                run_id,
                StageName.EXTRACTION,
                input_data=retrieval_trace["output"],
                model=self.provider.model_name,
                prompt_version=EXTRACTOR_PROMPT_VERSION,
            ) as extraction_trace:
                extraction = await self.extractor.run(request.query, evidence)
                self.repository.patch_state(run_id, extraction=extraction.model_dump(mode="json"))
                extraction_trace["output"] = extraction.model_dump(mode="json")
                extraction_trace["metadata"] = {
                    "provider": self.provider.provider_name,
                    "grounded_hypotheses": len(extraction.hypotheses),
                    "evidence_only_fallback": not bool(extraction.hypotheses),
                    **self.extractor.last_diagnostics,
                }

            with self.traces.stage(
                run_id,
                StageName.PLANNING,
                input_data=extraction_trace["output"],
            ) as planning_trace:
                plans = self.planner.plan(extraction.hypotheses)
                self.repository.patch_state(run_id, plans=[plan.model_dump(mode="json") for plan in plans])
                planning_trace["output"] = [plan.model_dump(mode="json") for plan in plans]
                planning_trace["metadata"] = {
                    "tool_calls": [plan.test for plan in plans],
                    "evidence_only_fallback": not bool(plans),
                }

            with self.traces.stage(
                run_id,
                StageName.EXPERIMENTATION,
                input_data=planning_trace["output"],
            ) as experiment_trace:
                experiments = await asyncio.gather(
                    *[asyncio.to_thread(self.toolbox.execute, plan) for plan in plans]
                )
                self.repository.patch_state(
                    run_id,
                    experiments=[item.model_dump(mode="json") for item in experiments],
                )
                experiment_trace["output"] = [item.model_dump(mode="json") for item in experiments]
                experiment_trace["metadata"] = {
                    "completed": sum(item.status == "completed" for item in experiments),
                    "insufficient": sum(item.status == "insufficient_data" for item in experiments),
                    "evidence_only_fallback": not bool(experiments),
                }

            with self.traces.stage(
                run_id,
                StageName.JUDGING,
                input_data=experiment_trace["output"],
                model=self.provider.model_name,
                prompt_version=JUDGE_PROMPT_VERSION,
            ) as judge_trace:
                report = await self.judge.run(request.query, evidence, experiments)
                self.repository.patch_state(run_id, report=report.model_dump(mode="json"))
                judge_trace["output"] = report.model_dump(mode="json")
                judge_trace["metadata"] = {
                    "provider": self.provider.provider_name,
                    "evidence_only_fallback": not bool(experiments),
                }

            self.repository.set_status(run_id, RunStatus.COMPLETED)
        except Exception as exc:
            code = exc.code if isinstance(exc, PipelineError) else exc.__class__.__name__.upper()
            self.repository.set_status(
                run_id,
                RunStatus.FAILED,
                error_code=code,
                error_message=str(exc)[:2000],
            )
            raise
