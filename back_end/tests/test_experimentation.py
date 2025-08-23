from back_end.agents.experimentation.runner import run_experiment

def test_summary_ttest():
    payload = {
        "hypothesis": "A > B",
        "test": "ttest",
        "groups_summary": [
            {"name": "A", "mean": 5.2, "sd": 1.1, "n": 50},
            {"name": "B", "mean": 4.6, "sd": 1.3, "n": 50}
        ],
        "alpha": 0.05,
        "allow_simulation": True,
        "variables": ["A", "B", "mean recovery rate"],
        "evidence": ["chunk1_text", "chunk2_text"]
    }

    out = run_experiment(payload)

    # Extended format checks
    assert "hypothesis" in out
    assert "variables" in out
    assert "evidence" in out

    # Statistical results checks
    assert out["test_used"].startswith("Welch t-test")
    assert 0 <= (out["p_value"] or 0) <= 1
    assert out["confidence_interval"] and len(out["confidence_interval"]) == 2
    assert isinstance(out["conclusion"], str)


def test_insufficient_data():
    payload = {
        "hypothesis": "A > B",
        "test": "ttest",
        "groups_summary": [{"name": "A", "mean": 5, "sd": 0, "n": 10}],
        "variables": ["A"],
        "evidence": ["chunk1_text"]
    }

    out = run_experiment(payload)

    # Extended format still expected
    assert "hypothesis" in out
    assert "variables" in out
    assert "evidence" in out

    # When insufficient data
    assert out["test_used"] == "none"
    assert "insufficient_data" in out.get("quality_flags", [])
