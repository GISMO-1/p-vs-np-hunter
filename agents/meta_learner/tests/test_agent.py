from __future__ import annotations

from agents.meta_learner.agent import (
    BarrierClassifier,
    MetaLearnerAgent,
    RewardCalculator,
    StrategyRecommender,
)


def test_barrier_classifier_natural_proofs() -> None:
    cls = BarrierClassifier()
    barrier = cls.classify({"note": "This natural proof approach fails by largeness."})
    assert barrier == "natural_proofs"


def test_strategy_avoids_zero_success_technique() -> None:
    rec = StrategyRecommender().recommend(
        "AC0",
        "parity",
        [
            {
                "circuit_class": "AC0",
                "technique": "bad",
                "status": "failed",
                "lean_verified": False,
            },
            {
                "circuit_class": "AC0",
                "technique": "good",
                "status": "verified",
                "lean_verified": True,
            },
        ],
    )
    assert rec.technique == "good"


def test_reward_cases() -> None:
    calc = RewardCalculator()
    seen: set[str] = set()
    assert calc.score({"type": "lower_bound", "known_result": False}, seen) == 3.0
    assert calc.score({"type": "lower_bound", "known_result": True}, seen) == 1.0
    assert (
        calc.score({"type": "conjecture", "status": "active", "id": "c1"}, seen) == 5.0
    )
    assert (
        calc.score({"type": "conjecture", "status": "active", "id": "c1"}, seen) == -0.5
    )


def test_progress_report_empty_and_populated() -> None:
    agent = MetaLearnerAgent()
    empty = agent.get_progress_report()
    assert "total_proof_attempts" in empty
    _ = agent.ingest_failure(
        {
            "source_agent": "x",
            "technique": "gate_elimination",
            "failure_mode": "incomplete lemma",
            "status": "failed",
        }
    )
    populated = agent.get_progress_report()
    assert populated["total_proof_attempts"] >= 0


def test_ingest_lower_bound_result_populates_tracking_fields() -> None:
    agent = MetaLearnerAgent()
    _ = agent.ingest_failure(
        {
            "session_id": "s-meta",
            "type": "lower_bound",
            "lower_bound_result": {
                "circuit_class": "AC0",
                "method": "random_restriction",
                "known_result": True,
            },
        }
    )
    report = agent.get_progress_report()
    assert "AC0" in report["techniques_tried_per_circuit_class"]
    assert "random_restriction" in report["techniques_tried_per_circuit_class"]["AC0"]
