# 🔬 pvsnp-hunter

## Current Status: ALL 6 AGENTS OPERATIONAL

pvsnp-hunter is in a **computational evidence phase — findings documented, formal verification pending**.

pvsnp-hunter is a multi-agent system for circuit lower bounds, conjecture synthesis, and Lean-backed verification in the P vs NP program.

| Agent | Status | Primary Mission |
|---|---|---|
| `circuit_explorer` | ✅ Operational | Exact small-n circuit cartography across AC0/ACC0/monotone models |
| `sat_oracle` | ✅ Operational | SAT instance generation, solving, and hardness fingerprinting |
| `lower_bound_hunter` | ✅ Operational | Williams pipeline + classical lower-bound techniques |
| `conjecture_engine` | ✅ Operational | Local + optional LLM conjecture synthesis with falsification pathways |
| `lean_formalizer` | ✅ Operational | JSON proof-sketch to Lean translation and draft/live verification |
| `meta_learner` | ✅ Operational | Failure-pattern mining, barrier tagging, and strategy recommendation |

## Findings

See the full report at [`docs/FINDINGS.md`](docs/FINDINGS.md).

- PHP exhibits a finite-window GF(3)/GF(2) degree asymmetry through n≤15, with fitted exponents 1.2079 vs 0.9534 and maximum observed gap 4 (first at n=11).
- Clique and Independent Set (under corrected graph-edge encoding) show near-linear degree growth in both GF(2) and GF(3) on tested sizes.
- Majority shows a GF(2) degree plateau at 2 for n=4..15, while GF(3) degree increases to 9 by n=15.

## Quick Start in 60 Seconds

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/run_agents.py --mission lower_bound_hunt --model AC0 --rounds 1
```

## First Run Output (Sample Session Report)

```text
=== pvsnp-hunter session start ===
mission=lower_bound_hunt model=AC0 rounds=1
[circuit_explorer] analyzed 16 boolean functions; generated complexity profile JSON
[sat_oracle] generated SAT hardness batch; fingerprints saved
[lower_bound_hunter] produced candidate lower-bound report (method=williams_inversion)
[conjecture_engine] emitted 3 conjectures with falsification paths
[lean_formalizer] mode=draft; generated Lean artifacts and diagnostics
[meta_learner] barriers={natural_proofs}; recommended next_strategy=algorithmic-inversion
=== session complete ===
```

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
black --check agents/ core/ scripts/
isort --check agents/ core/ scripts/
mypy --strict agents/ core/ scripts/
pytest -q
```

## CI

GitHub Actions workflow `.github/workflows/ci.yml` runs lint, tests+coverage, and known-result validation on push/PR to `main` using Python 3.12.
