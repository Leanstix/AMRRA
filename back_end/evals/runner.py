from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.config import Settings
from app.domain.schemas import RunRequest, SourceInput
from app.factory import build_orchestrator
from app.infrastructure.repository import RunRepository
from app.providers.agentrouter import FakeProvider
from app.services.ingestion import SourceIngestor
from app.services.orchestrator import AgentOrchestrator

CASES_PATH = Path(__file__).with_name("golden_cases.json")


@dataclass
class EvalCaseResult:
    case_id: str
    completed: bool
    schema_valid: bool
    citation_grounded: bool
    tool_correct: bool
    significance_correct: bool | None
    error: str | None = None


def _judge_payload(case: dict) -> dict:
    return {
        "title": f"Evaluation: {case['case_id']}",
        "summary": "Evaluation fixture synthesis.",
        "conclusion": "The deterministic result is preserved.",
        "confidence": 0.9,
        "limitations": [],
        "citations": [{"chunk_id": "source-1-chunk-1", "claim": "fixture evidence"}],
    }


async def evaluate_case(case: dict, *, live: bool = False) -> EvalCaseResult:
    with tempfile.TemporaryDirectory(prefix="amrra-eval-") as tmp:
        settings = Settings(
            environment="evaluation",
            database_url=f"sqlite:///{Path(tmp) / 'eval.db'}",
        )
        repository = RunRepository(settings.database_url)
        try:
            if live:
                orchestrator = build_orchestrator(settings=settings, repository=repository)
            else:
                provider = FakeProvider([case["extraction"], _judge_payload(case)])
                orchestrator = AgentOrchestrator(
                    repository=repository,
                    provider=provider,
                    ingestor=SourceIngestor(settings),
                )

            run_id = str(uuid.uuid4())
            request = RunRequest(
                query=case["query"],
                sources=[SourceInput(kind="text", title=case["case_id"], content=case["source"])],
                top_k=3,
            )
            repository.create_run(run_id, request.query, request.model_dump(mode="json"))
            try:
                await orchestrator.run(run_id)
            except Exception as exc:
                snapshot = repository.snapshot(run_id)
                return EvalCaseResult(
                    case_id=case["case_id"],
                    completed=False,
                    schema_valid=bool(snapshot.traces),
                    citation_grounded=False,
                    tool_correct=False,
                    significance_correct=None,
                    error=f"{exc.__class__.__name__}: {exc}",
                )

            snapshot = repository.snapshot(run_id)
            evidence_ids = {item.chunk_id for item in snapshot.evidence}
            citation_grounded = bool(snapshot.report) and all(
                citation.chunk_id in evidence_ids for citation in snapshot.report.citations
            )
            tool_correct = bool(snapshot.plans) and snapshot.plans[0].test == case["expected_test"]
            expected_significant = case.get("expected_significant")
            significance_correct = None
            if expected_significant is not None and snapshot.experiments:
                p_value = snapshot.experiments[0].p_value
                significance_correct = p_value is not None and (p_value < 0.05) == expected_significant

            return EvalCaseResult(
                case_id=case["case_id"],
                completed=snapshot.status.value == "completed",
                schema_valid=True,
                citation_grounded=citation_grounded,
                tool_correct=tool_correct,
                significance_correct=significance_correct,
            )
        finally:
            repository.close()


async def run_evals(*, live: bool = False) -> dict:
    cases = json.loads(CASES_PATH.read_text())
    results = [await evaluate_case(case, live=live) for case in cases]
    scored = [asdict(result) for result in results]
    metrics = {
        "cases": len(results),
        "completion_rate": sum(r.completed for r in results) / len(results),
        "schema_valid_rate": sum(r.schema_valid for r in results) / len(results),
        "citation_grounding_rate": sum(r.citation_grounded for r in results) / len(results),
        "tool_selection_accuracy": sum(r.tool_correct for r in results) / len(results),
    }
    significance = [r.significance_correct for r in results if r.significance_correct is not None]
    metrics["significance_accuracy"] = (
        sum(bool(value) for value in significance) / len(significance) if significance else None
    )
    return {"mode": "live" if live else "offline", "metrics": metrics, "results": scored}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AMRRA agent-quality evaluations")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use GPT-5.6 Sol through the configured AgentRouter account instead of fixtures",
    )
    args = parser.parse_args()
    report = asyncio.run(run_evals(live=args.live))
    print(json.dumps(report, indent=2))
    scored_values = [
        value
        for key, value in report["metrics"].items()
        if key != "cases" and value is not None
    ]
    if any(value < 1.0 for value in scored_values):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
