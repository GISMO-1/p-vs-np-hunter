from __future__ import annotations

import json
from pathlib import Path

from agents.lean_formalizer.agent import LeanFormalizerAgent


def test_draft_mode_translation_and_verification() -> None:
    agent = LeanFormalizerAgent()
    translated = agent.formalize(
        {"function": "parity", "proof_sketch": "parity lower bound"}
    )
    assert Path(translated.lean_file_path).exists()
    assert ": parity_requires_" in translated.theorem_statement
    result = agent.verify(translated.lean_file_path)
    assert result.status in {"draft_valid", "verified", "failed"}


def test_known_axioms_file_exists_and_mentions_axioms() -> None:
    text = Path("lean/pvsnp_hunter/PvsNP/LowerBounds.lean").read_text(encoding="utf-8")
    assert "hastad_parity_lower_bound" in text
    assert "razborov_clique_lower_bound" in text
    assert "williams_acc0" in text


def test_library_index_round_trip() -> None:
    agent = LeanFormalizerAgent()
    translated = agent.formalize({"function": "xor", "proof_sketch": "dummy"})
    _ = agent.verify(translated.lean_file_path)
    idx = agent.get_library()
    raw = json.loads(
        Path("data/proof_attempts/library_index.json").read_text(encoding="utf-8")
    )
    assert isinstance(idx, list)
    assert isinstance(raw, list)


def test_failed_verification_feedback_fields() -> None:
    agent = LeanFormalizerAgent()
    bad = Path("lean/pvsnp_hunter/PvsNP/Attempts/bad.lean")
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("theorem bad : True := by\n  invalid_tactic\n", encoding="utf-8")
    v = agent.verify(str(bad))
    feedback = agent.format_feedback(v, "lower_bound_hunter", "session-x")
    payload = feedback["payload"]
    assert "status" in payload
    assert "failed_tactic" in payload
    assert "suggested_alternatives" in payload
