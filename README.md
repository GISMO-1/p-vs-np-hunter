# 🔬 pvsnp-hunter

> *"A computer program that uses computation to discover the limits of computation."*

**pvsnp-hunter** is a multi-agent AI research system designed to make meaningful progress on the **P vs NP problem** — one of the seven Millennium Prize Problems and the deepest open question in computer science.

This is not a toy. This is not a simulation. This system is built to do real mathematical work:
- Discover circuit lower bounds in progressively stronger models
- Generate and formally verify proof sketches in Lean 4
- Synthesize new conjectures via AI-guided search
- Self-improve its own algorithms through reinforcement learning loops

---

## 🧠 What Is P vs NP?

If a solution to a problem can be **verified quickly**, can it also be **solved quickly**?

- **P** = problems solvable in polynomial time
- **NP** = problems whose solutions are verifiable in polynomial time
- If P = NP → encryption collapses, optimization becomes trivial, AI goes superhuman overnight
- If P ≠ NP → computational hardness is a law of nature, some problems are forever intractable

No one has proven either. We strongly suspect P ≠ NP. This system hunts for the proof.

---

## 🏗️ System Architecture
```
pvsnp-hunter/
├── agents/                    # All autonomous agents
│   ├── circuit_explorer/      # Generates & analyzes boolean circuit families
│   ├── sat_oracle/            # ML-enhanced SAT solver & hardness detector
│   ├── lower_bound_hunter/    # Searches for superpolynomial lower bounds
│   ├── conjecture_engine/     # Proposes new mathematical conjectures
│   ├── lean_formalizer/       # Converts proof sketches to Lean 4
│   └── meta_learner/          # Learns from failed proof attempts
├── core/
│   ├── complexity_models/     # AC0, ACC0, TC0, monotone circuit models
│   ├── reduction_engine/      # NP-complete problem reduction library
│   ├── invariant_detector/    # Finds structural invariants in hard instances
│   └── proof_verifier/        # Lean 4 kernel integration
├── data/
│   ├── hard_instances/        # Curated library of genuinely hard SAT instances
│   ├── circuit_families/      # Indexed boolean function families
│   └── proof_attempts/        # All partial proofs (wins AND failures)
├── experiments/               # Reproducible experiment configs
├── benchmarks/                # Runtime & correctness benchmarks
├── scripts/                   # Setup, run, and analysis scripts
├── docs/                      # Deep technical documentation
├── AGENTS.md                  # Agent behavior specs
├── CONTRIBUTING.md
├── ARCHITECTURE.md
└── ROADMAP.md
```

---

## 🎯 Mission Objectives

### Phase 1 — Foundation (Weeks 1–4)
- [ ] Boolean circuit simulation engine (AC0, ACC0, TC0, monotone)
- [ ] SAT instance generator with hardness classification
- [ ] Baseline ML circuit lower bound hunter
- [ ] Lean 4 environment scaffolding

### Phase 2 — Agent Launch (Weeks 5–10)
- [ ] Circuit Explorer Agent: enumerate minimal circuits for NP functions
- [ ] Lower Bound Hunter: detect superpolynomial growth patterns
- [ ] Conjecture Engine: propose and rank new mathematical conjectures
- [ ] Lean Formalizer: translate promising sketches to checkable proofs

### Phase 3 — Deep Autonomy (Weeks 11–20)
- [ ] Meta-Learner: self-improve from failed attempts via RL
- [ ] Williams-style "algorithms-to-lower-bounds" pipeline
- [ ] Natural proofs barrier detection and circumvention strategies
- [ ] Full formal proof pipeline from conjecture → Lean-verified theorem

### Phase 4 — Publish or Perish (Ongoing)
- [ ] Automated paper draft generation from successful proof fragments
- [ ] Integration with Lean Mathlib
- [ ] ArXiv submission pipeline for novel partial results

---

## 🚧 Known Barriers (We Know What We're Up Against)

| Barrier | Description | Our Strategy |
|---|---|---|
| **Relativization** | Most proofs fail when oracles are added | Use non-relativizing techniques (diagonalization) |
| **Natural Proofs** | Most lower bound methods are self-defeating | Williams' "algorithms → lower bounds" inversion |
| **Algebrization** | Algebraic extensions break most proofs | Geometric/topological circuit invariants |
| **Unknown unknowns** | We don't know what we don't know | Conjecture engine + meta-learner loop |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Core language | Python 3.12 + Rust (hot paths) |
| Formal proofs | Lean 4 + Mathlib |
| ML backbone | PyTorch + JAX |
| SAT solving | CaDiCaL, Kissat, custom ML-SAT hybrid |
| Graph/circuit analysis | NetworkX + custom C++ engine |
| Agent orchestration | Custom multi-agent framework |
| Experiment tracking | Weights & Biases |
| Distributed compute | Ray |

---

## 🚀 Quick Start
```bash
git clone https://github.com/GISMO-1/pvsnp-hunter
cd pvsnp-hunter
pip install -r requirements.txt
python scripts/setup_lean.py
python scripts/run_agents.py --mission lower_bound_hunt --model AC0
```

---

## ⚡ Philosophy

This project proceeds on the assumption that:

1. **The proof exists** — mathematical truth doesn't hide forever
2. **Computation can find structure humans miss** — pattern detection at scale
3. **Formal verification is non-negotiable** — no hand-waving, ever
4. **Failure is data** — every failed proof attempt teaches the meta-learner

We are not here to approximate. We are here to prove.

---

## 📜 License

MIT — because if we crack P vs NP, the whole world should benefit.

---

## 🤝 Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md) first.
PRs should be large, ambitious, and well-tested. We don't do incremental here.
