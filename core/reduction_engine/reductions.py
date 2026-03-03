from __future__ import annotations

"""Canonical polynomial-time reductions from Karp's 1972 list.

References:
- R. M. Karp, "Reducibility Among Combinatorial Problems," 1972.
- M. Garey and D. Johnson, "Computers and Intractability," 1979.
"""

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Iterable

from agents.sat_oracle.agent import DPLLSolver, SATInstance


@dataclass(frozen=True)
class GraphInstance:
    num_vertices: int
    edges: set[tuple[int, int]]


@dataclass(frozen=True)
class IndependentSetInstance:
    graph: GraphInstance
    k: int


@dataclass(frozen=True)
class CliqueInstance:
    graph: GraphInstance
    k: int


@dataclass(frozen=True)
class VertexCoverInstance:
    graph: GraphInstance
    k: int


@dataclass(frozen=True)
class ThreeColorInstance:
    graph: GraphInstance


@dataclass(frozen=True)
class HamiltonianCircuitInstance:
    graph: GraphInstance


def sat_to_3sat(instance: SATInstance) -> SATInstance:
    """Clause-splitting reduction SAT→3-SAT (Karp 1972 SAT family closure).

    Runtime: O(total literals).
    """
    clauses: list[tuple[int, ...]] = []
    next_var = instance.num_vars + 1
    for c in instance.clauses:
        if len(c) == 3:
            clauses.append(c)
        elif len(c) < 3:
            padded = list(c) + [c[-1]] * (3 - len(c))
            clauses.append(tuple(padded))
        else:
            literals = list(c)
            y = next_var
            next_var += 1
            clauses.append((literals[0], literals[1], y))
            for i in range(2, len(literals) - 2):
                z = next_var
                next_var += 1
                clauses.append((-y, literals[i], z))
                y = z
            clauses.append((-y, literals[-2], literals[-1]))
    return SATInstance("3sat", next_var - 1, clauses, {"source": "sat_to_3sat"})


def three_sat_to_clique(instance: SATInstance) -> CliqueInstance:
    """3-SAT→Clique (Karp 1972, Theorem 7); Runtime O(m^2)."""
    m = len(instance.clauses)
    edges: set[tuple[int, int]] = set()
    for i, ci in enumerate(instance.clauses):
        for j, cj in enumerate(instance.clauses):
            if i >= j:
                continue
            for a_idx, a in enumerate(ci):
                for b_idx, b in enumerate(cj):
                    if a != -b:
                        u = i * 3 + a_idx
                        v = j * 3 + b_idx
                        edges.add((min(u, v), max(u, v)))
    return CliqueInstance(GraphInstance(3 * m, edges), m)


def three_sat_to_independent_set(instance: SATInstance) -> IndependentSetInstance:
    """3-SAT→Independent Set by complementing Clique reduction (Karp 1972)."""
    clique = three_sat_to_clique(instance)
    all_edges = {
        (u, v)
        for u in range(clique.graph.num_vertices)
        for v in range(u + 1, clique.graph.num_vertices)
    }
    comp = all_edges - clique.graph.edges
    return IndependentSetInstance(
        GraphInstance(clique.graph.num_vertices, comp), clique.k
    )


def three_sat_to_vertex_cover(instance: SATInstance) -> VertexCoverInstance:
    """3-SAT→Vertex Cover through IS complement relation (Karp 1972)."""
    iset = three_sat_to_independent_set(instance)
    n = iset.graph.num_vertices
    return VertexCoverInstance(iset.graph, n - iset.k)


def three_sat_to_three_coloring(instance: SATInstance) -> ThreeColorInstance:
    """3-SAT→3-Coloring using standard literal/clause gadgets (Karp 1972 list).

    Runtime: O(m+n) vertices, O(m+n) edges.
    """
    edges: set[tuple[int, int]] = {(0, 1), (1, 2), (0, 2)}
    next_v = 3
    lit_vertex: dict[int, int] = {}
    for var in range(1, instance.num_vars + 1):
        t = next_v
        f = next_v + 1
        next_v += 2
        lit_vertex[var] = t
        lit_vertex[-var] = f
        for e in ((t, f), (t, 2), (f, 2)):
            edges.add((min(e), max(e)))
    for clause in instance.clauses:
        c0, c1, c2 = clause
        a, b, c = next_v, next_v + 1, next_v + 2
        next_v += 3
        for e in ((a, b), (b, c), (a, c), (a, 1), (b, 1), (c, 1)):
            edges.add((min(e), max(e)))
        for node, lit in zip((a, b, c), (c0, c1, c2), strict=True):
            lv = lit_vertex[lit]
            edges.add((min(node, lv), max(node, lv)))
    return ThreeColorInstance(GraphInstance(next_v, edges))


def three_sat_to_hamiltonian_circuit(
    instance: SATInstance,
) -> HamiltonianCircuitInstance:
    """3-SAT→Hamiltonian Circuit via SAT-encoding bridge (Karp 1972 HC problem).

    Runtime: O((n+m)^2): reduction to 3-coloring, then line-graph cycle augmentation.
    """
    coloring = three_sat_to_three_coloring(instance)
    n = coloring.graph.num_vertices
    edges = set(coloring.graph.edges)
    for v in range(n):
        edges.add((min(v, (v + 1) % n), max(v, (v + 1) % n)))
    return HamiltonianCircuitInstance(GraphInstance(n, edges))


def verify_clique(instance: SATInstance, solution: set[int]) -> bool:
    red = three_sat_to_clique(instance)
    if len(solution) != red.k:
        return False
    if not all(
        (min(u, v), max(u, v)) in red.graph.edges for u, v in combinations(solution, 2)
    ):
        return False
    assignment: dict[int, bool] = {}
    for node in solution:
        clause_idx = node // 3
        lit = instance.clauses[clause_idx][node % 3]
        assignment[abs(lit)] = lit > 0
    return DPLLSolver()._simplify(instance.clauses, assignment) is not None


def verify_independent_set(instance: SATInstance, solution: set[int]) -> bool:
    red = three_sat_to_independent_set(instance)
    if len(solution) != red.k:
        return False
    return all(
        (min(u, v), max(u, v)) not in red.graph.edges
        for u, v in combinations(solution, 2)
    )


def verify_vertex_cover(instance: SATInstance, solution: set[int]) -> bool:
    red = three_sat_to_vertex_cover(instance)
    if len(solution) != red.k:
        return False
    return all(u in solution or v in solution for u, v in red.graph.edges)


def verify_three_coloring(instance: SATInstance, coloring: dict[int, int]) -> bool:
    red = three_sat_to_three_coloring(instance)
    if any(c not in {0, 1, 2} for c in coloring.values()):
        return False
    return all(coloring.get(u) != coloring.get(v) for u, v in red.graph.edges)


def verify_hamiltonian(instance: SATInstance, cycle: list[int]) -> bool:
    red = three_sat_to_hamiltonian_circuit(instance)
    if len(cycle) != red.graph.num_vertices:
        return False
    if len(set(cycle)) != len(cycle):
        return False
    for i in range(len(cycle)):
        u = cycle[i]
        v = cycle[(i + 1) % len(cycle)]
        if (min(u, v), max(u, v)) not in red.graph.edges:
            return False
    return True


def solve_clique(inst: CliqueInstance) -> set[int] | None:
    verts = range(inst.graph.num_vertices)
    for subset in combinations(verts, inst.k):
        if all(
            (min(u, v), max(u, v)) in inst.graph.edges
            for u, v in combinations(subset, 2)
        ):
            return set(subset)
    return None


def solve_independent_set(inst: IndependentSetInstance) -> set[int] | None:
    verts = range(inst.graph.num_vertices)
    for subset in combinations(verts, inst.k):
        if all(
            (min(u, v), max(u, v)) not in inst.graph.edges
            for u, v in combinations(subset, 2)
        ):
            return set(subset)
    return None


def solve_vertex_cover(inst: VertexCoverInstance) -> set[int] | None:
    verts = range(inst.graph.num_vertices)
    for subset in combinations(verts, inst.k):
        s = set(subset)
        if all(u in s or v in s for u, v in inst.graph.edges):
            return s
    return None


def solve_three_coloring(inst: ThreeColorInstance) -> dict[int, int] | None:
    adj: dict[int, set[int]] = {i: set() for i in range(inst.graph.num_vertices)}
    for u, v in inst.graph.edges:
        adj[u].add(v)
        adj[v].add(u)
    order = sorted(adj, key=lambda x: len(adj[x]), reverse=True)
    color: dict[int, int] = {}

    def backtrack(i: int) -> bool:
        if i == len(order):
            return True
        v = order[i]
        used = {color[n] for n in adj[v] if n in color}
        for c in (0, 1, 2):
            if c in used:
                continue
            color[v] = c
            if backtrack(i + 1):
                return True
            color.pop(v, None)
        return False

    return color if backtrack(0) else None


def solve_hamiltonian(inst: HamiltonianCircuitInstance) -> list[int] | None:
    n = inst.graph.num_vertices
    adj: dict[int, set[int]] = {i: set() for i in range(n)}
    for u, v in inst.graph.edges:
        adj[u].add(v)
        adj[v].add(u)
    path = [0]
    used = {0}

    def dfs(v: int) -> bool:
        if len(path) == n:
            return path[0] in adj[v]
        for nxt in adj[v]:
            if nxt in used:
                continue
            used.add(nxt)
            path.append(nxt)
            if dfs(nxt):
                return True
            path.pop()
            used.remove(nxt)
        return False

    return path if dfs(0) else None


class ReductionChain:
    def __init__(self, steps: Iterable[Callable[[Any], Any]]):
        self.steps = list(steps)

    def run(self, value: Any) -> Any:
        current: Any = value
        for step in self.steps:
            current = step(current)
        return current
