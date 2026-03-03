from __future__ import annotations

"""SAT Oracle: hardness instance generation, solving, and prediction.

References:
- S. Cook, "The complexity of theorem-proving procedures," STOC 1971.
- A. Tseitin, "On the complexity of derivation in propositional calculus," 1968.
- M. Ben-Sasson and A. Wigderson, "Short proofs are narrow," JACM 2001 (resolution hardness intuition).
- B. Monien and E. Speckenmeyer, "Solving satisfiability in less than 2^n steps," Discrete Applied Math. 1985 (DPLL lineage).
"""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
import random
import re
import statistics
import subprocess
import time
from typing import Any, Mapping, Sequence


@dataclass
class SATInstance:
    instance_type: str
    num_vars: int
    clauses: list[tuple[int, ...]]
    metadata: dict[str, Any]

    def to_dimacs(self) -> str:
        body = [" ".join(str(v) for v in c) + " 0" for c in self.clauses]
        return f"p cnf {self.num_vars} {len(self.clauses)}\n" + "\n".join(body) + "\n"

    def save(self, root: Path) -> tuple[Path, Path]:
        root.mkdir(parents=True, exist_ok=True)
        stem = f"{self.instance_type}_{self.num_vars}_{int(time.time()*1000)}"
        cnf_path = root / f"{stem}.cnf"
        meta_path = root / f"{stem}.json"
        cnf_path.write_text(self.to_dimacs(), encoding="utf-8")
        payload = asdict(self)
        meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return cnf_path, meta_path

    @staticmethod
    def from_files(cnf_path: Path, meta_path: Path) -> SATInstance:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        clauses: list[tuple[int, ...]] = []
        for line in cnf_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("c", "p")):
                continue
            nums = [int(x) for x in line.split()]
            clauses.append(tuple(x for x in nums if x != 0))
        return SATInstance(meta["instance_type"], meta["num_vars"], clauses, meta["metadata"])


@dataclass
class SolveResult:
    result: str
    solve_time_sec: float
    conflicts: int
    decisions: int
    learned_clauses: int
    assignment: dict[int, bool] | None
    solver: str


@dataclass
class HardnessFingerprint:
    feature_names: list[str]
    values: list[float]
    metadata: dict[str, Any]


@dataclass
class HardnessPrediction:
    score: float
    label: str
    model: str


class DPLLSolver:
    def solve(self, instance: SATInstance) -> SolveResult:
        start = time.perf_counter()
        stats = {"conflicts": 0, "decisions": 0, "learned": 0}
        assignment = self._dpll(instance.clauses, {}, instance.num_vars, stats)
        elapsed = time.perf_counter() - start
        if assignment is None:
            return SolveResult("UNSAT", elapsed, stats["conflicts"], stats["decisions"], stats["learned"], None, "dpll")
        return SolveResult("SAT", elapsed, stats["conflicts"], stats["decisions"], stats["learned"], assignment, "dpll")

    def _dpll(self, clauses: Sequence[tuple[int, ...]], assignment: dict[int, bool], num_vars: int, stats: dict[str, int]) -> dict[int, bool] | None:
        reduced = self._simplify(clauses, assignment)
        if reduced is None:
            stats["conflicts"] += 1
            return None
        if not reduced:
            return assignment.copy()
        unit = next((c[0] for c in reduced if len(c) == 1), None)
        if unit is not None:
            lit = unit
            assignment[abs(lit)] = lit > 0
            return self._dpll(reduced, assignment, num_vars, stats)
        var = next(v for v in range(1, num_vars + 1) if v not in assignment)
        stats["decisions"] += 1
        for value in (True, False):
            assignment[var] = value
            out = self._dpll(reduced, assignment, num_vars, stats)
            if out is not None:
                return out
        assignment.pop(var, None)
        return None

    def _simplify(self, clauses: Sequence[tuple[int, ...]], assignment: Mapping[int, bool]) -> list[tuple[int, ...]] | None:
        out: list[tuple[int, ...]] = []
        for clause in clauses:
            undecided: list[int] = []
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var not in assignment:
                    undecided.append(lit)
                    continue
                if assignment[var] == (lit > 0):
                    satisfied = True
                    break
            if satisfied:
                continue
            if not undecided:
                return None
            out.append(tuple(undecided))
        return out


class SATOracleAgent:
    def __init__(self, config_path: str | Path | None = None):
        cfg_path = Path(config_path) if config_path else Path(__file__).with_name("config.yaml")
        self.config = self._load_config(cfg_path)
        self.data_dir = Path(self.config["hard_instances_dir"])
        self.model_path = Path(self.config["model_path"])
        self.dpll = DPLLSolver()
        self._model_weights: list[float] | None = None
        self._cadical_available = self._find_cadical() is not None

    def _load_config(self, path: Path) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = [p.strip() for p in line.split(":", 1)]
            if value.lower() in {"true", "false"}:
                data[key] = value.lower() == "true"
            else:
                try:
                    data[key] = int(value)
                except ValueError:
                    try:
                        data[key] = float(value)
                    except ValueError:
                        data[key] = value
        return data

    def generate(self, instance_type: str, n_vars: int, **kwargs: Any) -> SATInstance:
        if instance_type in {"3sat", "ksat"}:
            k = int(kwargs.get("k", 3))
            ratio = float(kwargs.get("ratio", 4.0))
            clauses = self._random_k_sat(n_vars, k, ratio)
        elif instance_type == "planted":
            ratio = float(kwargs.get("ratio", 4.0))
            backbone = float(kwargs.get("backbone", 0.5))
            clauses = self._planted_sat(n_vars, ratio, backbone)
        elif instance_type == "tseitin_k4":
            clauses, n_vars = self._tseitin_k4()
        elif instance_type == "php":
            n = int(kwargs.get("n", max(2, n_vars - 1)))
            clauses, n_vars = self._php(n)
        else:
            raise ValueError(f"Unknown instance_type {instance_type}")
        instance = SATInstance(instance_type, n_vars, clauses, {"kwargs": kwargs, "created": datetime.now(UTC).isoformat()})
        cnf_path, meta_path = instance.save(self.data_dir)
        fp = self.fingerprint(instance)
        (self.data_dir / f"{cnf_path.stem}.fingerprint.json").write_text(json.dumps(asdict(fp), indent=2), encoding="utf-8")
        instance.metadata["paths"] = {"cnf": str(cnf_path), "meta": str(meta_path)}
        return instance

    def solve(self, instance: SATInstance) -> SolveResult:
        cadical = self._find_cadical()
        if cadical is None:
            return self.dpll.solve(instance)
        tmp = self.data_dir / "_tmp_query.cnf"
        tmp.write_text(instance.to_dimacs(), encoding="utf-8")
        try:
            completed = subprocess.run([cadical, str(tmp)], capture_output=True, text=True, timeout=float(self.config["cadical_timeout_sec"]))
        except subprocess.TimeoutExpired:
            return SolveResult("TIMEOUT", float(self.config["cadical_timeout_sec"]), 0, 0, 0, None, "cadical")
        text = completed.stdout + "\n" + completed.stderr
        result = "UNKNOWN"
        if "SATISFIABLE" in text and "UNSATISFIABLE" not in text:
            result = "SAT"
        if "UNSATISFIABLE" in text:
            result = "UNSAT"
        return SolveResult(result, 0.0, self._stat(text, "conflicts"), self._stat(text, "decisions"), self._stat(text, "learned"), None, "cadical")

    def fingerprint(self, instance: SATInstance) -> HardnessFingerprint:
        n = instance.num_vars
        m = len(instance.clauses)
        ratio = m / max(1, n)
        var_degree = [0] * (n + 1)
        for c in instance.clauses:
            for lit in c:
                var_degree[abs(lit)] += 1
        non_zero = [d for d in var_degree[1:] if d > 0]
        mean_deg = statistics.mean(non_zero) if non_zero else 0.0
        std_deg = statistics.pstdev(non_zero) if len(non_zero) > 1 else 0.0
        clustering = self._variable_clustering(instance)
        spectral_gap = self._spectral_gap(instance)
        backbone = self._backbone_fraction(instance)
        pebbling_lb = math.log2(1 + max(non_zero, default=0))
        vsids_var = self._vsids_activity_variance(instance)
        values = [ratio, mean_deg, std_deg, clustering, spectral_gap, backbone, pebbling_lb, vsids_var]
        return HardnessFingerprint(
            ["clause_var_ratio", "degree_mean", "degree_std", "clustering", "spectral_gap", "backbone_fraction", "resolution_lb_est", "vsids_variance"],
            [float(v) for v in values],
            {"num_clauses": m, "num_vars": n},
        )

    def predict_hardness(self, instance: SATInstance) -> HardnessPrediction:
        fp = self.fingerprint(instance)
        if self._model_weights is None:
            self._load_or_train_model([instance])
        assert self._model_weights is not None
        score = sum(w * x for w, x in zip(self._model_weights, fp.values, strict=False))
        label = "hard" if score > 0.5 else "easy"
        return HardnessPrediction(float(score), label, "mlp-fallback")

    def handle_message(self, message: Mapping[str, Any]) -> dict[str, Any]:
        required = {"from_agent", "to_agent", "message_type", "payload", "confidence", "citations", "lean_verified", "timestamp", "session_id"}
        missing = sorted(required - set(message))
        if missing:
            raise ValueError(f"Message missing required fields: {missing}")
        kind = str(message["message_type"])
        payload = dict(message["payload"])
        if kind == "query" and payload.get("action") == "generate":
            instance = self.generate(str(payload["instance_type"]), int(payload["n_vars"]), **payload.get("kwargs", {}))
            data = asdict(instance)
        elif kind == "query" and payload.get("action") == "solve":
            inst = SATInstance(**payload["instance"])
            data = asdict(self.solve(inst))
        else:
            data = {"status": "unsupported"}
        return {
            "from_agent": "sat_oracle",
            "to_agent": message["from_agent"],
            "message_type": "result",
            "payload": data,
            "confidence": 0.9,
            "citations": ["Tseitin-1968", "Cook-1971"],
            "lean_verified": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": message["session_id"],
        }

    def _random_k_sat(self, n_vars: int, k: int, ratio: float) -> list[tuple[int, ...]]:
        rng = random.Random(int(self.config["seed"]))
        num_clauses = int(ratio * n_vars)
        clauses: list[tuple[int, ...]] = []
        for _ in range(num_clauses):
            vars_ = rng.sample(range(1, n_vars + 1), k=min(k, n_vars))
            clauses.append(tuple(v if rng.random() < 0.5 else -v for v in vars_))
        return clauses

    def _planted_sat(self, n_vars: int, ratio: float, backbone: float) -> list[tuple[int, ...]]:
        rng = random.Random(int(self.config["seed"]) + 7)
        planted = {i: rng.random() < 0.5 for i in range(1, n_vars + 1)}
        frozen = set(rng.sample(list(planted), int(backbone * n_vars)))
        clauses: list[tuple[int, ...]] = []
        for _ in range(int(ratio * n_vars)):
            vars_ = rng.sample(range(1, n_vars + 1), k=min(3, n_vars))
            lits = []
            for v in vars_:
                if v in frozen:
                    lits.append(v if planted[v] else -v)
                else:
                    sign = 1 if rng.random() < 0.5 else -1
                    lits.append(sign * v)
            if not any((lit > 0) == planted[abs(lit)] for lit in lits):
                lits[0] *= -1
            clauses.append(tuple(lits))
        return clauses

    def _tseitin_k4(self) -> tuple[list[tuple[int, ...]], int]:
        edges = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
        incidence: dict[int, list[int]] = {1: [], 2: [], 3: [], 4: []}
        for idx, (u, v) in enumerate(edges, start=1):
            incidence[u].append(idx)
            incidence[v].append(idx)
        charges = {1: 1, 2: 0, 3: 0, 4: 0}
        clauses: list[tuple[int, ...]] = []
        for v in range(1, 5):
            a, b, c = incidence[v]
            rhs = charges[v]
            for x in (0, 1):
                for y in (0, 1):
                    for z in (0, 1):
                        if (x ^ y ^ z) == rhs:
                            continue
                        clause = (a if x == 0 else -a, b if y == 0 else -b, c if z == 0 else -c)
                        clauses.append(clause)
        return clauses, len(edges)

    def _php(self, n: int) -> tuple[list[tuple[int, ...]], int]:
        pigeons = n + 1
        num_vars = pigeons * n
        def var(p: int, h: int) -> int:
            return p * n + h + 1
        clauses: list[tuple[int, ...]] = []
        for p in range(pigeons):
            clauses.append(tuple(var(p, h) for h in range(n)))
            for h1 in range(n):
                for h2 in range(h1 + 1, n):
                    clauses.append((-var(p, h1), -var(p, h2)))
        for h in range(n):
            for p1 in range(pigeons):
                for p2 in range(p1 + 1, pigeons):
                    clauses.append((-var(p1, h), -var(p2, h)))
        return clauses, num_vars

    def _variable_clustering(self, instance: SATInstance) -> float:
        neigh: dict[int, set[int]] = {v: set() for v in range(1, instance.num_vars + 1)}
        for clause in instance.clauses:
            vars_ = [abs(l) for l in clause]
            for i in range(len(vars_)):
                for j in range(i + 1, len(vars_)):
                    neigh[vars_[i]].add(vars_[j])
                    neigh[vars_[j]].add(vars_[i])
        vals: list[float] = []
        for v in neigh:
            d = len(neigh[v])
            if d < 2:
                continue
            links = 0
            pairs = d * (d - 1) / 2
            nodes = list(neigh[v])
            for i in range(d):
                for j in range(i + 1, d):
                    if nodes[j] in neigh[nodes[i]]:
                        links += 1
            vals.append(links / pairs)
        return statistics.mean(vals) if vals else 0.0

    def _spectral_gap(self, instance: SATInstance) -> float:
        deg = [0] * (instance.num_vars + 1)
        for c in instance.clauses:
            for lit in c:
                deg[abs(lit)] += 1
        if not deg[1:]:
            return 0.0
        max_d = max(deg[1:])
        min_d = min(d for d in deg[1:] if d > 0) if any(d > 0 for d in deg[1:]) else 0
        return float(max_d - min_d)

    def _backbone_fraction(self, instance: SATInstance) -> float:
        rng = random.Random(int(self.config["seed"]) + 11)
        sat_assignments: list[dict[int, bool]] = []
        for _ in range(int(self.config["backbone_samples"])):
            guess = {v: rng.random() < 0.5 for v in range(1, instance.num_vars + 1)}
            if self._satisfies(instance.clauses, guess):
                sat_assignments.append(guess)
        if len(sat_assignments) < 2:
            return 0.0
        fixed = 0
        for v in range(1, instance.num_vars + 1):
            values = {a[v] for a in sat_assignments}
            if len(values) == 1:
                fixed += 1
        return fixed / instance.num_vars

    def _vsids_activity_variance(self, instance: SATInstance) -> float:
        activity = [0.0] * (instance.num_vars + 1)
        for c in instance.clauses:
            for lit in c:
                activity[abs(lit)] += 1.0
        vals = [x for x in activity[1:] if x > 0]
        return statistics.pvariance(vals) if len(vals) > 1 else 0.0

    def _load_or_train_model(self, instances: list[SATInstance]) -> None:
        if self.model_path.exists():
            payload = json.loads(self.model_path.read_text(encoding="utf-8"))
            self._model_weights = [float(x) for x in payload["weights"]]
            return
        xs = [self.fingerprint(inst).values for inst in instances]
        ys = [math.log(self.solve(inst).solve_time_sec + 1e-6) for inst in instances]
        dim = len(xs[0])
        means = [statistics.mean(row[i] for row in xs) for i in range(dim)]
        target = statistics.mean(ys)
        norm = sum(abs(m) for m in means) + 1e-9
        self._model_weights = [target * m / norm for m in means]
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_path.write_text(json.dumps({"weights": self._model_weights}), encoding="utf-8")

    def _satisfies(self, clauses: Sequence[tuple[int, ...]], assignment: Mapping[int, bool]) -> bool:
        for clause in clauses:
            if not any(assignment.get(abs(l), False) == (l > 0) for l in clause):
                return False
        return True

    def _find_cadical(self) -> str | None:
        for candidate in ("cadical", "./cadical"):
            try:
                subprocess.run([candidate, "--version"], capture_output=True, timeout=1, check=False)
                return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def _stat(self, text: str, key: str) -> int:
        match = re.search(rf"{key}\s*:?\s*(\d+)", text, flags=re.IGNORECASE)
        return int(match.group(1)) if match else 0
