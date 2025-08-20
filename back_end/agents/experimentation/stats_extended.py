import numpy as np
import math
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from .explain import gpt5_explain_results

# ---------- ANOVA (raw only) ----------
def anova_from_raw(groups: list[np.ndarray], alpha=0.05, with_ai=False):
    f_stat, p = stats.f_oneway(*groups)
    k = len(groups)
    n = sum(len(g) for g in groups)
    df_between, df_within = k-1, n-k
    conclusion = "Group means differ significantly" if p < alpha else "No significant differences"
    result = {
        "test_used": "One-way ANOVA",
        "p_value": float(p),
        "effect_size": None,  # eta^2 or omega^2 could be added
        "confidence_interval": None,
        "estimate": float(f_stat),
        "df": [df_between, df_within],
        "conclusion": conclusion,
        "method_notes": "One-way ANOVA across k groups (raw data)."
    }
    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Regression (linear) ----------
def linear_regression(y: np.ndarray, X: np.ndarray, alpha=0.05, with_ai=False):
    Xc = sm.add_constant(X)
    model = sm.OLS(y, Xc).fit()
    ci = model.conf_int(alpha=alpha).tolist()
    summary = model.summary().as_text()
    result = {
        "test_used": "Linear regression",
        "p_value": float(model.f_pvalue),
        "effect_size": float(model.rsquared),
        "confidence_interval": ci,
        "estimate": model.params.tolist(),
        "df": [int(model.df_model), int(model.df_resid)],
        "conclusion": "Regression significant" if model.f_pvalue < alpha else "Not significant",
        "method_notes": "OLS linear regression",
        "extra": summary
    }
    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Regression (logistic) ----------
def logistic_regression(y: np.ndarray, X: np.ndarray, alpha=0.05, with_ai=False):
    Xc = sm.add_constant(X)
    model = sm.Logit(y, Xc).fit(disp=False)
    ci = model.conf_int(alpha=alpha).tolist()
    summary = model.summary().as_text()
    result = {
        "test_used": "Logistic regression",
        "p_value": float(model.llr_pvalue),
        "effect_size": float(model.prsquared),  # pseudo-R^2
        "confidence_interval": ci,
        "estimate": model.params.tolist(),
        "df": [int(model.df_model), int(model.df_resid)],
        "conclusion": "Regression significant" if model.llr_pvalue < alpha else "Not significant",
        "method_notes": "Logistic regression (binary outcome)",
        "extra": summary
    }
    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Chi-square effect size ----------
def cramers_v(table: list[list[int]], with_ai=False) -> float | dict:
    arr = np.array(table)
    chi2, _, _, _ = stats.chi2_contingency(arr)
    n = arr.sum()
    phi2 = chi2 / n
    r, k = arr.shape
    value = math.sqrt(phi2 / min(k-1, r-1))

    if with_ai:
        return {
            "value": float(value),
            "gpt5_explanation": gpt5_explain_results({
                "test_used": "Chi-square effect size (Cramér's V)",
                "estimate": float(value),
                "method_notes": "Effect size measure for categorical association."
            })
        }
    return value

# ---------- Confidence calibration ----------
def calibrate_confidence(p_value=None, effect_size=None, n=None, quality_flags=None, with_ai=False):
    score = 0.5
    if p_value is not None:
        if p_value < 0.001: score += 0.3
        elif p_value < 0.05: score += 0.2
        else: score -= 0.2
    if effect_size is not None:
        if abs(effect_size) > 0.8: score += 0.2
        elif abs(effect_size) > 0.5: score += 0.1
    if n is not None:
        if n > 200: score += 0.1
        elif n < 30: score -= 0.1
    if quality_flags:
        if "insufficient_data" in quality_flags: score -= 0.3
        if any("simulated" in f.lower() for f in quality_flags): score -= 0.1

    score = max(0.0, min(1.0, score))
    if with_ai:
        return {
            "confidence_score": score,
            "gpt5_explanation": gpt5_explain_results({
                "test_used": "Confidence calibration",
                "estimate": score,
                "method_notes": "Heuristic scoring combining p-value, effect size, sample size, and quality flags."
            })
        }
    return score
