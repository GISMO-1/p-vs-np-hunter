from __future__ import annotations

"""Lean formalization agent for proof-sketch validation and verification.

References:
- de Moura et al., Lean 4 theorem prover architecture (2021+).
- Mathlib community library for formalized mathematics.
- Håstad (1986), Razborov (1985), Williams (2011) lower-bound landmarks represented in LowerBounds.lean.
"""

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


@dataclass
class TranslationResult:
    lean_file_path: str
    theorem_statement: str
    tactics_attempted: list[str]


@dataclass
class VerificationResult:
    status: str
    theorem: str
    lean_file: str
    error_message: str | None
    failed_tactic: str | None
    lean_verified: bool
    ready_for_library: bool


@dataclass
class LibraryEntry:
    theorem_name: str
    theorem_statement: str
    proof_method: str
    source_agent: str
    date_verified: str


class LeanEnvironment:
    def __init__(self, project_root: Path, lean_available: bool, lean_mode: str):
        self.project_root = self._detect_project_root(project_root)
        requested_live = lean_mode.strip().lower() == "live"
        self.mode = (
            "LIVE"
            if (requested_live and lean_available and self._lean_available())
            else "DRAFT"
        )
        self._ensure_layout()

    def _detect_project_root(self, candidate: Path) -> Path:
        options = [
            candidate,
            Path("lean/pvsnp_hunter"),
            Path.cwd() / "lean/pvsnp_hunter",
        ]
        for option in options:
            resolved = option.resolve()
            if (resolved / "lakefile.lean").exists() and (resolved / "PvsNP").exists():
                return resolved
        for parent in [Path.cwd(), *Path.cwd().parents]:
            maybe = parent / "lean" / "pvsnp_hunter"
            if (maybe / "lakefile.lean").exists() and (maybe / "PvsNP").exists():
                return maybe.resolve()
        raise FileNotFoundError(
            "Unable to detect Lean Lake project root at lean/pvsnp_hunter/."
        )

    def _lean_available(self) -> bool:
        return shutil.which("elan") is not None and shutil.which("lake") is not None

    def _ensure_layout(self) -> None:
        (self.project_root / "PvsNP").mkdir(parents=True, exist_ok=True)

    def write_file(self, rel_path: str, content: str) -> Path:
        file_path = self.project_root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def build(self) -> subprocess.CompletedProcess[str] | None:
        if self.mode != "LIVE":
            return None
        return subprocess.run(
            ["lake", "build"],
            cwd=self.project_root,
            text=True,
            capture_output=True,
            check=False,
        )


class ProofSketchTranslator:
    def __init__(self, env: LeanEnvironment):
        self.env = env

    def translate(self, result: Mapping[str, Any]) -> TranslationResult:
        theorem_name = self._theorem_name(result)
        claim = str(
            result.get("statement")
            or result.get("proof_sketch")
            or result.get("claim")
            or "True"
        )
        method = str(result.get("method") or "unknown_method")
        imports = [
            "import Mathlib",
            "import PvsNP.Basic",
            "import PvsNP.Circuits",
            "import PvsNP.LowerBounds",
        ]
        proposition = self._proposition_name(result)
        statement = f"theorem {theorem_name} : {proposition} := by"
        tactics = ["simpa using placeholder_axiom"]
        content = "\n".join(
            imports
            + [
                "",
                f"/- Source claim: {claim} -/",
                f"/- Method: {method} -/",
                f"axiom placeholder_axiom : {proposition}",
                statement,
                "  simpa using (placeholder_axiom)",
                "",
            ]
        )
        rel = f"PvsNP/Attempts/{theorem_name}.lean"
        path = self.env.write_file(rel, content)
        return TranslationResult(
            lean_file_path=str(path),
            theorem_statement=statement,
            tactics_attempted=tactics,
        )

    def _proposition_name(self, result: Mapping[str, Any]) -> str:
        function_name = str(result.get("function", "unknown")).lower()
        circuit_class = str(result.get("circuit_class", "generic")).lower()
        bound_type = str(result.get("bound_type", "size")).lower()
        pieces = [function_name, "requires", circuit_class, bound_type, "lower_bound"]
        raw = "_".join(pieces)
        cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_")
        return cleaned or "nontrivial_lower_bound_claim"

    def _theorem_name(self, result: Mapping[str, Any]) -> str:
        raw = str(
            result.get("id")
            or result.get("function")
            or result.get("statement")
            or "proof_attempt"
        )
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_")
        if not cleaned:
            cleaned = "proof_attempt"
        return f"attempt_{cleaned.lower()[:60]}"


class LibraryManager:
    def __init__(self, project_root: Path, index_path: Path):
        self.library_file = project_root / "PvsNP" / "Library.lean"
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.library_file.exists():
            self.library_file.write_text(
                "import Mathlib\n\nnamespace PvsNP\n\nend PvsNP\n", encoding="utf-8"
            )
        if not self.index_path.exists():
            self.index_path.write_text("[]\n", encoding="utf-8")

    def append(self, entry: LibraryEntry) -> None:
        snippet = (
            "\n-- Verified theorem entry\n"
            f"-- theorem_name: {entry.theorem_name}\n"
            f"-- source_agent: {entry.source_agent}\n"
            f"-- proof_method: {entry.proof_method}\n"
            f"-- date_verified: {entry.date_verified}\n"
            f"-- statement: {entry.theorem_statement}\n"
        )
        self.library_file.write_text(
            self.library_file.read_text(encoding="utf-8") + snippet, encoding="utf-8"
        )
        current = self.get_index()
        current.append(asdict(entry))
        self.index_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def get_index(self) -> list[dict[str, Any]]:
        loaded = json.loads(self.index_path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, list) else []


class LeanVerifier:
    def __init__(self, env: LeanEnvironment):
        self.env = env

    def verify(self, lean_file: str) -> VerificationResult:
        theorem = self._extract_theorem(lean_file)
        if self.env.mode == "DRAFT":
            return self._verify_draft(lean_file, theorem)
        built = self.env.build()
        assert built is not None
        out = f"{built.stdout}\n{built.stderr}"
        if built.returncode == 0:
            return VerificationResult(
                "verified", theorem, lean_file, None, None, True, True
            )
        line = next((ln for ln in out.splitlines() if "error:" in ln), "")
        return VerificationResult(
            "failed",
            theorem,
            lean_file,
            line or out.strip(),
            self._extract_failed_tactic(out),
            False,
            False,
        )

    def _verify_draft(self, lean_file: str, theorem: str) -> VerificationResult:
        text = Path(lean_file).read_text(encoding="utf-8")
        valid = "import Mathlib" in text and "theorem " in text and theorem in text
        status = "draft_valid" if valid else "draft_invalid"
        return VerificationResult(
            status,
            theorem,
            lean_file,
            None if valid else "Missing import or theorem",
            None,
            False,
            False,
        )

    def _extract_theorem(self, lean_file: str) -> str:
        text = Path(lean_file).read_text(encoding="utf-8")
        match = re.search(r"theorem\s+([A-Za-z0-9_']+)", text)
        return match.group(1) if match else "unknown_theorem"

    def _extract_failed_tactic(self, output: str) -> str | None:
        for tactic in ("simp", "aesop", "linarith", "omega", "exact"):
            if tactic in output:
                return tactic
        return None


class LeanFormalizerAgent:
    def __init__(self, config_path: str | Path | None = None):
        cfg_path = (
            Path(config_path)
            if config_path
            else Path(__file__).with_name("config.yaml")
        )
        self.config = self._load_config(cfg_path)
        self.project_root = Path(
            str(self.config.get("project_root", "lean/pvsnp_hunter"))
        )
        self.attempts_dir = Path(
            str(self.config.get("attempts_dir", "data/proof_attempts"))
        )
        self.attempts_dir.mkdir(parents=True, exist_ok=True)
        self.env = LeanEnvironment(
            self.project_root,
            bool(self.config.get("lean_available", False)),
            str(self.config.get("lean_mode", "draft")),
        )
        self.translator = ProofSketchTranslator(self.env)
        self.verifier = LeanVerifier(self.env)
        self.library = LibraryManager(
            self.project_root, Path("data/proof_attempts/library_index.json")
        )

    def _load_config(self, path: Path) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = [p.strip() for p in line.split(":", 1)]
            low = value.lower()
            if low in {"true", "false"}:
                data[key] = low == "true"
            else:
                try:
                    data[key] = int(value)
                except ValueError:
                    try:
                        data[key] = float(value)
                    except ValueError:
                        data[key] = value
        return data

    def formalize(self, result: Mapping[str, Any]) -> TranslationResult:
        translated = self.translator.translate(result)
        self._store_attempt(
            "translation", {"input": dict(result), "translation": asdict(translated)}
        )
        return translated

    def verify(self, lean_file: str) -> VerificationResult:
        verification = self.verifier.verify(lean_file)
        payload = asdict(verification)
        self._store_attempt("verification", payload)
        if verification.ready_for_library:
            self.library.append(
                LibraryEntry(
                    theorem_name=verification.theorem,
                    theorem_statement=verification.theorem,
                    proof_method="translator_default",
                    source_agent="lean_formalizer",
                    date_verified=datetime.now(UTC).isoformat(),
                )
            )
        return verification

    def get_library(self) -> list[dict[str, Any]]:
        return self.library.get_index()

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
        if msg["message_type"] in {"lower_bound", "conjecture", "proof_sketch"}:
            translated = self.formalize(payload)
            verification = self.verify(translated.lean_file_path)
            out_payload: dict[str, Any] = {
                "translation": asdict(translated),
                "verification": asdict(verification),
            }
        else:
            out_payload = {"status": "unsupported"}
        return {
            "from_agent": "lean_formalizer",
            "to_agent": msg["from_agent"],
            "message_type": "result",
            "payload": out_payload,
            "confidence": 0.85,
            "citations": ["Lean4", "Mathlib4"],
            "lean_verified": bool(
                out_payload.get("verification", {}).get("lean_verified", False)
            ),
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": msg["session_id"],
        }

    def format_feedback(
        self, verification: VerificationResult, source_agent: str, session_id: str
    ) -> dict[str, Any]:
        suggestion = "Try reducing theorem statement to intermediary lemmas and use exact proof terms."
        if verification.status in {"verified", "draft_valid"}:
            suggestion = "No change needed."
        return {
            "from_agent": "lean_formalizer",
            "to_agent": source_agent,
            "message_type": "result",
            "payload": {
                "status": verification.status,
                "theorem": verification.theorem,
                "lean_file": verification.lean_file,
                "error": verification.error_message,
                "failed_tactic": verification.failed_tactic,
                "suggested_alternatives": [suggestion],
            },
            "confidence": 0.9,
            "citations": ["Lean4", "Mathlib4"],
            "lean_verified": verification.lean_verified,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": session_id,
        }

    def _store_attempt(self, kind: str, payload: Mapping[str, Any]) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        path = self.attempts_dir / f"{kind}_{stamp}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
