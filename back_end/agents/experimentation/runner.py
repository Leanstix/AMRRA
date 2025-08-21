import numpy as np
from .models import TwoSampleInput, ExperimentOutput
from .stats import (
    ttest_from_raw, ttest_from_summary, chi2_from_contingency,
    simulate_from_summary, plot_groups, chi2_from_observed_expected
)
from .stats_extended import (
    anova_from_raw, linear_regression, logistic_regression,
    cramers_v, calibrate_confidence
)

try:
    from .explain import gpt5_explain_results
except ImportError:
    def gpt5_explain_results(_):
        return "AI module not available (no API key)."

def run_experiment(input_data: TwoSampleInput, with_ai: bool = False) -> ExperimentOutput:
    """
    Main experiment dispatcher.
    Ensures ExperimentOutput format compliance.
    """
    data = input_data
    quality_flags = []
    res = {}
    plots = []

    # ---------- Chi-square ----------
    if data.test == "chi2":
        if data.contingency:
            res = chi2_from_contingency(data.contingency, data.alpha)
            res["effect_size"] = cramers_v(data.contingency)
            res["test_used"] = "chi2"
            quality_flags.append("chi2_with_cramers_v")
        elif data.groups_raw or (data.data and data.expected):
            # Handle goodness-of-fit chi-square
            res = chi2_from_observed_expected(data.data, data.expected, data.alpha)
            res["test_used"] = "chi2_gof"

    # ---------- ANOVA ----------
    elif data.test == "anova" and data.groups_raw:
        groups = [np.array(g.values, dtype=float) for g in data.groups_raw]
        res = anova_from_raw(groups, data.alpha)
        res["test_used"] = "anova"

    # ---------- Linear regression ----------
    elif data.test == "regression" and data.groups_raw and len(data.groups_raw) >= 2:
        Y = np.array(data.groups_raw[-1].values, dtype=float)
        X = np.array([g.values for g in data.groups_raw[:-1]], dtype=float).T
        res = linear_regression(Y, X, data.alpha)
        res["test_used"] = "regression"

    # ---------- Logistic regression ----------
    elif data.test == "logistic" and data.groups_raw and len(data.groups_raw) >= 2:
        Y = np.array(data.groups_raw[-1].values, dtype=int)
        X = np.array([g.values for g in data.groups_raw[:-1]], dtype=float).T
        res = logistic_regression(Y, X, data.alpha)
        res["test_used"] = "logistic"

    # ---------- Two-sample mean comparisons ----------
    elif data.groups_raw and len(data.groups_raw) == 2:
        g1 = np.array(data.groups_raw[0].values, dtype=float)
        g2 = np.array(data.groups_raw[1].values, dtype=float)
        res = ttest_from_raw(g1, g2, alpha=data.alpha)
        res["test_used"] = "t-test"
        plots.append(plot_groups(g1, g2))

    elif data.groups_summary and len(data.groups_summary) == 2:
        gs1, gs2 = data.groups_summary
        res = ttest_from_summary(
            gs1.mean, gs1.sd, gs1.n,
            gs2.mean, gs2.sd, gs2.n,
            data.alpha,
        )
        res["test_used"] = "t-test"
        if data.allow_simulation and all(v.n >= 10 for v in [gs1, gs2]) and gs1.sd > 0 and gs2.sd > 0:
            sim1 = simulate_from_summary(gs1.mean, gs1.sd, gs1.n)
            sim2 = simulate_from_summary(gs2.mean, gs2.sd, gs2.n)
            plots.append(plot_groups(sim1, sim2))
            quality_flags.append("Simulated-from-summary (bootstrap CI)")

    # ---------- Fallback ----------
    else:
        return ExperimentOutput(
            hypothesis=data.hypothesis,
            variables=data.variables,
            evidence=data.evidence,
            test_used="none",
            conclusion="Insufficient data to run a sound statistical test.",
            quality_flags=["insufficient_data"]
        )

    # ---------- Confidence calibration ----------
    res["confidence_interval"] = res.get("confidence_interval") or None
    res["conclusion"] = res.get("conclusion") or "No conclusion drawn."
    res["confidence_score"] = calibrate_confidence(
        p_value=res.get("p_value"),
        effect_size=res.get("effect_size"),
        n=sum(len(g.values) for g in data.groups_raw) if data.groups_raw else None,
        quality_flags=quality_flags
    )

    # ---------- Optional GPT-5 Explanation ----------
    if with_ai:
        ai_note = gpt5_explain_results(res)
        res["method_notes"] = (res.get("method_notes") or "") + f"\nAI interpretation: {ai_note}"

    return ExperimentOutput(
        hypothesis=data.hypothesis,
        variables=data.variables,
        evidence=data.evidence,
        plots=plots or None,
        quality_flags=quality_flags,
        **res
    )
