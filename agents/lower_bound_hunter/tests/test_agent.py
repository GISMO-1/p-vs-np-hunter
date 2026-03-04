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
    cfg.write_text(
        "lower_bound_db_dir: " + str(tmp_path / "db") + "\n", encoding="utf-8"
    )
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


def test_polynomial_method_marks_candidate_result() -> None:
    agent = LowerBoundHunterAgent()
    result = agent.hunt(
        CircuitModel(CircuitClass.ACC0, 32, 4),
        "majority",
        technique="polynomial_method",
    )
    assert result.method == "polynomial_method"
    assert result.known_result is False
    assert "deg_1/3" in result.bound_value


def test_degree_table_generation_and_save(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "lower_bound_db_dir: " + str(tmp_path / "db") + "\n", encoding="utf-8"
    )
    agent = LowerBoundHunterAgent(config_path=cfg)
    out = agent.save_polynomial_degree_table(
        tmp_path / "polynomial_degree_table.json", max_n=10
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert set(payload) == {"table", "growth_fits", "growth_models"}
    assert "majority" in payload["table"]
    assert payload["table"]["majority"]["10"]["GF2"] >= 0


def test_graph_encoding_independent_set_not_flat() -> None:
    agent = LowerBoundHunterAgent()
    table = agent.degree_estimator.build_degree_table(max_n=15)
    indep = {int(k): v for k, v in table["independent_set"].items()}
    assert sorted(indep) == [3, 6, 10, 15]
    gf2_vals = [indep[n]["GF2"] for n in sorted(indep)]
    gf3_vals = [indep[n]["GF3"] for n in sorted(indep)]
    assert gf2_vals[-1] >= gf2_vals[0]
    assert gf3_vals[-1] >= gf3_vals[0]


def test_php_asymmetry_extends_to_n15() -> None:
    agent = LowerBoundHunterAgent()
    table = agent.degree_estimator.build_degree_table(max_n=15)
    php = {int(k): v for k, v in table["php"].items()}
    assert 15 in php
    assert php[15]["GF3"] > php[15]["GF2"]
