from __future__ import annotations

from scripts.run_agents import run_loop


def test_run_loop_rotates_targets_techniques_and_context() -> None:
    summary = run_loop("lower_bound_hunt", "AC0", 5)
    rounds = summary["rounds"]
    assert isinstance(rounds, list)
    assert len(rounds) == 5
    functions = [r["target_function"] for r in rounds]
    techniques = [r["technique"] for r in rounds]
    assert len(set(functions)) == 5
    assert len(set(techniques)) >= 4
    assert rounds[1]["previous_round_context"]


def test_run_loop_session_score_non_zero() -> None:
    summary = run_loop("lower_bound_hunt", "AC0", 2)
    score = summary["session_score"]
    assert isinstance(score, float)
    assert score != 0.0
