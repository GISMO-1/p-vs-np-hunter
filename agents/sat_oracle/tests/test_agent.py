from __future__ import annotations

import math
from pathlib import Path

from agents.sat_oracle.agent import SATInstance, SATOracleAgent


def test_php_unsat() -> None:
    agent = SATOracleAgent()
    inst = agent.generate("php", 3, n=3)
    result = agent.dpll.solve(inst)
    assert result.result == "UNSAT"


def test_ratio_2_mostly_sat() -> None:
    agent = SATOracleAgent()
    sat = 0
    for _ in range(8):
        inst = agent.generate("3sat", 15, ratio=2.0)
        sat += agent.dpll.solve(inst).result == "SAT"
    assert sat >= 6


def test_ratio_10_mostly_unsat() -> None:
    agent = SATOracleAgent()
    unsat = 0
    for _ in range(8):
        inst = agent.generate("3sat", 12, ratio=10.0)
        unsat += agent.dpll.solve(inst).result == "UNSAT"
    assert unsat >= 6


def test_tseitin_k4_unsat() -> None:
    agent = SATOracleAgent()
    inst = agent.generate("tseitin_k4", 0)
    assert agent.dpll.solve(inst).result == "UNSAT"


def test_fingerprint_dimension_and_finite() -> None:
    agent = SATOracleAgent()
    inst = agent.generate("planted", 10, ratio=4.0, backbone=0.6)
    fp = agent.fingerprint(inst)
    assert len(fp.values) == 8
    assert all(math.isfinite(x) for x in fp.values)


def test_serialization_roundtrip(tmp_path: Path) -> None:
    inst = SATInstance("3sat", 3, [(1, -2, 3), (2,)], {"x": 1})
    cnf, meta = inst.save(tmp_path)
    loaded = SATInstance.from_files(cnf, meta)
    assert loaded.num_vars == inst.num_vars
    assert loaded.clauses == inst.clauses
