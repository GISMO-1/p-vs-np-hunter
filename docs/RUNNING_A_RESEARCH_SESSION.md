# Running a Research Session

This guide explains how to run one complete pvsnp-hunter session and interpret outputs.

## 1) Agent Roles (Plain English)

- **circuit_explorer**: maps small Boolean functions to exact circuit complexity profiles.
- **sat_oracle**: creates SAT instances and computes hardness fingerprints.
- **lower_bound_hunter**: searches for candidate lower-bound steps (Williams pipeline, monotone, switching-lemma style checks).
- **conjecture_engine**: proposes formal conjectures with small-case evidence and falsification paths.
- **lean_formalizer**: turns proof sketches into Lean artifacts and attempts verification.
- **meta_learner**: classifies failure modes (barriers) and proposes next strategic direction.

## 2) Run a Full Research Session

From repo root:

```bash
python scripts/run_agents.py --mission lower_bound_hunt --model AC0 --rounds 1
```

Optional environment setup:

```bash
cp .env.example .env
```

## 3) Read Session Output

A full session report includes:

- mission metadata (model, rounds, timestamp)
- per-agent structured outputs
- candidate lower bounds and proof sketches
- conjectures with confidence and citations
- Lean formalization status (draft/live)
- meta-learner strategic recommendation

Treat each record as a message object with confidence, citations, and verification status.

## 4) Interpreting `LowerBoundResult`

Typical fields:

- `target_class`: circuit class (e.g., AC0, ACC0, monotone)
- `bound_value`: textual quantitative claim
- `method`: method family (`williams_inversion`, `monotone_approximation`, etc.)
- `proof_sketch`: human-readable rationale to formalize
- `citations`: theorem/paper keys supporting the claim
- `lean_ready`: whether the sketch is structured enough for Lean translation

A useful `LowerBoundResult` must include clear assumptions and should be considered a *candidate* until formalized.

## 5) Reading Conjecture Engine Output

A conjecture output should contain:

- formal statement
- motivation
- small-case evidence
- falsification path
- implication if true

Prefer conjectures that are falsifiable with existing tooling and align with known barriers.

## 6) Meaning of `lean_ready: true`

`lean_ready: true` means the proof sketch is formatted to be ingested by `agents/lean_formalizer` without additional schema translation. It does **not** mean the theorem is already verified.

Recommended next action:

1. Send the sketch to `lean_formalizer`.
2. Run Lean checks.
3. If errors occur, feed structured error output back to the originating agent.

## 7) Set Up Lean 4 for LIVE Verification

Use elan (not system Lean):

```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
source "$HOME/.elan/env"
cd lean/pvsnp_hunter
lake update
lake build
```

After successful build, run a research session again; Lean formalizer should report LIVE mode when toolchain detection succeeds.
