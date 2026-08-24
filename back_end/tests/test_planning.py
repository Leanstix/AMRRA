from app.domain.schemas import Hypothesis, Observation
from app.services.planning import ExperimentPlanner


def hypothesis(observations):
    return Hypothesis(
        hypothesis_id="h1",
        statement="Group A differs from Group B",
        observations=observations,
        evidence_chunk_ids=["c1"],
        confidence=0.9,
    )


def test_plans_ttest_only_from_explicit_groups():
    plan = ExperimentPlanner().plan([
        hypothesis([
            Observation(name="score", role="outcome", value_type="raw_numeric", group="A", values=[1, 2, 3], evidence_chunk_ids=["c1"], confidence=1),
            Observation(name="score", role="outcome", value_type="raw_numeric", group="B", values=[4, 5, 6], evidence_chunk_ids=["c1"], confidence=1),
        ])
    ])[0]
    assert plan.test == "welch_ttest"
    assert plan.input_data["groups"]["A"] == [1.0, 2.0, 3.0]


def test_refuses_inferential_test_when_numbers_are_not_semantically_grouped():
    plan = ExperimentPlanner().plan([
        hypothesis([
            Observation(name="reported number", value_type="raw_numeric", values=[2024, 0.05, 95], evidence_chunk_ids=["c1"], confidence=0.6),
        ])
    ])[0]
    assert plan.test == "descriptive"
    assert "does not satisfy" in plan.rationale


def test_plans_chi_square_from_contingency_counts():
    observations = [
        Observation(name="count", value_type="categorical_count", group="A", category="yes", count=20, evidence_chunk_ids=["c1"], confidence=1),
        Observation(name="count", value_type="categorical_count", group="A", category="no", count=10, evidence_chunk_ids=["c1"], confidence=1),
        Observation(name="count", value_type="categorical_count", group="B", category="yes", count=5, evidence_chunk_ids=["c1"], confidence=1),
        Observation(name="count", value_type="categorical_count", group="B", category="no", count=25, evidence_chunk_ids=["c1"], confidence=1),
    ]
    plan = ExperimentPlanner().plan([hypothesis(observations)])[0]
    assert plan.test == "chi_square"
    assert plan.input_data["table"] == [[10, 20], [25, 5]] or plan.input_data["table"] == [[20, 10], [5, 25]]


def test_plans_ttest_from_summary_statistics():
    plan = ExperimentPlanner().plan([
        hypothesis([
            Observation(name="score", role="outcome", value_type="summary", group="A", mean=5, sd=1.2, n=20, evidence_chunk_ids=["c1"], confidence=1),
            Observation(name="score", role="outcome", value_type="summary", group="B", mean=7, sd=1.1, n=20, evidence_chunk_ids=["c1"], confidence=1),
        ])
    ])[0]
    assert plan.test == "welch_ttest"
    assert plan.input_data["group_summaries"]["A"]["n"] == 20


def test_plans_anova_for_three_explicit_groups():
    plan = ExperimentPlanner().plan([
        hypothesis([
            Observation(name="score", value_type="raw_numeric", group="A", values=[1, 2], evidence_chunk_ids=["c1"], confidence=1),
            Observation(name="score", value_type="raw_numeric", group="B", values=[3, 4], evidence_chunk_ids=["c1"], confidence=1),
            Observation(name="score", value_type="raw_numeric", group="C", values=[5, 6], evidence_chunk_ids=["c1"], confidence=1),
        ])
    ])[0]
    assert plan.test == "anova"


def test_plans_linear_regression_from_paired_predictor_and_outcome():
    plan = ExperimentPlanner().plan([
        hypothesis([
            Observation(name="dose", role="predictor", value_type="raw_numeric", values=[1, 2, 3, 4], evidence_chunk_ids=["c1"], confidence=1),
            Observation(name="outcome", role="outcome", value_type="raw_numeric", values=[2, 4, 6, 8], evidence_chunk_ids=["c1"], confidence=1),
        ])
    ])[0]
    assert plan.test == "linear_regression"
