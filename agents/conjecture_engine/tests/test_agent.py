from __future__ import annotations

import json
from pathlib import Path

from agents.conjecture_engine.agent import (
    ConjectureEngineAgent,
    ConjectureMiner,
    ConjectureTemplateEngine,
    OllamaConjectureGenerator,
)


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _agent(tmp_path: Path) -> ConjectureEngineAgent:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "model: deepseek-r1",
                "local_llm_enabled: true",
                "ollama_host: http://localhost:11434",
                f"conjecture_db_dir: {tmp_path / 'db'}",
                f"lower_bounds_dir: {tmp_path / 'lower_bounds'}",
                f"circuit_families_dir: {tmp_path / 'circuit_families'}",
                f"hard_instances_dir: {tmp_path / 'hard_instances'}",
            ]
        ),
        encoding="utf-8",
    )
    return ConjectureEngineAgent(cfg)


def test_template_generation_produces_valid_conjectures() -> None:
    engine = ConjectureTemplateEngine()
    out = engine.generate({"session": "t"})
    assert out
    assert all(c.id and c.statement and c.related_results for c in out)


def test_miner_finds_acc0_gap(tmp_path: Path) -> None:
    _write(tmp_path / "lower" / "ac0.json", {"circuit_class": "AC0", "bound": "exp"})
    _write(
        tmp_path / "lower" / "tc0.json", {"circuit_class": "TC0", "bound": "superpoly"}
    )
    miner = ConjectureMiner(
        tmp_path / "lower", tmp_path / "circuits", tmp_path / "hard"
    )
    out = miner.mine()
    assert any(c.id == "miner-gap-acc0" for c in out)


def test_ollama_fallback_when_unavailable() -> None:
    ollama = OllamaConjectureGenerator(
        "http://localhost:65535", "deepseek-r1", enabled=True
    )
    out = ollama.propose({"goal": "test"})
    assert out == []


def test_agent_propose_degrades_gracefully_with_empty_data(tmp_path: Path) -> None:
    agent = _agent(tmp_path)
    out = agent.propose({"session": "x"})
    assert out
    assert (tmp_path / "db").exists()


def test_serialization_roundtrip(tmp_path: Path) -> None:
    agent = _agent(tmp_path)
    c = agent.propose({"session": "r"})[0]
    saved = tmp_path / "db" / f"{c.id}.json"
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["id"] == c.id
