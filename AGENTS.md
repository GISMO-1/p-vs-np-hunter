# AGENTS.md — Agent Behavior Specification for pvsnp-hunter

> This file governs how all AI agents (including Codex) behave inside this repository.
> **Read this before writing a single line of code.**

---

## 🧭 Prime Directive

Every agent in this system exists for one purpose:
**Make mathematical progress toward resolving P vs NP.**

This means:
- Build things that are **mathematically correct**, not just computationally clever
- Formal verification is the gold standard — if it can't be Lean-checked, it's a sketch
- Every PR must advance the mission; no cosmetic changes, no vanity refactors

---

## 🤖 Agent Roster

### 1. `circuit_explorer` — The Cartographer
**Mission:** Map the landscape of boolean circuit complexity.

**Responsibilities:**
- Implement simulation of all major circuit classes: AC0, ACC0, TC0, NC1, monotone
- Generate explicit boolean function families and compute their circuit complexity
- Enumerate all circuits up to size N for target functions
- Detect structural properties: symmetry, locality, gate elimination candidates
- Output: circuit complexity databases, structural invariant reports

**Codex instructions:**
- Never approximate. Exact gate counts matter.
- Build Rust extensions for any computation over n > 20 variables
- All circuit families must be serializable and reproducible
- Tests must cover all known lower bound results (Håstad, Razborov-Smolensky, etc.)

---

### 2. `sat_oracle` — The Interrogator
**Mission:** Understand the deep structure of SAT hardness.

**Responsibilities:**
- Generate 3-SAT, k-SAT, and circuit-SAT instances across the full hardness spectrum
- Classify instances by phase transition, backbone structure, and resolution complexity
- Train ML models to predict hardness from structural features
- Implement CDCL, DPLL, and custom hybrid solvers
- Build a "hardness fingerprint" for every instance class

**Codex instructions:**
- Use CaDiCaL and Kissat as baseline solvers; wrap them cleanly
- GNN-based hardness predictor is high priority — graph the variable-clause graph
- All generated instances must be stored with metadata in `data/hard_instances/`
- Create adversarial instance generators: find inputs that break known heuristics

---

### 3. `lower_bound_hunter` — The Excavator
**Mission:** Find superpolynomial lower bounds in increasingly strong circuit models.

**Responsibilities:**
- Implement Williams' "algorithms-to-lower-bounds" paradigm
- Search for functions in NP that require large circuits in restricted models
- Implement the gate elimination method and its generalizations
- Track the current frontier: we know 3.1n lower bounds for affine dispersers; we need more
- Detect when a lower bound proof candidate might generalize

**Codex instructions:**
- Start with AC0 and monotone circuits — these are solved, use as ground truth tests
- Target ACC0 as the next frontier (Williams 2011 result is the starting point)
- Every candidate lower bound must generate a formal proof sketch before being reported
- Build a "generalization detector": does this bound hold in a stronger model?

---

### 4. `conjecture_engine` — The Dreamer
**Mission:** Propose new mathematical conjectures for humans and agents to prove.

**Responsibilities:**
- Use LLM backbone (Claude API) to propose new complexity-theoretic conjectures
- Filter conjectures by: novelty, falsifiability, tractability, and potential impact
- Test conjectures on small cases automatically before surfacing them
- Maintain a ranked conjecture database with confidence scores
- Connect conjectures to known results via automated literature graph

**Codex instructions:**
- Conjectures must be formally stated, not informal vibes
- Every conjecture must include: statement, motivation, small-case evidence, falsification path
- Use the Anthropic API (claude-sonnet-4-20250514) for conjecture generation
- Build a conjecture evolution tree: child conjectures derived from parent conjectures

---

### 5. `lean_formalizer` — The Judge
**Mission:** Convert proof sketches into machine-verified Lean 4 proofs.

**Responsibilities:**
- Maintain Lean 4 + Mathlib environment
- Accept proof sketches from other agents and attempt formalization
- Return structured error feedback to the originating agent
- Build a library of formalized complexity theory lemmas
- Track proof completion percentage for all active proof attempts

**Codex instructions:**
- Install Lean 4 via elan — do not use system Lean
- Mathlib4 is a required dependency — pull it via Lake
- Proof sketches come in as structured JSON; output Lean 4 `.lean` files
- Every verified lemma must be added to `core/proof_verifier/library/`
- The verifier never approves unverified proofs — no exceptions

---

### 6. `meta_learner` — The Strategist
**Mission:** Learn from everything that fails and improve the system's own strategy.

**Responsibilities:**
- Ingest all failed proof attempts and extract structural failure patterns
- Update agent search strategies based on what has and hasn't worked
- Implement RL loop: reward = progress toward verified proof fragment
- Maintain a "proof space map" of explored and unexplored territory
- Identify which barriers (relativization, natural proofs, algebrization) each attempt hits

**Codex instructions:**
- This is the most experimental component — use JAX for flexibility
- Reward shaping is critical: reward partial progress, not just full proofs
- The meta-learner must expose a clean API for other agents to query strategy
- Log everything to Weights & Biases with structured tags

---

## 📐 Coding Standards for All Agents

### Structure
- Each agent lives in `agents/<agent_name>/`
- Required files: `__init__.py`, `agent.py`, `config.yaml`, `tests/`, `README.md`
- Agents communicate via message-passing (no shared mutable state)
- All agent outputs are structured JSON or Lean 4 files

### Code Quality
- Type annotations everywhere — use `mypy --strict`
- No functions longer than 50 lines without a documented reason
- All mathematical operations must cite the theorem/paper they implement
- Every module must have >80% test coverage

### Git Discipline
- Branch names: `agent/<name>/<feature>` or `core/<subsystem>/<feature>`
- PRs must include: what mathematical progress this enables
- No PR that doesn't advance the mission is merged
- Commit messages must be precise: "Implement Håstad switching lemma for AC0 lower bounds" not "fix stuff"

---

## 🚨 What Codex Must Never Do

1. **Never hallucinate mathematical results** — cite or verify everything
2. **Never simplify away correctness for performance**
3. **Never merge a proof claim without Lean verification**
4. **Never use approximation where exactness is required**
5. **Never ignore a known complexity barrier** — if you're hitting one, say so

---

## 🏆 Definition of Progress

We define "progress" as any of the following:
1. A new Lean-verified lower bound result (even in a restricted model)
2. A new conjecture with formal statement + small-case evidence
3. A new connection between two previously unrelated lower bound techniques
4. A new SAT hardness characterization that holds provably
5. Any result that, if extended, would imply P ≠ NP

Everything else is infrastructure. Infrastructure serves these five goals.

---

## 📡 Communication Protocol Between Agents
```python
# All inter-agent messages follow this schema:
{
  "from_agent": str,           # sender agent name
  "to_agent": str,             # recipient (or "broadcast")
  "message_type": str,         # "conjecture" | "proof_sketch" | "lower_bound" | "query" | "result"
  "payload": dict,             # structured content
  "confidence": float,         # 0.0 to 1.0
  "citations": list[str],      # paper DOIs or arXiv IDs
  "lean_verified": bool,       # has this been formally verified?
  "timestamp": str,
  "session_id": str
}
```

---

## 🔗 External Resources Agents May Use

- **Lean 4 Mathlib**: https://leanprover-community.github.io/mathlib4_docs/
- **ECCC** (complexity preprints): https://eccc.weizmann.ac.il
- **Complexity Zoo**: https://complexityzoo.net
- **arxiv cs.CC**: https://arxiv.org/list/cs.CC/recent
- **Clay Institute P vs NP page**: https://www.claymath.org/millennium/p-vs-np/

---

*"We are not here to approximate. We are here to prove."*
