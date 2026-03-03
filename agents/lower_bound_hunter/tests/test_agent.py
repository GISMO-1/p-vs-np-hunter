from __future__ import annotations

import json
from pathlib import Path

from agents.lower_bound_hunter.agent import CircuitModel, LowerBoundHunterAgent
from core.complexity_models.circuit import CircuitClass


def test_validate_known_results() -> None:
    agent = LowerBoundHunterAgent()
    report = agent.validate_known_results()
    assert report.passed
    assert report.checks["ac0_parity"]
    assert report.checks["monotone_clique"]


def test_williams_pipeline_direction() -> None:
    agent = LowerBoundHunterAgent()
    result = agent.hunt(CircuitModel(CircuitClass.AC0, 16, 3), "parity")
    assert "NEXP not subset" in result.bound_value or "exp(Omega" in result.bound_value


def test_gate_elimination_small_functions() -> None:
    agent = LowerBoundHunterAgent()
    assert agent.gate_elimination.lower_bound_small("and", 4) == 3
    assert agent.gate_elimination.lower_bound_small("or", 4) == 3
    assert agent.gate_elimination.lower_bound_small("xor", 4) == 3


def test_serialization_schema(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("lower_bound_db_dir: " + str(tmp_path / "db") + "\n", encoding="utf-8")
    agent = LowerBoundHunterAgent(config_path=cfg)
    _ = agent.hunt(CircuitModel(CircuitClass.AC0, 16, 3), "parity")
    files = list((tmp_path / "db").glob("*.json"))
    assert files
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert set(payload) == {
        "function",
        "circuit_class",
        "bound_type",
        "bound_value",
        "method",
        "known_result",
        "proof_sketch",
        "confidence",
        "citations",
        "lean_ready",
    }
