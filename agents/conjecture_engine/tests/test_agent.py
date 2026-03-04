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


def test_template_engine_avoids_duplicates_across_rounds() -> None:
    engine = ConjectureTemplateEngine()
    first = engine.generate({"session": "s1"})
    second = engine.generate({"session": "s1"})
    assert first and second
    assert first[0].id != second[0].id


def test_agent_switches_to_miner_when_templates_exhausted(tmp_path: Path) -> None:
    _write(
        tmp_path / "lower_bounds" / "ac0.json", {"circuit_class": "AC0", "bound": "exp"}
    )
    _write(
        tmp_path / "lower_bounds" / "tc0.json",
        {"circuit_class": "TC0", "bound": "superpoly"},
    )
    agent = _agent(tmp_path)
    agent.template_engine.classes = ["AC0"]
    agent.template_engine.functions = ["parity"]
    agent.template_engine.techniques = ["williams_pipeline"]
    # Exhaust all 4 templates for the single available combination.
    for _ in range(4):
        _ = agent.propose({"session": "mini"})
    out = agent.propose({"session": "mini"})
    assert any(c.id.startswith("miner-") for c in out)


def test_propose_runs_small_case_tester_and_updates_history(tmp_path: Path) -> None:
    agent = _agent(tmp_path)
    out = agent.propose({"session": "small-case"})
    tested = [c for c in out if c.small_case_testable]
    assert tested
    assert any(len(c.confidence_history) > 1 for c in tested)


def test_template_sets_min_n_for_asymptotic_bounds() -> None:
    engine = ConjectureTemplateEngine()
    conjectures = engine.generate({"session": "min-n"})
    assert conjectures
    size_bound = [c for c in conjectures if "requires size Ω(" in c.statement]
    assert size_bound
    c = size_bound[0]
    if "n log n" in c.statement:
        assert c.min_n >= 8
    if "n^2" in c.statement:
        assert c.min_n >= 6


def test_small_case_tester_respects_min_n(tmp_path: Path) -> None:
    agent = _agent(tmp_path)
    conjecture = agent.propose({"session": "min-n-run"})[0]
    conjecture.min_n = 8
    result = agent.test(conjecture)
    assert result.tested_n == [8, 9, 10, 11, 12]
