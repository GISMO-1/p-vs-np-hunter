from __future__ import annotations

import random
import time
from typing import cast

from agents.sat_oracle.agent import DPLLSolver, SATInstance
from core.reduction_engine.reductions import (
    ReductionChain,
    sat_to_3sat,
    solve_clique,
    solve_hamiltonian,
    solve_independent_set,
    solve_three_coloring,
    solve_vertex_cover,
    three_sat_to_clique,
    three_sat_to_hamiltonian_circuit,
    three_sat_to_independent_set,
    three_sat_to_three_coloring,
    three_sat_to_vertex_cover,
    verify_clique,
    verify_hamiltonian,
    verify_independent_set,
    verify_three_coloring,
    verify_vertex_cover,
)


def random_3sat(n: int, m: int, seed: int) -> SATInstance:
    rng = random.Random(seed)
    clauses = []
    for _ in range(m):
        vars_ = rng.sample(range(1, n + 1), 3)
        clauses.append(tuple(v if rng.random() < 0.5 else -v for v in vars_))
    return SATInstance("3sat", n, clauses, {})


def test_reductions_random_50_instances() -> None:
    solver = DPLLSolver()
    for i in range(50):
        inst = random_3sat(5, 8, i)
        sat = solver.solve(inst).result == "SAT"

        csol = solve_clique(three_sat_to_clique(inst))
        assert (csol is not None) == sat
        if csol is not None:
            assert verify_clique(inst, csol)

        isol = solve_independent_set(three_sat_to_independent_set(inst))
        assert (isol is not None) == sat
        if isol is not None:
            assert verify_independent_set(inst, isol)

        vsol = solve_vertex_cover(three_sat_to_vertex_cover(inst))
        assert (vsol is not None) == sat
        if vsol is not None:
            assert verify_vertex_cover(inst, vsol)


def test_three_coloring_and_hamiltonian_basic() -> None:
    inst = random_3sat(3, 4, 123)
    col = solve_three_coloring(three_sat_to_three_coloring(inst))
    if col is not None:
        assert verify_three_coloring(inst, col)
    ham = solve_hamiltonian(three_sat_to_hamiltonian_circuit(inst))
    if ham is not None:
        assert verify_hamiltonian(inst, ham)


def test_runtime_polynomial_reduction_only() -> None:
    inst = random_3sat(100, 300, 7)
    start = time.perf_counter()
    _ = three_sat_to_clique(inst)
    _ = three_sat_to_independent_set(inst)
    _ = three_sat_to_vertex_cover(inst)
    _ = three_sat_to_three_coloring(inst)
    _ = three_sat_to_hamiltonian_circuit(inst)
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0


def test_reduction_chain_roundtrip() -> None:
    sat = SATInstance("sat", 4, [(1, 2, 3, 4), (-1, 2), (-2, 3)], {})
    chain = ReductionChain([sat_to_3sat, three_sat_to_clique])
    out = cast(object, chain.run(sat))
    assert hasattr(out, "k")
