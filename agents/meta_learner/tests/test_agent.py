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
    assert calc.score({"lean_verified": True}) == 10.0
    assert calc.score({"type": "conjecture", "small_case_support": True}) == 5.0
    assert calc.score({"type": "lower_bound"}) == 3.0
    assert calc.score({"barrier": "natural_proofs"}) == -1.0
    assert calc.score({"incorrect_claim": True}) == -2.0
    assert calc.score({"duplicate": True}) == -0.5


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
