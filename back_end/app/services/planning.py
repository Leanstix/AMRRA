from __future__ import annotations

from collections import defaultdict

from app.domain.schemas import ExperimentPlan, Hypothesis, Observation


class ExperimentPlanner:
    """Selects deterministic tools from semantically typed evidence.

    The planner deliberately refuses to infer statistical samples from arbitrary numbers in prose.
    It only schedules a test when the extractor has represented enough data to satisfy the tool's
    preconditions.
    """

    def plan(self, hypotheses: list[Hypothesis]) -> list[ExperimentPlan]:
        return [self._plan_one(h) for h in hypotheses]

    def _plan_one(self, hypothesis: Hypothesis) -> ExperimentPlan:
        raw_groups: dict[str, list[float]] = defaultdict(list)
        summary_groups: dict[str, dict] = {}
        counts: list[dict] = []
        predictors: list[Observation] = []
        outcomes: list[Observation] = []

        for obs in hypothesis.observations:
            if obs.value_type == "raw_numeric" and obs.group and obs.values:
                raw_groups[obs.group].extend(obs.values)
            elif obs.value_type == "summary" and obs.group and obs.mean is not None and obs.sd is not None and obs.n:
                summary_groups[obs.group] = {"mean": obs.mean, "sd": obs.sd, "n": obs.n}
            elif obs.value_type == "categorical_count" and obs.category is not None and obs.count is not None:
                counts.append({"category": obs.category, "group": obs.group or "observed", "count": obs.count})
            if obs.role == "predictor" and obs.values:
                predictors.append(obs)
            if obs.role == "outcome" and obs.values:
                outcomes.append(obs)

        refs = hypothesis.evidence_chunk_ids
        if len(raw_groups) == 2 and all(len(v) >= 2 for v in raw_groups.values()):
            return ExperimentPlan(
                hypothesis_id=hypothesis.hypothesis_id,
                test="welch_ttest",
                rationale="Two independent groups contain at least two explicit raw numeric observations each.",
                input_data={"groups": dict(raw_groups)},
                evidence_chunk_ids=refs,
            )
        if len(summary_groups) == 2:
            return ExperimentPlan(
                hypothesis_id=hypothesis.hypothesis_id,
                test="welch_ttest",
                rationale="Two groups provide explicit mean, standard deviation, and sample size summaries.",
                input_data={"group_summaries": summary_groups},
                evidence_chunk_ids=refs,
            )
        if len(raw_groups) > 2 and all(len(v) >= 2 for v in raw_groups.values()):
            return ExperimentPlan(
                hypothesis_id=hypothesis.hypothesis_id,
                test="anova",
                rationale="More than two independent groups contain explicit raw numeric observations.",
                input_data={"groups": dict(raw_groups)},
                evidence_chunk_ids=refs,
            )
        if counts:
            groups = sorted({item["group"] for item in counts})
            categories = sorted({item["category"] for item in counts})
            if len(groups) >= 2 and len(categories) >= 2:
                table = [
                    [
                        next(
                            (x["count"] for x in counts if x["group"] == group and x["category"] == category),
                            0,
                        )
                        for category in categories
                    ]
                    for group in groups
                ]
                return ExperimentPlan(
                    hypothesis_id=hypothesis.hypothesis_id,
                    test="chi_square",
                    rationale="Evidence contains an explicit categorical contingency table.",
                    input_data={"groups": groups, "categories": categories, "table": table},
                    evidence_chunk_ids=refs,
                )
        if len(predictors) == 1 and len(outcomes) == 1:
            x, y = predictors[0].values, outcomes[0].values
            if len(x) == len(y) and len(x) >= 3:
                return ExperimentPlan(
                    hypothesis_id=hypothesis.hypothesis_id,
                    test="linear_regression",
                    rationale="Paired predictor/outcome observations are explicitly represented with equal length.",
                    input_data={"x": x, "y": y},
                    evidence_chunk_ids=refs,
                )

        return ExperimentPlan(
            hypothesis_id=hypothesis.hypothesis_id,
            test="descriptive",
            rationale="Evidence does not satisfy the preconditions for a supported inferential test without inventing data.",
            input_data={},
            evidence_chunk_ids=refs,
        )
