from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime

from agents.circuit_explorer.agent import BooleanFunction, CircuitExplorerAgent
from agents.circuit_explorer.agent import CircuitModel as ExplorerCircuitModel
from agents.conjecture_engine.agent import ConjectureEngineAgent
from agents.lean_formalizer.agent import LeanFormalizerAgent
from agents.lower_bound_hunter.agent import CircuitModel as HunterCircuitModel
from agents.lower_bound_hunter.agent import LowerBoundHunterAgent
from agents.meta_learner.agent import MetaLearnerAgent
from agents.sat_oracle.agent import SATOracleAgent
from core.complexity_models.circuit import CircuitClass


def parity_function() -> BooleanFunction:
    return BooleanFunction(
        name="parity",
        variable_names=("x0", "x1", "x2"),
        evaluator=lambda a: bool(a["x0"] ^ a["x1"] ^ a["x2"]),
    )


def run_loop(mission: str, model: str, rounds: int) -> dict[str, object]:
    del mission
    circuit_explorer = CircuitExplorerAgent()
    sat_oracle = SATOracleAgent()
    hunter = LowerBoundHunterAgent()
    conjecture_engine = ConjectureEngineAgent()
    formalizer = LeanFormalizerAgent()
    meta = MetaLearnerAgent()

    cls = CircuitClass(model)
    session_id = f"session-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    rounds_data: list[dict[str, object]] = []
    summary: dict[str, object] = {"session_id": session_id, "rounds": rounds_data}

    for _ in range(rounds):
        explore = circuit_explorer.explore(
            parity_function(), [ExplorerCircuitModel(cls, 16, 3)]
        )
        sat_instance = sat_oracle.generate("3sat", 8, k=3, ratio=4.0)
        lower = hunter.hunt(HunterCircuitModel(cls, 32, 4), "parity")
        conjectures = conjecture_engine.propose({"lower_bound_result": asdict(lower)})
        top_conjecture = asdict(conjectures[0]) if conjectures else {}
        translated = formalizer.formalize(asdict(lower))
        verified = formalizer.verify(translated.lean_file_path)
        feedback = formalizer.format_feedback(
            verified, "lower_bound_hunter", session_id
        )
        meta.ingest_failure(
            {
                "session_id": session_id,
                "source_agent": "lower_bound_hunter",
                "technique": lower.method,
                "status": verified.status,
                "lean_verified": verified.lean_verified,
                "circuit_class": lower.circuit_class,
                "failure_mode": verified.error_message or "none",
                "barrier": "unknown",
            }
        )
        recommendation = asdict(
            meta.recommend_strategy(
                {"circuit_class": model, "target_function": "parity"}
            )
        )
        rounds_data.append(
            {
                "circuit_explorer_output": explore.output_path,
                "sat_instance_type": sat_instance.instance_type,
                "lower_bound": asdict(lower),
                "conjecture": top_conjecture,
                "translation": asdict(translated),
                "verification": asdict(verified),
                "feedback": feedback,
                "strategy_recommendation": recommendation,
            }
        )

    summary["session_score"] = meta.score_session(session_id)
    summary["progress_report"] = meta.get_progress_report()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", default="lower_bound_hunt")
    parser.add_argument("--model", default="AC0")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    summary = run_loop(args.mission, args.model, args.rounds)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
