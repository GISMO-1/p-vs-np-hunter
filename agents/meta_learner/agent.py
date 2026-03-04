from __future__ import annotations

"""Meta-learner agent for learning from proof attempts and recommending strategy.

References:
- Baker-Gill-Solovay (1975) relativization barrier.
- Razborov-Rudich (1994) natural proofs barrier.
- Aaronson-Wigderson (2009) algebrization barrier.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4
from pathlib import Path
from typing import Any, Literal, Mapping

BarrierType = Literal["relativization", "natural_proofs", "algebrization", "unknown"]


@dataclass
class BarrierClassification:
    barrier: BarrierType
    agent: str
    technique: str
    failure_mode: str


@dataclass
class StrategyRecommendation:
    technique: str
    rationale: str
    expected_barrier_risk: float
    priority: int


class BarrierClassifier:
    def classify(self, attempt: Mapping[str, Any]) -> BarrierType:
        text = json.dumps(attempt).lower()
        if "natural" in text and "proof" in text:
            return "natural_proofs"
        if "relativ" in text or "oracle" in text:
            return "relativization"
        if "algebr" in text:
            return "algebrization"
        return "unknown"


class RewardCalculator:
    def score(self, attempt: Mapping[str, Any], seen_conjectures: set[str]) -> float:
        score = 0.0
        if attempt.get("type") == "lower_bound":
            score += 1.0 if bool(attempt.get("known_result")) else 3.0
        if attempt.get("type") == "conjecture" and attempt.get("status") == "active":
            conjecture_id = str(attempt.get("id", ""))
            if conjecture_id and conjecture_id in seen_conjectures:
                score -= 0.5
            else:
                if conjecture_id:
                    seen_conjectures.add(conjecture_id)
                score += 5.0
        return score


class SessionScorer:
    def __init__(self, attempts_dir: Path):
        self.attempts_dir = attempts_dir
        self.reward = RewardCalculator()

    def session_score(self, session_id: str) -> float:
        total = 0.0
        seen_conjectures: set[str] = set()
        for rec in _load_attempts(self.attempts_dir):
            if str(rec.get("session_id", "")) == session_id:
                total += self.reward.score(rec, seen_conjectures)
        return total


class StrategyRecommender:
    def recommend(
        self,
        circuit_class: str,
        target_function: str,
        attempt_history: list[dict[str, Any]],
    ) -> StrategyRecommendation:
        del target_function
        techniques: dict[str, tuple[int, int]] = {}
        for attempt in attempt_history:
            if (
                str(attempt.get("circuit_class", ""))
                and attempt.get("circuit_class") != circuit_class
            ):
                continue
            t = str(attempt.get("technique", "unknown"))
            success = (
                1
                if bool(
                    attempt.get("lean_verified") or attempt.get("status") == "verified"
                )
                else 0
            )
            tried, won = techniques.get(t, (0, 0))
            techniques[t] = (tried + 1, won + success)
        ranked = sorted(
            techniques.items(),
            key=lambda kv: ((kv[1][1] / max(1, kv[1][0])), -kv[1][0]),
            reverse=True,
        )
        for tech, (tried, won) in ranked:
            if tried > 0 and won == 0:
                continue
            risk = 1.0 - (won / max(1, tried))
            return StrategyRecommendation(
                tech, f"Technique {tech} has non-zero success history.", risk, 1
            )
        fallback = (
            "random_restriction"
            if circuit_class.upper() == "AC0"
            else "gate_elimination"
        )
        return StrategyRecommendation(
            fallback, "Fallback to literature-grounded baseline technique.", 0.6, 2
        )


class MetaLearnerAgent:
    def __init__(self, config_path: str | Path | None = None):
        _ = config_path
        self.attempts_dir = Path("data/proof_attempts")
        self.meta_dir = Path("data/meta")
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.classifier = BarrierClassifier()
        self.recommender = StrategyRecommender()
        self.scorer = SessionScorer(self.attempts_dir)
        self.map_path = self.meta_dir / "proof_space_map.json"
        if not self.map_path.exists():
            self.map_path.write_text(
                json.dumps({"nodes": {}, "edges": []}, indent=2), encoding="utf-8"
            )

    def ingest_failure(self, attempt: Mapping[str, Any]) -> BarrierClassification:
        normalized = self._normalize_attempt(attempt)
        barrier = self.classifier.classify(normalized)
        classification = BarrierClassification(
            barrier=barrier,
            agent=str(
                normalized.get("source_agent", normalized.get("from_agent", "unknown"))
            ),
            technique=str(normalized.get("technique", "unknown")),
            failure_mode=str(normalized.get("failure_mode", "unknown")),
        )
        self._persist_attempt(normalized)
        self._update_proof_space_map(normalized, classification)
        return classification

    def recommend_strategy(self, context: Mapping[str, Any]) -> StrategyRecommendation:
        history = [x for x in _load_attempts(self.attempts_dir)]
        return self.recommender.recommend(
            str(context.get("circuit_class", "AC0")),
            str(context.get("target_function", "parity")),
            history,
        )

    def score_session(self, session_id: str) -> float:
        return self.scorer.session_score(session_id)

    def get_progress_report(self) -> dict[str, Any]:
        attempts = _load_attempts(self.attempts_dir)
        total = len(attempts)
        verified = sum(
            1
            for a in attempts
            if bool(a.get("lean_verified")) or a.get("status") == "verified"
        )
        failed = sum(1 for a in attempts if str(a.get("status", "")).startswith("fail"))
        classes: dict[str, set[str]] = {}
        for a in attempts:
            cls = str(a.get("circuit_class", "unknown"))
            tech = str(a.get("technique", "unknown"))
            if cls == "unknown" or tech == "unknown":
                continue
            classes.setdefault(cls, set()).add(tech)
        report = {
            "total_proof_attempts": total,
            "success_rate": (verified / total) if total else 0.0,
            "techniques_tried_per_circuit_class": {
                k: sorted(v) for k, v in classes.items()
            },
            "conjectures": {
                "active": sum(
                    1
                    for a in attempts
                    if a.get("type") == "conjecture" and a.get("status") == "active"
                ),
                "falsified": sum(1 for a in attempts if a.get("status") == "falsified"),
                "verified": sum(
                    1
                    for a in attempts
                    if a.get("type") == "conjecture" and bool(a.get("lean_verified"))
                ),
            },
            "lower_bounds": {
                "known_reproduced": sum(
                    1 for a in attempts if a.get("known_result") is True
                ),
                "candidate_new_results": sum(
                    1
                    for a in attempts
                    if a.get("type") == "lower_bound" and a.get("known_result") is False
                ),
            },
            "lean_verifications": {
                "verified": verified,
                "failed": failed,
                "pending": max(0, total - verified - failed),
            },
            "estimated_distance_to_publishable_result": (
                "high" if verified == 0 else "moderate"
            ),
        }
        out = self.meta_dir / "progress_report.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

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
        if msg["message_type"] == "query" and payload.get("action") == "recommend":
            out: dict[str, Any] = asdict(self.recommend_strategy(payload))
        elif msg["message_type"] == "result":
            out = asdict(self.ingest_failure(payload))
        else:
            out = {"status": "unsupported"}
        return {
            "from_agent": "meta_learner",
            "to_agent": msg["from_agent"],
            "message_type": "result",
            "payload": out,
            "confidence": 0.8,
            "citations": [
                "Baker-Gill-Solovay-1975",
                "Razborov-Rudich-1994",
                "Aaronson-Wigderson-2009",
            ],
            "lean_verified": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": msg["session_id"],
        }

    def _normalize_attempt(self, attempt: Mapping[str, Any]) -> dict[str, Any]:
        normalized = dict(attempt)
        lb = normalized.get("lower_bound_result")
        if isinstance(lb, Mapping):
            normalized.setdefault("circuit_class", str(lb.get("circuit_class", "unknown")))
            normalized.setdefault("technique", str(lb.get("method", "unknown")))
            normalized.setdefault("known_result", bool(lb.get("known_result", False)))
            normalized.setdefault("function", str(lb.get("function", "unknown")))
        normalized.setdefault("circuit_class", str(normalized.get("circuit_class", "unknown")))
        normalized.setdefault("technique", str(normalized.get("technique", "unknown")))
        normalized.setdefault("session_id", str(normalized.get("session_id", "unknown")))
        normalized.setdefault("status", str(normalized.get("status", "unknown")))
        return normalized

    def _persist_attempt(self, attempt: Mapping[str, Any]) -> Path:
        self.attempts_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        ident = uuid4().hex[:8]
        path = self.attempts_dir / f"meta_{stamp}_{ident}.json"
        path.write_text(json.dumps(dict(attempt), indent=2), encoding="utf-8")
        return path

    def _update_proof_space_map(
        self, attempt: dict[str, Any], classification: BarrierClassification
    ) -> None:
        data = json.loads(self.map_path.read_text(encoding="utf-8"))
        nodes: dict[str, dict[str, Any]] = data.get("nodes", {})
        edges: list[dict[str, Any]] = data.get("edges", [])
        tech = classification.technique
        node = nodes.get(tech, {"attempts": 0, "successes": 0, "barrier_hit_count": {}})
        node["attempts"] = int(node.get("attempts", 0)) + 1
        success = bool(
            attempt.get("lean_verified") or attempt.get("status") == "verified"
        )
        node["successes"] = int(node.get("successes", 0)) + (1 if success else 0)
        hit = dict(node.get("barrier_hit_count", {}))
        hit[classification.barrier] = int(hit.get(classification.barrier, 0)) + 1
        node["barrier_hit_count"] = hit
        node["success_rate"] = node["successes"] / max(1, node["attempts"])
        node["last_attempted"] = datetime.now(UTC).isoformat()
        nodes[tech] = node
        prev = str(attempt.get("previous_technique", ""))
        if prev:
            edges.append(
                {
                    "from": prev,
                    "to": tech,
                    "circuit_class": str(attempt.get("circuit_class", "unknown")),
                }
            )
        self.map_path.write_text(
            json.dumps({"nodes": nodes, "edges": edges}, indent=2), encoding="utf-8"
        )


def _load_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    attempts: list[dict[str, Any]] = []
    for file in sorted(path.glob("*.json")):
        try:
            loaded = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, dict):
            attempts.append(loaded)
    return attempts
