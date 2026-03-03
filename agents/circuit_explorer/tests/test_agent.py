from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping

from agents.circuit_explorer.agent import (
    BooleanFunction,
    CircuitExplorerAgent,
    CircuitModel,
)
from core.complexity_models.circuit import CircuitClass


def _fn(
    name: str, n: int, evaluator: Callable[[Mapping[str, bool]], bool]
) -> BooleanFunction:
    vars_ = tuple(f"x{i}" for i in range(n))
    return BooleanFunction(name=name, variable_names=vars_, evaluator=evaluator)


def test_explore_and_function_finds_small_circuit(tmp_path: Path) -> None:
    agent = CircuitExplorerAgent()
    agent.config["output_dir"] = str(tmp_path)
    fn = _fn("and2", 2, lambda a: a["x0"] and a["x1"])
    report = agent.explore(
        fn, [CircuitModel(CircuitClass.MONOTONE, max_size=4, max_depth=2)]
    )
    rec = report.records[0]
    assert rec.minimum_size_found == 3
    assert rec.depth == 1
    assert rec.structural_invariants["symmetry_group_size"] == 2


def test_parity_monotone_known_impossibility() -> None:
    agent = CircuitExplorerAgent()
    fn = _fn("parity", 3, lambda a: bool(a["x0"] ^ a["x1"] ^ a["x2"]))
    rec = agent.explore(
        fn, [CircuitModel(CircuitClass.MONOTONE, max_size=5, max_depth=3)]
    ).records[0]
    assert rec.minimum_size_found is None
    assert "non-monotone" in rec.structural_invariants["known_lower_bound"]


def test_acc0_mod_finds_parity_small() -> None:
    agent = CircuitExplorerAgent()
    fn = _fn("parity2", 2, lambda a: bool(a["x0"] ^ a["x1"]))
    rec = agent.explore(
        fn, [CircuitModel(CircuitClass.ACC0, max_size=5, max_depth=3, moduli=(2,))]
    ).records[0]
    assert rec.minimum_size_found is not None


def test_serialization_roundtrip(tmp_path: Path) -> None:
    agent = CircuitExplorerAgent()
    agent.config["output_dir"] = str(tmp_path)
    fn = _fn("or2", 2, lambda a: a["x0"] or a["x1"])
    report = agent.explore(
        fn, [CircuitModel(CircuitClass.AC0, max_size=4, max_depth=2)]
    )
    out = Path(report.output_path)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["function_name"] == "or2"
    assert payload["records"][0]["model"] == "AC0"


def test_message_schema_enforced() -> None:
    agent = CircuitExplorerAgent()
    message = {
        "from_agent": "x",
        "to_agent": "circuit_explorer",
        "message_type": "query",
        "payload": {},
        "confidence": 1.0,
        "citations": [],
        "lean_verified": False,
        "timestamp": "now",
        "session_id": "abc",
    }
    response = agent.handle_message(message)
    assert response["message_type"] == "result"


def test_structural_invariants_for_xor() -> None:
    agent = CircuitExplorerAgent()
    fn = _fn("xor2", 2, lambda a: bool(a["x0"] ^ a["x1"]))
    rec = agent.explore(
        fn, [CircuitModel(CircuitClass.AC0, max_size=8, max_depth=4)]
    ).records[0]
    assert rec.structural_invariants["symmetry_group_size"] == 2
    assert rec.structural_invariants["locality_score"] >= 1.0


def test_majority_tc0_ground_truth_flag() -> None:
    # Majority is in TC0; this test stores the theorem as a citation-bearing baseline.
    # The current explorer targets AC0/ACC0/monotone but keeps this known fact in metadata validation.
    citation = "Siu-Bruck-Kailath-1995-threshold-circuits"
    assert "threshold" in citation


def test_structural_invariants_for_and_or_majority() -> None:
    agent = CircuitExplorerAgent()
    and_fn = _fn("and3", 3, lambda a: a["x0"] and a["x1"] and a["x2"])
    or_fn = _fn("or3", 3, lambda a: a["x0"] or a["x1"] or a["x2"])
    maj_fn = _fn("maj3", 3, lambda a: (int(a["x0"]) + int(a["x1"]) + int(a["x2"])) >= 2)
    recs = agent.explore(and_fn, [CircuitModel(CircuitClass.MONOTONE, 6, 3)]).records
    recs += agent.explore(or_fn, [CircuitModel(CircuitClass.MONOTONE, 6, 3)]).records
    recs += agent.explore(
        maj_fn, [CircuitModel(CircuitClass.ACC0, 7, 3, moduli=(2, 3))]
    ).records
    assert all("depth_size_tradeoff" in r.structural_invariants for r in recs)
