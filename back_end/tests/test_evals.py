import pytest

from evals.runner import run_evals


@pytest.mark.asyncio
async def test_offline_agent_evaluation_suite_is_perfect_on_gold_cases():
    report = await run_evals(live=False)
    assert report["mode"] == "offline"
    assert report["metrics"]["completion_rate"] == 1.0
    assert report["metrics"]["schema_valid_rate"] == 1.0
    assert report["metrics"]["citation_grounding_rate"] == 1.0
    assert report["metrics"]["tool_selection_accuracy"] == 1.0
    assert report["metrics"]["significance_accuracy"] == 1.0
