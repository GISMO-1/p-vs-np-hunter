# 🔬 pvsnp-hunter

pvsnp-hunter is a multi-agent system for circuit lower bounds, conjecture synthesis, and Lean-backed verification in the P vs NP program.

## Active Agents
- `agents/circuit_explorer/`: exact small-n circuit cartography.
- `agents/sat_oracle/`: SAT instance generation, solving, and hardness fingerprinting.
- `agents/lower_bound_hunter/`: Williams pipeline + classical lower-bound techniques.
- `agents/conjecture_engine/`: formal conjecture generation and small-case testing.
- `agents/lean_formalizer/`: JSON proof-sketch → Lean attempt, draft/live verification, feedback.
- `agents/meta_learner/`: failure ingestion, barrier classification, strategy recommendation, progress scoring.

## Lean Project Layout
`lean/pvsnp_hunter/` contains the Lake project and Mathlib dependency:
- `PvsNP/Basic.lean`: core complexity-theory definitions.
- `PvsNP/Circuits.lean`: AC0/ACC0/Monotone types and complexity predicates.
- `PvsNP/LowerBounds.lean`: current axiomatized landmarks (Håstad, Razborov, Williams).
- `PvsNP/Library.lean`: verified theorem registry sink.

If `elan` + `lake` are available, `lean_formalizer` runs in LIVE mode; otherwise it runs DRAFT checks for CI compatibility.

## End-to-End Orchestration
Run one full loop:

```bash
python scripts/run_agents.py --mission lower_bound_hunt --model AC0 --rounds 1
```

This executes:
1. Circuit exploration for the target class.
2. SAT hardness instance generation.
3. Lower-bound hunting.
4. Conjecture proposal.
5. Lean translation and verification attempt.
6. Meta-learner ingestion, scoring, and next-strategy recommendation.

## Known-Result Validation

```bash
python scripts/validate_known_results.py
```

Exit code `0` means the current implementation still reproduces baseline known bounds (AC0 parity and monotone CLIQUE checks).

## Development Checks

```bash
black --check .
isort --check .
mypy --strict agents core scripts
pytest -q --cov=agents --cov=core --cov-report=term-missing
```

## CI
GitHub Actions workflow `.github/workflows/ci.yml` runs lint, tests+coverage, and known-result validation on push/PR to `main` using Python 3.12.
