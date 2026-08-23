import math

from app.domain.schemas import ExperimentPlan
from app.services.statistics import StatisticalToolbox


def test_welch_ttest_returns_bounded_p_value_and_effect_size():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="welch_ttest",
        rationale="two groups",
        input_data={"groups": {"A": [1, 2, 3, 4, 5], "B": [8, 9, 10, 11, 12]}},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "completed"
    assert 0 <= result.p_value <= 1
    assert result.p_value < 0.05
    assert result.effect_size is not None
    assert result.confidence_interval and len(result.confidence_interval) == 2


def test_anova_known_separation_is_significant():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="anova",
        rationale="three groups",
        input_data={"groups": {"A": [1, 2, 1.5], "B": [5, 6, 5.5], "C": [10, 11, 10.5]}},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "completed"
    assert result.p_value < 0.05
    assert 0 <= result.effect_size <= 1


def test_chi_square_flags_sparse_expected_cells():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="chi_square",
        rationale="counts",
        input_data={"table": [[1, 0], [0, 1]], "groups": ["A", "B"], "categories": ["yes", "no"]},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "completed"
    assert "low_expected_cell_count" in result.quality_flags


def test_descriptive_plan_never_fabricates_inferential_statistics():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="descriptive",
        rationale="insufficient",
        input_data={},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "insufficient_data"
    assert result.p_value is None
    assert result.effect_size is None


def test_welch_summary_statistics_branch():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="welch_ttest",
        rationale="summary",
        input_data={"group_summaries": {"A": {"mean": 4, "sd": 1, "n": 30}, "B": {"mean": 6, "sd": 1, "n": 30}}},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "completed"
    assert result.p_value < 0.05
    assert result.degrees_of_freedom is not None


def test_linear_regression_recovers_positive_slope():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="linear_regression",
        rationale="paired",
        input_data={"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "completed"
    assert math.isclose(result.estimate, 2.0, rel_tol=1e-7)
    assert math.isclose(result.effect_size, 1.0, rel_tol=1e-7)


def test_invalid_anova_is_converted_to_failed_result():
    result = StatisticalToolbox().execute(ExperimentPlan(
        hypothesis_id="h1",
        test="anova",
        rationale="bad",
        input_data={"groups": {"A": [1], "B": [2], "C": [3]}},
        evidence_chunk_ids=["c1"],
    ))
    assert result.status == "failed"
    assert "invalid_statistical_input" in result.quality_flags
