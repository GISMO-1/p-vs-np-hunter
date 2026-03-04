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
from typing import Any

from agents.circuit_explorer.agent import BooleanFunction, CircuitExplorerAgent
from agents.circuit_explorer.agent import CircuitModel as ExplorerCircuitModel
from agents.conjecture_engine.agent import ConjectureEngineAgent
from agents.lean_formalizer.agent import LeanFormalizerAgent
from agents.lower_bound_hunter.agent import CircuitModel as HunterCircuitModel
from agents.lower_bound_hunter.agent import LowerBoundHunterAgent
from agents.meta_learner.agent import MetaLearnerAgent
from agents.sat_oracle.agent import SATOracleAgent
from core.complexity_models.circuit import CircuitClass

TARGET_FUNCTIONS = ["parity", "majority", "clique", "independent_set", "php", "xor"]
TECHNIQUES = [
    "williams_pipeline",
    "gate_elimination",
    "random_restriction",
    "monotone_lower_bound",
]


def _target_boolean_function(name: str) -> BooleanFunction:
    variable_names = ("x0", "x1", "x2")
    if name == "parity":
        evaluator = lambda a: bool(a["x0"] ^ a["x1"] ^ a["x2"])
    elif name == "majority":
        evaluator = lambda a: (int(a["x0"]) + int(a["x1"]) + int(a["x2"])) >= 2
    elif name == "clique":
        evaluator = lambda a: bool(a["x0"] and a["x1"] and a["x2"])
    elif name == "independent_set":
        evaluator = lambda a: bool((not a["x0"]) or (not a["x1"]) or (not a["x2"]))
    elif name == "php":
        evaluator = lambda a: bool((not a["x0"]) and (not a["x1"]) and (not a["x2"]))
    else:
        evaluator = lambda a: bool(a["x0"] ^ a["x1"])
    return BooleanFunction(
        name=name, variable_names=variable_names, evaluator=evaluator
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

    prior_context: dict[str, Any] = {}
    for round_index in range(rounds):
        target_function = TARGET_FUNCTIONS[round_index % len(TARGET_FUNCTIONS)]
        technique = TECHNIQUES[round_index % len(TECHNIQUES)]

        explore = circuit_explorer.explore(
            _target_boolean_function(target_function),
            [ExplorerCircuitModel(cls, 16, 3)],
        )
        sat_instance = sat_oracle.generate("3sat", 8 + round_index, k=3, ratio=4.0)
        lower = hunter.hunt(
            HunterCircuitModel(cls, 32 + round_index, 4),
            target_function,
            technique=technique,
        )

        conjectures = conjecture_engine.propose(
            {
                "session": session_id,
                "round_index": round_index,
                "target_function": target_function,
                "technique": technique,
                "circuit_class": model,
                "lower_bound_result": asdict(lower),
                "previous_round": prior_context,
            }
        )
        top_conjecture = asdict(conjectures[0]) if conjectures else {}

        translated = formalizer.formalize(asdict(lower))
        verified = formalizer.verify(translated.lean_file_path)
        feedback = formalizer.format_feedback(
            verified, "lower_bound_hunter", session_id
        )

        meta.ingest_failure(
            {
                "session_id": session_id,
                "type": "lower_bound",
                "source_agent": "lower_bound_hunter",
                "lower_bound_result": asdict(lower),
                "status": verified.status,
                "lean_verified": verified.lean_verified,
                "failure_mode": verified.error_message or "none",
                "barrier": "unknown",
            }
        )
        if top_conjecture:
            meta.ingest_failure(
                {
                    "session_id": session_id,
                    "type": "conjecture",
                    "source_agent": "conjecture_engine",
                    "id": top_conjecture.get("id", ""),
                    "status": top_conjecture.get("status", "active"),
                    "circuit_class": model,
                    "technique": technique,
                    "lean_verified": False,
                }
            )

        recommendation = asdict(
            meta.recommend_strategy(
                {"circuit_class": model, "target_function": target_function}
            )
        )
        round_payload = {
            "round": round_index + 1,
            "target_function": target_function,
            "technique": technique,
            "circuit_explorer_output": explore.output_path,
            "sat_instance_type": sat_instance.instance_type,
            "lower_bound": asdict(lower),
            "conjecture": top_conjecture,
            "translation": asdict(translated),
            "verification": asdict(verified),
            "feedback": feedback,
            "strategy_recommendation": recommendation,
            "previous_round_context": prior_context,
        }
        rounds_data.append(round_payload)
        prior_context = {
            "lower_bound": asdict(lower),
            "strategy_recommendation": recommendation,
        }

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
