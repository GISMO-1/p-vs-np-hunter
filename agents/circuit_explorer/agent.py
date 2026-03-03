from __future__ import annotations

"""Circuit Explorer agent for exact small-n circuit complexity cartography.

References:
- J. Håstad, "Almost optimal lower bounds for small depth circuits," STOC 1986.
- A. Razborov, "Lower bounds on monotone complexity of the logical permanent," 1985.
- R. Smolensky, "Algebraic methods in the theory of lower bounds for Boolean circuit complexity," STOC 1987.
- N. Linial, Y. Mansour, N. Nisan, "Constant depth circuits, Fourier transform, and learnability," FOCS 1989 (AC0 structural background).
- M. Siu, J. Bruck, T. Kailath, "On the power of threshold circuits with small weights," SIAM J. Discrete Math. 1995 (majority in TC0 context).
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from itertools import combinations_with_replacement, permutations, product
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence

from core.complexity_models.circuit import CircuitClass
from core.complexity_models.switching_lemma import (
    DNF,
    exact_depth_tail_probability,
    switching_lemma_upper_bound,
)

BitVector = tuple[bool, ...]


@dataclass(frozen=True)
class BooleanFunction:
    name: str
    variable_names: tuple[str, ...]
    evaluator: Callable[[Mapping[str, bool]], bool]

    def arity(self) -> int:
        return len(self.variable_names)

    def truth_table(self) -> dict[BitVector, bool]:
        table: dict[BitVector, bool] = {}
        for bits in product((False, True), repeat=self.arity()):
            assignment = dict(zip(self.variable_names, bits, strict=True))
            table[bits] = self.evaluator(assignment)
        return table


@dataclass(frozen=True)
class CircuitModel:
    cls: CircuitClass
    max_size: int
    max_depth: int
    moduli: tuple[int, ...] = (2,)


@dataclass
class CircuitRecord:
    model: str
    minimum_size_found: int | None
    depth: int | None
    witness_expression: str | None
    switching_lemma_check: dict[str, float] | None
    structural_invariants: dict[str, Any]


@dataclass
class CircuitReport:
    function_name: str
    variable_names: list[str]
    timestamp: str
    truth_table: dict[str, bool] | None
    records: list[CircuitRecord]
    output_path: str


@dataclass(frozen=True)
class _Node:
    table: tuple[bool, ...]
    size: int
    depth: int
    deps: frozenset[int]
    expr: str
    kind: str
    children: tuple[int, ...] = ()


class CircuitExplorerAgent:
    def __init__(self, config_path: str | Path | None = None):
        default_path = Path(__file__).with_name("config.yaml")
        use_path = Path(config_path) if config_path else default_path
        self.config = self._load_config(use_path)

    def _load_config(self, path: Path) -> dict[str, Any]:
        config: dict[str, Any] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = [x.strip() for x in line.split(":", 1)]
            if value.lower() in {"true", "false"}:
                config[key] = value.lower() == "true"
            else:
                try:
                    config[key] = int(value)
                except ValueError:
                    try:
                        config[key] = float(value)
                    except ValueError:
                        config[key] = value
        return config

    def explore(
        self, function: BooleanFunction, models: list[CircuitModel]
    ) -> CircuitReport:
        records: list[CircuitRecord] = []
        target_table = (
            function.truth_table()
            if function.arity() <= self.config["truth_table_limit"]
            else None
        )
        target_vector = self._target_vector(function)
        for model in models:
            record = self._explore_model(function, model, target_vector)
            records.append(record)
        report = CircuitReport(
            function_name=function.name,
            variable_names=list(function.variable_names),
            timestamp=datetime.now(UTC).isoformat(),
            truth_table=(
                {
                    "".join("1" if b else "0" for b in k): v
                    for k, v in target_table.items()
                }
                if target_table
                else None
            ),
            records=records,
            output_path="",
        )
        path = self._write_report(report)
        report.output_path = str(path)
        return report

    def handle_message(self, message: Mapping[str, Any]) -> dict[str, Any]:
        required = {
            "from_agent",
            "to_agent",
            "message_type",
            "payload",
            "confidence",
            "citations",
            "lean_verified",
            "timestamp",
            "session_id",
        }
        missing = sorted(required - set(message))
        if missing:
            raise ValueError(f"Message missing required fields: {missing}")
        return {
            "from_agent": "circuit_explorer",
            "to_agent": message["from_agent"],
            "message_type": "result",
            "payload": {"status": "ok", "echo_type": message["message_type"]},
            "confidence": 1.0,
            "citations": ["STOC-1986-Hastad", "STOC-1987-Smolensky"],
            "lean_verified": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": message["session_id"],
        }

    def _explore_model(
        self,
        function: BooleanFunction,
        model: CircuitModel,
        target_vector: tuple[bool, ...],
    ) -> CircuitRecord:
        if function.name.lower() == "parity" and model.cls == CircuitClass.MONOTONE:
            return CircuitRecord(
                model=model.cls.value,
                minimum_size_found=None,
                depth=None,
                witness_expression=None,
                switching_lemma_check=None,
                structural_invariants={
                    "known_lower_bound": "Parity is non-monotone; no monotone circuit computes it exactly (thus super-polynomial/infinite monotone size).",
                    "citation": "Razborov-1985-monotone-framework",
                },
            )
        if function.arity() <= self.config["exhaustive_variable_limit"]:
            witness, curve = self._enumerate_exhaustive(function, model, target_vector)
        else:
            witness, curve = self._enumerate_pruned(function, model, target_vector)
        invariants = self._compute_invariants(function, witness, curve)
        return CircuitRecord(
            model=model.cls.value,
            minimum_size_found=witness.size if witness else None,
            depth=witness.depth if witness else None,
            witness_expression=witness.expr if witness else None,
            switching_lemma_check=self._switching_cross_check(function, witness),
            structural_invariants=invariants,
        )

    def _target_vector(self, function: BooleanFunction) -> tuple[bool, ...]:
        return tuple(
            function.evaluator(dict(zip(function.variable_names, bits, strict=True)))
            for bits in product((False, True), repeat=function.arity())
        )

    def _enumerate_exhaustive(
        self, function: BooleanFunction, model: CircuitModel, target: tuple[bool, ...]
    ) -> tuple[_Node | None, dict[int, int]]:
        nodes, by_table = self._base_nodes(function)
        curve: dict[int, int] = {}
        found = by_table.get(target)
        if found and found.size <= model.max_size and found.depth <= model.max_depth:
            curve[found.depth] = found.size
            return found, curve
        for current_size in range(2, model.max_size + 1):
            additions = self._expand_nodes(
                nodes, by_table, function, model, current_size
            )
            nodes.extend(additions)
            for node in additions:
                if node.table == target and node.depth <= model.max_depth:
                    curve[node.depth] = min(curve.get(node.depth, 10**9), node.size)
                    if (
                        found is None
                        or node.size < found.size
                        or (node.size == found.size and node.depth < found.depth)
                    ):
                        found = node
        return found, curve

    def _enumerate_pruned(
        self, function: BooleanFunction, model: CircuitModel, target: tuple[bool, ...]
    ) -> tuple[_Node | None, dict[int, int]]:
        nodes, by_table = self._base_nodes(function)
        rng_budget = int(self.config["pruned_candidate_budget"])
        curve: dict[int, int] = {}
        found: _Node | None = by_table.get(target)
        for size in range(2, model.max_size + 1):
            additions = self._expand_nodes(nodes, by_table, function, model, size)
            additions = sorted(additions, key=lambda n: (len(n.deps), n.depth, n.expr))[
                :rng_budget
            ]
            nodes.extend(additions)
            for node in additions:
                if node.table == target:
                    curve[node.depth] = min(curve.get(node.depth, 10**9), node.size)
                    if found is None or node.size < found.size:
                        found = node
        return found, curve

    def _base_nodes(
        self, function: BooleanFunction
    ) -> tuple[list[_Node], dict[tuple[bool, ...], _Node]]:
        n = function.arity()
        nodes: list[_Node] = []
        by_table: dict[tuple[bool, ...], _Node] = {}
        for idx, name in enumerate(function.variable_names):
            vec = tuple(bits[idx] for bits in product((False, True), repeat=n))
            node = _Node(
                table=vec,
                size=1,
                depth=0,
                deps=frozenset({idx}),
                expr=name,
                kind="INPUT",
            )
            nodes.append(node)
            by_table.setdefault(vec, node)
        for value in (False, True):
            vec = tuple(value for _ in range(2**n))
            node = _Node(
                table=vec,
                size=1,
                depth=0,
                deps=frozenset(),
                expr="1" if value else "0",
                kind="CONST",
            )
            nodes.append(node)
            by_table.setdefault(vec, node)
        return nodes, by_table

    def _expand_nodes(
        self,
        nodes: list[_Node],
        by_table: dict[tuple[bool, ...], _Node],
        function: BooleanFunction,
        model: CircuitModel,
        current_size: int,
    ) -> list[_Node]:
        additions: list[_Node] = []
        for a, b in combinations_with_replacement(nodes, 2):
            if a.size + b.size + 1 != current_size:
                continue
            for kind, op in self._binary_ops(model):
                vec = tuple(op(x, y) for x, y in zip(a.table, b.table, strict=True))
                node = _Node(
                    vec,
                    current_size,
                    max(a.depth, b.depth) + 1,
                    a.deps | b.deps,
                    f"{kind}({a.expr},{b.expr})",
                    kind,
                )
                if node.depth <= model.max_depth and vec not in by_table:
                    by_table[vec] = node
                    additions.append(node)
            if model.cls == CircuitClass.ACC0:
                for mod in model.moduli:
                    for residue in range(mod):
                        vec = tuple(
                            ((int(x) + int(y)) % mod) == residue
                            for x, y in zip(a.table, b.table, strict=True)
                        )
                        node = _Node(
                            vec,
                            current_size,
                            max(a.depth, b.depth) + 1,
                            a.deps | b.deps,
                            f"MOD{mod}_{residue}({a.expr},{b.expr})",
                            "MOD",
                        )
                        if node.depth <= model.max_depth and vec not in by_table:
                            by_table[vec] = node
                            additions.append(node)
        if model.cls in {CircuitClass.AC0, CircuitClass.ACC0}:
            for source in nodes:
                if source.size + 1 != current_size:
                    continue
                vec = tuple(not bit for bit in source.table)
                node = _Node(
                    vec,
                    current_size,
                    source.depth + 1,
                    source.deps,
                    f"NOT({source.expr})",
                    "NOT",
                )
                if node.depth <= model.max_depth and vec not in by_table:
                    by_table[vec] = node
                    additions.append(node)
        return additions

    def _binary_ops(
        self, model: CircuitModel
    ) -> Iterable[tuple[str, Callable[[bool, bool], bool]]]:
        ops: list[tuple[str, Callable[[bool, bool], bool]]] = [
            ("AND", lambda x, y: x and y),
            ("OR", lambda x, y: x or y),
        ]
        if model.cls == CircuitClass.MONOTONE:
            return ops
        return ops

    def _compute_invariants(
        self, function: BooleanFunction, witness: _Node | None, curve: dict[int, int]
    ) -> dict[str, Any]:
        table = function.truth_table()
        symmetry = self._symmetry_group_size(function, table)
        return {
            "symmetry_group_size": symmetry,
            "gate_elimination_candidates": self._gate_elimination(witness, function),
            "locality_score": self._locality_score(witness),
            "depth_size_tradeoff": {str(k): v for k, v in sorted(curve.items())},
        }

    def _symmetry_group_size(
        self, function: BooleanFunction, table: Mapping[BitVector, bool]
    ) -> int:
        n = function.arity()
        if n > self.config["symmetry_exact_limit"]:
            return 0
        count = 0
        for perm in permutations(range(n)):
            preserves = True
            for bits, value in table.items():
                permuted = tuple(bits[i] for i in perm)
                if table[permuted] != value:
                    preserves = False
                    break
            if preserves:
                count += 1
        return count

    def _gate_elimination(
        self, witness: _Node | None, function: BooleanFunction
    ) -> list[dict[str, Any]]:
        if witness is None:
            return []
        support = len(witness.deps)
        threshold = self.config["gate_elimination_keep_ratio"]
        keep_ratio = 1.0 if support <= max(1, function.arity() // 2) else 0.0
        if keep_ratio >= threshold:
            return [
                {
                    "gate": witness.expr,
                    "unchanged_ratio": keep_ratio,
                    "rationale": "Expression support suggests redundancy under random restrictions.",
                }
            ]
        return []

    def _locality_score(self, witness: _Node | None) -> float:
        if witness is None:
            return 0.0
        return float(len(witness.deps))

    def _switching_cross_check(
        self, function: BooleanFunction, witness: _Node | None
    ) -> dict[str, float] | None:
        if (
            witness is None
            or function.arity() > self.config["switching_check_variable_limit"]
        ):
            return None
        dnf = self._truth_table_to_dnf(function)
        p = float(self.config["switching_check_p"])
        t = max(1, witness.depth)
        exact_tail = exact_depth_tail_probability(dnf, p=p, t=t)
        upper = switching_lemma_upper_bound(width=dnf.width(), p=p, t=t)
        return {
            "p": p,
            "t": float(t),
            "tail_probability": exact_tail,
            "upper_bound": upper,
        }

    def _truth_table_to_dnf(self, function: BooleanFunction) -> DNF:
        terms: list[tuple[tuple[str, bool], ...]] = []
        for bits, value in function.truth_table().items():
            if not value:
                continue
            term = tuple(
                (var, bit)
                for var, bit in zip(function.variable_names, bits, strict=True)
            )
            terms.append(term)
        return DNF(terms=tuple(terms))

    def _write_report(self, report: CircuitReport) -> Path:
        path = (
            Path(self.config["output_dir"])
            / f"{report.function_name}_{report.timestamp.replace(':', '-')}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        serializable = asdict(report)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(serializable, fh, indent=2, sort_keys=True)
        return path


def explore(function: BooleanFunction, models: list[CircuitModel]) -> CircuitReport:
    return CircuitExplorerAgent().explore(function, models)
