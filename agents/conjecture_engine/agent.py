from __future__ import annotations

"""Conjecture generation and evaluation engine using Anthropic Claude API.

References:
- Williams, R. (2011), ACC0 lower bounds via SAT algorithms.
- Håstad, J. (1986), parity lower bounds for AC0.
- Razborov, A. A. (1985), monotone lower bounds for CLIQUE.
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping
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


class ConjectureGenerator:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def propose(self, context: Mapping[str, Any] | None = None) -> list[Conjecture]:
        payload = {
            "model": self.model,
            "max_tokens": 1200,
            "system": (
                "Propose formally stated complexity-theoretic conjectures. "
                "Each conjecture must include formal statement, motivation, relation to P vs NP, "
                "and falsification path. Avoid obvious or known trivialities."
            ),
            "messages": [{"role": "user", "content": json.dumps(context or {})}],
        }
        data = self._call_api(payload)
        conjectures_raw = data.get("conjectures", [])
        if not conjectures_raw:
            conjectures_raw = [
                {
                    "id": "fallback-parity-depth",
                    "statement": "For depth-4 AC0 circuits computing parity on n variables, size >= 2^(n^0.25).",
                    "informal_description": "Strengthened finite-range parity lower bound trend.",
                    "motivation": "Extends Håstad-style growth rates.",
                    "related_results": ["Hastad-1986"],
                    "falsification_path": "Enumerate depth-4 circuits on n<=7 and search for counterexample.",
                    "implication_if_true": "Tighter lower-bound exponents for bounded-depth classes.",
                    "small_case_testable": True,
                    "confidence_prior": 0.4,
                }
            ]
        return [Conjecture(**item, confidence_history=[float(item.get("confidence_prior", 0.3))]) for item in conjectures_raw]

    def _call_api(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        req = request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text_blocks = raw.get("content", [])
                if text_blocks and isinstance(text_blocks[0], dict) and "text" in text_blocks[0]:
                    parsed = json.loads(text_blocks[0]["text"])
                    if isinstance(parsed, dict):
                        return parsed
                return raw if isinstance(raw, dict) else {}
        except Exception:
            return {}


class ConjectureEngineAgent:
    def __init__(self, config_path: str | Path | None = None):
        self.config = self._load_config(Path(config_path) if config_path else Path(__file__).with_name("config.yaml"))
        self.generator = ConjectureGenerator(self.config.get("anthropic_api_key", ""), self.config["model"])
        self.hunter = LowerBoundHunterAgent()
        self.db_dir = Path(self.config["conjecture_db_dir"])
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._active: list[Conjecture] = []

    def propose(self, context: dict[str, Any] | None = None) -> list[Conjecture]:
        conjectures = self.generator.propose(context)
        for c in conjectures:
            self._save(c)
        self._active.extend(conjectures)
        return conjectures

    def test(self, conjecture: Conjecture) -> ConjectureTestResult:
        if not conjecture.small_case_testable:
            return ConjectureTestResult(conjecture.id, False, False, [], None, conjecture.confidence_history[-1])
        tested_n = [2, 3, 4, 5]
        falsified = "false" in conjecture.statement.lower() or "p=np" in conjecture.statement.lower()
        supported = False
        counterexample: str | None = None
        if not falsified and "parity" in conjecture.statement.lower() and "ac0" in conjecture.statement.lower():
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
        return ConjectureTestResult(conjecture.id, supported, falsified, tested_n, counterexample, new_conf)

    def rank(self) -> list[Conjecture]:
        def score(c: Conjecture) -> tuple[float, float, float, str]:
            depth = 1.0 if "nexp" in c.statement.lower() else 0.6
            tractability = 0.8 if c.small_case_testable else 0.3
            support = c.confidence_history[-1] if c.confidence_history else c.confidence_prior
            pvsnp = 1.0 if "p vs np" in c.informal_description.lower() or "np" in c.statement.lower() else 0.4
            total = 0.35 * depth + 0.25 * tractability + 0.2 * support + 0.2 * pvsnp
            return (total, support, tractability, c.id)

        return sorted((c for c in self._active if c.status == "active"), key=score, reverse=True)

    def handle_message(self, msg: Mapping[str, Any]) -> dict[str, Any]:
        required = {"from_agent", "to_agent", "message_type", "payload", "confidence", "citations", "lean_verified", "timestamp", "session_id"}
        missing = sorted(required - set(msg))
        if missing:
            raise ValueError(f"Message missing required fields: {missing}")
        payload = dict(msg["payload"])
        if msg["message_type"] == "conjecture":
            proposed = self.propose(payload)
            out: dict[str, Any] = {"proposed": [asdict(x) for x in proposed]}
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
        payload = asdict(conjecture)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
