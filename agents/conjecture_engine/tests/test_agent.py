from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from agents.conjecture_engine.agent import Conjecture, ConjectureEngineAgent, ConjectureGenerator


class MockGenerator(ConjectureGenerator):
    def __init__(self) -> None:
        super().__init__(api_key="k", model="claude-sonnet-4-20250514")
        self.last_payload: dict[str, Any] = {}

    def _call_api(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        self.last_payload = dict(payload)
        return {
            "conjectures": [
                {
                    "id": "c1",
                    "statement": "Parity not in AC0 with polynomial size.",
                    "informal_description": "Connected to P vs NP through circuit lower bounds.",
                    "motivation": "Classical frontier.",
                    "related_results": ["Hastad-1986"],
                    "falsification_path": "Search small circuits.",
                    "implication_if_true": "Stronger AC0 understanding.",
                    "small_case_testable": True,
                    "confidence_prior": 0.5,
                }
            ]
        }


def _agent(tmp_path: Path) -> tuple[ConjectureEngineAgent, MockGenerator]:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "model: claude-sonnet-4-20250514",
                "anthropic_api_key: test",
                f"conjecture_db_dir: {tmp_path / 'db'}",
            ]
        ),
        encoding="utf-8",
    )
    agent = ConjectureEngineAgent(cfg)
    mock = MockGenerator()
    agent.generator = mock
    return agent, mock


def test_api_payload_shape(tmp_path: Path) -> None:
    agent, mock = _agent(tmp_path)
    _ = agent.propose({"context": "x"})
    payload = mock.last_payload
    assert payload["model"] == "claude-sonnet-4-20250514"
    assert "system" in payload
    assert payload["messages"]


def test_small_case_falsifies_known_false(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    c = Conjecture(
        id="false1",
        statement="P=NP is false-conjecture marker",
        informal_description="test",
        motivation="test",
        related_results=[],
        falsification_path="test",
        implication_if_true="test",
        small_case_testable=True,
        confidence_prior=0.2,
        confidence_history=[0.2],
    )
    out = agent.test(c)
    assert out.falsified
    assert out.updated_confidence < 0.05


def test_small_case_supports_known_true(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    conjecture = agent.propose()[0]
    out = agent.test(conjecture)
    assert out.supported
    assert out.updated_confidence > 0.5


def test_ranking_deterministic(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    c1 = agent.propose()[0]
    c2 = Conjecture(
        id="c2",
        statement="NEXP lower bound candidate",
        informal_description="Related to P vs NP",
        motivation="test",
        related_results=[],
        falsification_path="",
        implication_if_true="",
        small_case_testable=False,
        confidence_prior=0.1,
        confidence_history=[0.1],
    )
    agent._active = [c1, c2]
    ordered = [c.id for c in agent.rank()]
    assert ordered == ["c1", "c2"]


def test_serialization_roundtrip(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    c = agent.propose()[0]
    saved = tmp_path / "db" / f"{c.id}.json"
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["id"] == c.id
