# agents/experimentation/stats.py
import math
from .models import GroupSummary
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from .explain import gpt5_explain_results

# ---------- Utilities ----------
def _cohens_d_ind(mean1, mean2, sd1, sd2, n1, n2, with_ai=False):
    # Hedges' g (small-sample bias corrected)
    s_pooled = math.sqrt(((n1-1)*sd1**2 + (n2-1)*sd2**2) / (n1 + n2 - 2))
    d = (mean1 - mean2) / s_pooled if s_pooled > 0 else float("nan")
    # small sample correction
    J = 1 - (3/(4*(n1+n2)-9))
    return d*J


def _welch_df(sd1, sd2, n1, n2, with_ai=False):
    num = (sd1**2/n1 + sd2**2/n2)**2
    den = ((sd1**2/n1)**2/(n1-1)) + ((sd2**2/n2)**2/(n2-1))
    return num/den

def _ci_mean_diff_welch(mean1, mean2, sd1, sd2, n1, n2, alpha, with_ai=False):
    df = _welch_df(sd1, sd2, n1, n2)
    se = math.sqrt(sd1**2/n1 + sd2**2/n2)
    tcrit = stats.t.ppf(1 - alpha/2, df)
    diff = mean1 - mean2
    return [diff - tcrit*se, diff + tcrit*se], df, diff

# ---------- Case A: Raw data ----------
def ttest_from_raw(group1: np.ndarray, group2: np.ndarray, alpha=0.05, with_ai=False):
    # Welch by default (safer when variances differ)
    t, p = stats.ttest_ind(group1, group2, equal_var=False)
    m1, m2 = float(np.mean(group1)), float(np.mean(group2))
    s1, s2 = float(np.std(group1, ddof=1)), float(np.std(group2, ddof=1))
    n1, n2 = len(group1), len(group2)
    ci, df, diff = _ci_mean_diff_welch(m1, m2, s1, s2, n1, n2, alpha)
    d = _cohens_d_ind(m1, m2, s1, s2, n1, n2)
    result = {
        "test_used": "Welch t-test",
        "p_value": float(p),
        "effect_size": float(d),
        "confidence_interval": [float(ci[0]), float(ci[1])],
        "estimate": float(diff),
        "df": float(df),
        "conclusion": "Statistically significant" if p < alpha else "Not significant",
        "method_notes": "Welch t-test on raw data (unequal variances)."
    }
    
    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Case B: Summary stats ----------
def ttest_from_summary(mean1, sd1, n1, mean2, sd2, n2, alpha=0.05, with_ai=False):
    # Welch’s t from summary stats
    se = math.sqrt(sd1**2/n1 + sd2**2/n2)
    if se == 0:
        return {"test_used":"Welch t-test","p_value":None,"effect_size":None,
                "confidence_interval":None,"estimate":mean1-mean2,"df":None,
                "conclusion":"Indeterminate (zero SE)","method_notes":"Invalid SD or n."}
    t_stat = (mean1 - mean2) / se
    df = _welch_df(sd1, sd2, n1, n2)
    # two-sided p
    p = 2*(1 - stats.t.cdf(abs(t_stat), df))
    ci, df2, diff = _ci_mean_diff_welch(mean1, mean2, sd1, sd2, n1, n2, alpha)
    d = _cohens_d_ind(mean1, mean2, sd1, sd2, n1, n2)
    result = {
        "test_used": "Welch t-test (summary)",
        "p_value": float(p),
        "effect_size": float(d),
        "confidence_interval": [float(ci[0]), float(ci[1])],
        "estimate": float(diff),
        "df": float(df),
        "conclusion": "Statistically significant" if p < alpha else "Not significant",
        "method_notes": "Computed from reported means/SD/n (no raw data)."
    }

    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Case C: Chi-square ----------
def chi2_from_contingency(table, alpha=0.05, with_ai=False):
    chi2, p, dof, _ = stats.chi2_contingency(np.array(table))
    result = {
        "test_used": "Chi-square test of independence",
        "p_value": float(p),
        "effect_size": None,  # could add Cramér's V
        "confidence_interval": None,
        "estimate": float(chi2),
        "df": float(dof),
        "conclusion": "Association detected" if p < alpha else "No evidence of association",
        "method_notes": "Chi-square on contingency counts."
    }

    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

def chi2_from_observed_expected(observed, expected, alpha=0.05, with_ai=False):
    chi2, p = stats.chisquare(f_obs=observed, f_exp=expected)
    df = len(observed) - 1
    result = {
        "test_used": "Chi-square goodness-of-fit",
        "p_value": float(p),
        "effect_size": None,
        "confidence_interval": None,
        "estimate": float(chi2),
        "df": float(df),
        "conclusion": "Significant difference" if p < alpha else "No significant difference",
        "method_notes": "Chi-square goodness-of-fit test."
    }

    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Simulation (when defensible) ----------
def simulate_from_summary(mean, sd, n, seed=123, with_ai=False):
    rng = np.random.default_rng(seed)
    result = rng.normal(loc=mean, scale=sd, size=n)

    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

def ttest_via_simulation(g1, g2, alpha=0.05, with_ai=False):
    # bootstrap CI of mean diff for transparency
    rng = np.random.default_rng(7)
    t, p = stats.ttest_ind(g1, g2, equal_var=False)
    diffs = []
    B = 2000
    for _ in range(B):
        s1 = rng.choice(g1, size=len(g1), replace=True)
        s2 = rng.choice(g2, size=len(g2), replace=True)
        diffs.append(np.mean(s1) - np.mean(s2))
    ci = np.percentile(diffs, [2.5, 97.5])
    d = _cohens_d_ind(np.mean(g1), np.mean(g2), np.std(g1, ddof=1), np.std(g2, ddof=1), len(g1), len(g2))
    result = {
        "test_used": "Welch t-test (simulated)",
        "p_value": float(p),
        "effect_size": float(d),
        "confidence_interval": [float(ci[0]), float(ci[1])],
        "estimate": float(np.mean(g1) - np.mean(g2)),
        "df": None,
        "conclusion": "Statistically significant" if p < alpha else "Not significant",
        "method_notes": "Simulated raw samples from reported mean/SD/n; bootstrap CI."
    }

    if with_ai:
        result["gpt5_explanation"] = gpt5_explain_results(result)
    return result

# ---------- Plot helper ----------
def plot_groups(group1, group2, file_path="analysis_plot.png"):
    plt.figure()
    plt.boxplot([group1, group2], labels=["Group A","Group B"])
    plt.title("Group comparison")
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    return file_path

# ---------- Main function to run t-test ----------
def run_ttest(group1, group2, alpha=0.05):
    if not group1 or not group2:
        return {"error": "Both groups must have data."}
    # Case A: Raw data
    if isinstance(group1, np.ndarray) and isinstance(group2, np.ndarray):
        return ttest_from_raw(group1, group2, alpha)
    # Case B: Summary stats
    elif isinstance(group1, GroupSummary) and isinstance(group2, GroupSummary):
        return ttest_from_summary(group1.mean, group1.sd, group1.n,
                                   group2.mean, group2.sd, group2.n, alpha)
    # Case C: Contingency table
    elif isinstance(group1, list) and all(isinstance(row, list) for row in group1):
        return chi2_from_contingency(group1, alpha)
    return {"error": "Invalid group data."}