from __future__ import annotations

import math

import numpy as np
from scipy import stats

from app.domain.schemas import ExperimentPlan, ExperimentResult


def _hedges_g(a: np.ndarray, b: np.ndarray) -> float | None:
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None
    s1 = float(np.std(a, ddof=1))
    s2 = float(np.std(b, ddof=1))
    pooled_denom = n1 + n2 - 2
    if pooled_denom <= 0:
        return None
    pooled = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / pooled_denom)
    if pooled == 0:
        return 0.0
    d = (float(np.mean(a)) - float(np.mean(b))) / pooled
    correction = 1 - (3 / (4 * (n1 + n2) - 9)) if (4 * (n1 + n2) - 9) else 1
    return float(d * correction)


def _cramers_v(table: np.ndarray, chi2: float) -> float | None:
    n = float(table.sum())
    if n <= 0:
        return None
    rows, cols = table.shape
    denominator = min(rows - 1, cols - 1)
    if denominator <= 0:
        return None
    return float(math.sqrt((chi2 / n) / denominator))


class StatisticalToolbox:
    def execute(self, plan: ExperimentPlan) -> ExperimentResult:
        try:
            if plan.test == "welch_ttest":
                return self._welch(plan)
            if plan.test == "anova":
                return self._anova(plan)
            if plan.test == "chi_square":
                return self._chi_square(plan)
            if plan.test == "linear_regression":
                return self._regression(plan)
            return ExperimentResult(
                hypothesis_id=plan.hypothesis_id,
                test_used="descriptive",
                status="insufficient_data",
                conclusion="No inferential test was run because the evidence does not contain a defensible statistical sample.",
                quality_flags=["insufficient_structured_evidence"],
                method_notes=plan.rationale,
                evidence_chunk_ids=plan.evidence_chunk_ids,
            )
        except (ValueError, TypeError, FloatingPointError) as exc:
            return ExperimentResult(
                hypothesis_id=plan.hypothesis_id,
                test_used=plan.test,
                status="failed",
                conclusion="The deterministic statistical tool rejected the supplied data.",
                quality_flags=["invalid_statistical_input"],
                method_notes=str(exc),
                evidence_chunk_ids=plan.evidence_chunk_ids,
            )

    def _welch(self, plan: ExperimentPlan) -> ExperimentResult:
        data = plan.input_data
        if "groups" in data:
            values = list(data["groups"].values())
            a, b = np.asarray(values[0], dtype=float), np.asarray(values[1], dtype=float)
            if len(a) < 2 or len(b) < 2:
                raise ValueError("Welch t-test requires at least two observations per group")
            test = stats.ttest_ind(a, b, equal_var=False)
            p = float(test.pvalue)
            statistic = float(test.statistic)
            mean_diff = float(np.mean(a) - np.mean(b))
            se = math.sqrt(float(np.var(a, ddof=1) / len(a) + np.var(b, ddof=1) / len(b)))
            numerator = se**4
            denominator = ((np.var(a, ddof=1) / len(a)) ** 2 / (len(a) - 1)) + ((np.var(b, ddof=1) / len(b)) ** 2 / (len(b) - 1))
            df = float(numerator / denominator) if denominator else None
            ci = None
            if df is not None and se > 0:
                critical = float(stats.t.ppf(0.975, df))
                ci = [mean_diff - critical * se, mean_diff + critical * se]
            effect = _hedges_g(a, b)
        else:
            summaries = list(data["group_summaries"].values())
            g1, g2 = summaries[0], summaries[1]
            m1, m2 = float(g1["mean"]), float(g2["mean"])
            sd1, sd2 = float(g1["sd"]), float(g2["sd"])
            n1, n2 = int(g1["n"]), int(g2["n"])
            if min(n1, n2) < 2 or min(sd1, sd2) < 0:
                raise ValueError("invalid summary statistics")
            se2 = sd1**2 / n1 + sd2**2 / n2
            if se2 <= 0:
                raise ValueError("standard error is zero")
            se = math.sqrt(se2)
            statistic = (m1 - m2) / se
            denom = ((sd1**2 / n1) ** 2 / (n1 - 1)) + ((sd2**2 / n2) ** 2 / (n2 - 1))
            df = float(se2**2 / denom)
            p = float(2 * stats.t.sf(abs(statistic), df))
            mean_diff = m1 - m2
            critical = float(stats.t.ppf(0.975, df))
            ci = [mean_diff - critical * se, mean_diff + critical * se]
            pooled = math.sqrt(((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2))
            effect = float((mean_diff / pooled) * (1 - 3 / (4 * (n1 + n2) - 9))) if pooled else 0.0

        return ExperimentResult(
            hypothesis_id=plan.hypothesis_id,
            test_used="Welch two-sample t-test",
            status="completed",
            statistic=statistic,
            p_value=p,
            effect_size=effect,
            confidence_interval=[float(x) for x in ci] if ci else None,
            estimate=mean_diff,
            degrees_of_freedom=df,
            conclusion="Statistically significant at α=0.05." if p < 0.05 else "Not statistically significant at α=0.05.",
            method_notes="Two-sided Welch t-test; effect size is Hedges' g.",
            evidence_chunk_ids=plan.evidence_chunk_ids,
        )

    def _anova(self, plan: ExperimentPlan) -> ExperimentResult:
        groups = [np.asarray(v, dtype=float) for v in plan.input_data["groups"].values()]
        if len(groups) < 3 or any(len(group) < 2 for group in groups):
            raise ValueError("ANOVA requires at least three groups with two observations each")
        f_stat, p = stats.f_oneway(*groups)
        all_values = np.concatenate(groups)
        grand_mean = float(np.mean(all_values))
        ss_between = sum(len(group) * (float(np.mean(group)) - grand_mean) ** 2 for group in groups)
        ss_total = float(np.sum((all_values - grand_mean) ** 2))
        eta2 = float(ss_between / ss_total) if ss_total else 0.0
        df = [float(len(groups) - 1), float(len(all_values) - len(groups))]
        return ExperimentResult(
            hypothesis_id=plan.hypothesis_id,
            test_used="One-way ANOVA",
            status="completed",
            statistic=float(f_stat),
            p_value=float(p),
            effect_size=eta2,
            degrees_of_freedom=df,
            conclusion="At least one group mean differs at α=0.05." if p < 0.05 else "No significant group-mean difference at α=0.05.",
            method_notes="One-way independent-groups ANOVA; effect size is η².",
            evidence_chunk_ids=plan.evidence_chunk_ids,
        )

    def _chi_square(self, plan: ExperimentPlan) -> ExperimentResult:
        table = np.asarray(plan.input_data["table"], dtype=float)
        if table.ndim != 2 or min(table.shape) < 2 or np.any(table < 0):
            raise ValueError("chi-square requires a non-negative 2x2-or-larger contingency table")
        chi2, p, dof, expected = stats.chi2_contingency(table)
        flags: list[str] = []
        if np.any(expected < 5):
            flags.append("low_expected_cell_count")
        return ExperimentResult(
            hypothesis_id=plan.hypothesis_id,
            test_used="Chi-square test of independence",
            status="completed",
            statistic=float(chi2),
            p_value=float(p),
            effect_size=_cramers_v(table, float(chi2)),
            degrees_of_freedom=float(dof),
            conclusion="Variables are associated at α=0.05." if p < 0.05 else "No significant association at α=0.05.",
            quality_flags=flags,
            method_notes="Pearson chi-square; effect size is Cramér's V.",
            evidence_chunk_ids=plan.evidence_chunk_ids,
        )

    def _regression(self, plan: ExperimentPlan) -> ExperimentResult:
        x = np.asarray(plan.input_data["x"], dtype=float)
        y = np.asarray(plan.input_data["y"], dtype=float)
        if len(x) != len(y) or len(x) < 3:
            raise ValueError("linear regression requires at least three paired observations")
        result = stats.linregress(x, y)
        return ExperimentResult(
            hypothesis_id=plan.hypothesis_id,
            test_used="Simple linear regression",
            status="completed",
            statistic=float(result.slope),
            p_value=float(result.pvalue),
            effect_size=float(result.rvalue**2),
            confidence_interval=[float(result.slope - 1.96 * result.stderr), float(result.slope + 1.96 * result.stderr)] if result.stderr is not None else None,
            estimate=float(result.slope),
            degrees_of_freedom=float(len(x) - 2),
            conclusion="Slope differs from zero at α=0.05." if result.pvalue < 0.05 else "Slope is not significant at α=0.05.",
            method_notes="Simple least-squares regression; effect size is R².",
            evidence_chunk_ids=plan.evidence_chunk_ids,
        )
