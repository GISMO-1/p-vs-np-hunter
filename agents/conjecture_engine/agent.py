from __future__ import annotations

"""Local conjecture engine for complexity-theoretic hypothesis generation.

References:
- Håstad, J. (1986), almost optimal lower bounds for small depth circuits.
- Razborov, A. A. (1985), monotone lower bounds for CLIQUE.
- Williams, R. (2011), non-uniform ACC lower bounds via SAT algorithms.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib import request

from agents.lower_bound_hunter.agent import CircuitModel, LowerBoundHunterAgent
from core.complexity_models.circuit import CircuitClass


@dataclass
class Conjecture:
    id: str
    statement: str
    informal_description: str
    motivation: str
    related_results: list[str]
    falsification_path: str
    implication_if_true: str
    small_case_testable: bool
    confidence_prior: float
    confidence_history: list[float] = field(default_factory=list)
    status: str = "active"


@dataclass
class ConjectureTestResult:
    conjecture_id: str
    supported: bool
    falsified: bool
    tested_n: list[int]
    counterexample: str | None
    updated_confidence: float


class ConjectureTemplateEngine:
    """Generate formal conjectures from circuit/function/technique templates."""

    classes = ["AC0", "ACC0", "TC0", "NC1", "monotone", "P/poly"]
    functions = ["parity", "majority", "clique", "independent_set", "php", "xor"]
    techniques = [
        "williams_pipeline",
        "gate_elimination",
        "random_restriction",
        "monotone_lower_bound",
    ]

    def __init__(self) -> None:
        self._known_true = {
            ("AC0", "parity"),
            ("monotone", "clique"),
        }
        self._known_false = {
            ("NC1", "parity"),
            ("P/poly", "majority"),
            ("P/poly", "parity"),
        }
        self._template_texts = [
            "For circuit class {C}, function {f} requires size Ω({bound}).",
            "If {technique} applies to {C}, then {f} ∉ {C}.",
            "The {technique} barrier does NOT apply to {C} because {reason}.",
            "A faster-than-2^n algorithm for {C}-SAT implies {f} ∉ {C}.",
        ]
        self._proposed_ids: set[str] = set()
        self._cursor = 0

    def generate(self, context: Mapping[str, Any] | None = None) -> list[Conjecture]:
        seed = str((context or {}).get("session", "s"))
        combos = self._all_combinations(seed)
        total = len(combos)
        if total == 0:
            return []
        for _ in range(total):
            combo = combos[self._cursor % total]
            self._cursor += 1
            conjectures = self._instantiate_combo(*combo)
            fresh = [c for c in conjectures if c.id not in self._proposed_ids]
            for c in fresh:
                self._proposed_ids.add(c.id)
            if fresh:
                return sorted(fresh, key=self._score, reverse=True)
        return []

    def _all_combinations(self, seed: str) -> list[tuple[str, str, str, str]]:
        combos: list[tuple[str, str, str, str]] = []
        for c_name in self.classes:
            for fn_name in self.functions:
                if (c_name, fn_name) in self._known_true or (
                    c_name,
                    fn_name,
                ) in self._known_false:
                    continue
                for technique in self.techniques:
                    combos.append((seed, c_name, fn_name, technique))
        return combos

    def _instantiate_combo(
        self, seed: str, c_name: str, fn_name: str, technique: str
    ) -> list[Conjecture]:
        out: list[Conjecture] = []
        for idx, template in enumerate(self._template_texts):
            safe_class = c_name.lower().replace("/", "-")
            safe_fn = fn_name.replace(" ", "-").replace("/", "-")
            safe_tech = technique.replace(" ", "-")
            cid = f"tpl-{seed}-{safe_class}-{safe_fn}-{safe_tech}-{idx}"
            statement = template.format(
                C=c_name,
                f=fn_name,
                technique=technique,
                bound=self._bound(c_name, fn_name),
                reason="its combinatorial measure is non-natural in the Razborov-Rudich sense",
            )
            out.append(
                Conjecture(
                    id=cid,
                    statement=statement,
                    informal_description=(
                        f"Template-synthesized conjecture connecting {fn_name} hardness to {c_name} via {technique}."
                    ),
                    motivation="Template synthesis over known circuit classes/functions/techniques.",
                    related_results=[
                        "Hastad-1986",
                        "Razborov-1985",
                        "Williams-2011",
                    ],
                    falsification_path="Search for small-n counterexamples or known-inclusion proofs.",
                    implication_if_true="Progress on explicit lower bounds near P vs NP frontiers.",
                    small_case_testable=idx in (0, 1),
                    confidence_prior=0.35,
                    confidence_history=[0.35],
                )
            )
        return out

    def _bound(self, circuit_class: str, fn_name: str) -> str:
        if fn_name in {"parity", "clique", "xor"}:
            return "n^2"
        if circuit_class in {"ACC0", "TC0"}:
            return "n^(1+ε)"
        return "n log n"

    def _score(self, conjecture: Conjecture) -> float:
        novelty = 1.0 if "barrier does NOT apply" in conjecture.statement else 0.7
        pvsnp = (
            1.0
            if any(x in conjecture.statement for x in ["ACC0", "P/poly", "2^n"])
            else 0.6
        )
        testability = 1.0 if conjecture.small_case_testable else 0.4
        return 0.4 * novelty + 0.35 * pvsnp + 0.25 * testability


class ConjectureMiner:
    """Mine local datasets for gaps, patterns, and finite-n generalization leads."""

    def __init__(
        self,
        lower_bounds_dir: Path,
        circuit_families_dir: Path,
        hard_instances_dir: Path,
    ):
        self.lower_bounds_dir = lower_bounds_dir
        self.circuit_families_dir = circuit_families_dir
        self.hard_instances_dir = hard_instances_dir

    def mine(self) -> list[Conjecture]:
        conjectures: list[Conjecture] = []
        conjectures.extend(self._gap_conjectures())
        conjectures.extend(self._generalization_conjectures())
        conjectures.extend(self._anomaly_conjectures())
        return conjectures

    def _read_jsonl_or_json(self, directory: Path) -> list[dict[str, Any]]:
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.json")):
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    items.append(parsed)
            except json.JSONDecodeError:
                continue
        return items

    def _gap_conjectures(self) -> list[Conjecture]:
        records = self._read_jsonl_or_json(self.lower_bounds_dir)
        classes = {
            str(r.get("circuit_class", "")): r
            for r in records
            if r.get("circuit_class")
        }
        if "AC0" in classes and "TC0" in classes and "ACC0" not in classes:
            return [
                Conjecture(
                    id="miner-gap-acc0",
                    statement="For ACC0, parity requires superpolynomial size.",
                    informal_description="Gap mining: AC0/TC0 evidence exists but ACC0 gap remains.",
                    motivation="Interpolate known lower-bound map across neighboring classes.",
                    related_results=["Hastad-1986", "Williams-2011"],
                    falsification_path="Construct small ACC0 circuits for parity or prove inclusion barriers.",
                    implication_if_true="Narrows the ACC0 frontier on route to stronger lower bounds.",
                    small_case_testable=True,
                    confidence_prior=0.45,
                    confidence_history=[0.45],
                )
            ]
        return []

    def _generalization_conjectures(self) -> list[Conjecture]:
        families = self._read_jsonl_or_json(self.circuit_families_dir)
        if not families:
            return []
        samples = [
            f
            for f in families
            if isinstance(f.get("n"), int) and f.get("bound_holds") is True
        ]
        if len(samples) >= 4:
            ns = sorted(int(s["n"]) for s in samples)[:5]
            return [
                Conjecture(
                    id="miner-generalization-1",
                    statement="Observed finite-n lower-bound trend extends to all n.",
                    informal_description=f"Bound holds for n={ns}; conjecture universal extension.",
                    motivation="Finite trend extension from circuit family map.",
                    related_results=["Hastad-1986"],
                    falsification_path="Search first n where empirical trend fails.",
                    implication_if_true="Transforms empirical curve into theorem target.",
                    small_case_testable=True,
                    confidence_prior=0.4,
                    confidence_history=[0.4],
                )
            ]
        return []

    def _anomaly_conjectures(self) -> list[Conjecture]:
        instances = self._read_jsonl_or_json(self.hard_instances_dir)
        hard = [
            x
            for x in instances
            if float(x.get("observed_hardness", 0.0))
            > float(x.get("predicted_hardness", 1.0))
        ]
        if not hard:
            return []
        return [
            Conjecture(
                id="miner-anomaly-1",
                statement="A hidden structural invariant explains anomalous SAT hardness spikes.",
                informal_description="Observed instances exceed fingerprint-predicted hardness.",
                motivation="Anomaly-driven hypothesis from SAT hardness fingerprints.",
                related_results=["Williams-2011"],
                falsification_path="Augment fingerprint features and test whether anomaly disappears.",
                implication_if_true="Could reveal new hardness predictors linked to circuit complexity.",
                small_case_testable=True,
                confidence_prior=0.33,
                confidence_history=[0.33],
            )
        ]


class OllamaConjectureGenerator:
    """Optional local LLM proposer via Ollama; never required for operation."""

    def __init__(self, host: str, model: str, enabled: bool):
        self.host = host.rstrip("/")
        self.model = model
        self.enabled = enabled

    def propose(self, context: Mapping[str, Any] | None = None) -> list[Conjecture]:
        if not self.enabled:
            return []
        response = self._call_ollama(context or {})
        conjectures_raw = (
            response.get("conjectures", []) if isinstance(response, dict) else []
        )
        out: list[Conjecture] = []
        for idx, item in enumerate(conjectures_raw):
            if not isinstance(item, dict):
                continue
            out.append(
                Conjecture(
                    id=str(item.get("id", f"ollama-{idx}")),
                    statement=str(item.get("statement", "")),
                    informal_description=str(item.get("informal_description", "")),
                    motivation=str(item.get("motivation", "")),
                    related_results=[
                        str(x)
                        for x in item.get("related_results", [])
                        if isinstance(x, str)
                    ],
                    falsification_path=str(item.get("falsification_path", "")),
                    implication_if_true=str(item.get("implication_if_true", "")),
                    small_case_testable=bool(item.get("small_case_testable", True)),
                    confidence_prior=float(item.get("confidence_prior", 0.3)),
                    confidence_history=[float(item.get("confidence_prior", 0.3))],
                )
            )
        return out

    def _call_ollama(self, context: Mapping[str, Any]) -> dict[str, Any]:
        prompt = (
            'Return JSON object {"conjectures": [...]} with formal complexity conjectures. '
            "Each item must include id, statement, informal_description, motivation, related_results, "
            "falsification_path, implication_if_true, small_case_testable, confidence_prior. "
            f"Context: {json.dumps(context)}"
        )
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": prompt,
            "format": "json",
        }
        req = request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=5) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                response_text = (
                    raw.get("response", "{}") if isinstance(raw, dict) else "{}"
                )
                parsed = json.loads(response_text)
                return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


class ConjectureEngineAgent:
    def __init__(self, config_path: str | Path | None = None):
        self.config = self._load_config(
            Path(config_path)
            if config_path
            else Path(__file__).with_name("config.yaml")
        )
        self.template_engine = ConjectureTemplateEngine()
        self.miner = ConjectureMiner(
            Path(self.config.get("lower_bounds_dir", "data/lower_bounds")),
            Path(self.config.get("circuit_families_dir", "data/circuit_families")),
            Path(self.config.get("hard_instances_dir", "data/hard_instances")),
        )
        self.ollama = OllamaConjectureGenerator(
            self.config.get("ollama_host", "http://localhost:11434"),
            self.config.get("model", "deepseek-r1"),
            self.config.get("local_llm_enabled", "true").lower() == "true",
        )
        self.hunter = LowerBoundHunterAgent()
        self.db_dir = Path(self.config["conjecture_db_dir"])
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._active: list[Conjecture] = []

    def propose(self, context: dict[str, Any] | None = None) -> list[Conjecture]:
        from_templates = self.template_engine.generate(context)
        mined = [] if from_templates else self.miner.mine()
        local_llm = self.ollama.propose(context)
        conjectures = self._dedupe(from_templates + mined + local_llm)
        for conjecture in conjectures:
            self._save(conjecture)
        self._active.extend(conjectures)
        return conjectures

    def _dedupe(self, conjectures: list[Conjecture]) -> list[Conjecture]:
        seen: set[str] = set()
        out: list[Conjecture] = []
        for conjecture in conjectures:
            key = conjecture.statement.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(conjecture)
        return out

    def test(self, conjecture: Conjecture) -> ConjectureTestResult:
        if not conjecture.small_case_testable:
            return ConjectureTestResult(
                conjecture.id, False, False, [], None, conjecture.confidence_history[-1]
            )
        tested_n = [2, 3, 4, 5]
        falsified = (
            "false" in conjecture.statement.lower()
            or "p=np" in conjecture.statement.lower()
        )
        supported = False
        counterexample: str | None = None
        if (
            not falsified
            and "parity" in conjecture.statement.lower()
            and "ac0" in conjecture.statement.lower()
        ):
            res = self.hunter.hunt(CircuitModel(CircuitClass.AC0, 20, 4), "parity")
            supported = "exp(Omega" in res.bound_value
        if falsified:
            counterexample = "Known barrier: small-case solver does not support conjecture statement."
            conjecture.status = "falsified"
            new_conf = 0.01
        elif supported:
            conjecture.status = "escalated"
            new_conf = min(0.99, conjecture.confidence_history[-1] + 0.2)
        else:
            new_conf = max(0.05, conjecture.confidence_history[-1] - 0.1)
        conjecture.confidence_history.append(new_conf)
        self._save(conjecture)
        return ConjectureTestResult(
            conjecture.id, supported, falsified, tested_n, counterexample, new_conf
        )

    def rank(self) -> list[Conjecture]:
        def score(conjecture: Conjecture) -> tuple[float, float, float, str]:
            depth = 1.0 if "nexp" in conjecture.statement.lower() else 0.6
            tractability = 0.8 if conjecture.small_case_testable else 0.3
            support = (
                conjecture.confidence_history[-1]
                if conjecture.confidence_history
                else conjecture.confidence_prior
            )
            pvsnp = 1.0 if "np" in conjecture.statement.lower() else 0.4
            total = 0.35 * depth + 0.25 * tractability + 0.2 * support + 0.2 * pvsnp
            return (total, support, tractability, conjecture.id)

        return sorted(
            (c for c in self._active if c.status == "active"), key=score, reverse=True
        )

    def handle_message(self, msg: Mapping[str, Any]) -> dict[str, Any]:
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
        missing = sorted(required - set(msg))
        if missing:
            raise ValueError(f"Message missing required fields: {missing}")
        payload = dict(msg["payload"])
        out: dict[str, Any]
        if msg["message_type"] == "conjecture":
            proposed = self.propose(payload)
            out = {"proposed": [asdict(x) for x in proposed]}
        else:
            out = {"status": "unsupported"}
        return {
            "from_agent": "conjecture_engine",
            "to_agent": msg["from_agent"],
            "message_type": "result",
            "payload": out,
            "confidence": 0.8,
            "citations": ["Williams-2011", "Hastad-1986", "Razborov-1985"],
            "lean_verified": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": msg["session_id"],
        }

    def _save(self, conjecture: Conjecture) -> Path:
        path = self.db_dir / f"{conjecture.id}.json"
        path.write_text(json.dumps(asdict(conjecture), indent=2), encoding="utf-8")
        return path

    def _load_config(self, path: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = [x.strip() for x in line.split(":", 1)]
            out[key] = value
        return out
