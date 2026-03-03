# ROADMAP.md

## The Honest Truth About This Project

We might not solve P vs NP. Scott Aaronson has a standing $200K bet that no claimed proof survives peer review. Every crackpot and half the internet has "solved" it.

We are not doing that.

We are building a system that does **real, verifiable, publishable complexity theory** — the kind that gets cited in STOC and CCC papers. Every result we produce is machine-verified. Every conjecture is formally stated. Every lower bound is exact.

If we crack it? History. If we don't? We will have still published real results that push the field forward.

That's the deal.

---

## Milestone 0 — Repository Exists (Day 1) ✅
- [x] Repo created
- [x] README, AGENTS.md, ARCHITECTURE.md, ROADMAP.md
- [x] Project philosophy documented

## Milestone 1 — The Engine Runs (Week 2)
- [ ] Boolean circuit simulator: AC0, monotone, ACC0
- [ ] SAT instance generator + CaDiCaL integration
- [ ] Lean 4 + Mathlib4 environment verified working
- [ ] Agent scaffolding: all 6 agents have skeletons + tests
- [ ] CI/CD: Lean verification runs on every PR

## Milestone 2 — First Real Math (Week 6)
- [ ] Reproduce Håstad switching lemma result in Lean 4
- [ ] Reproduce Razborov-Smolensky result for parity in AC0[p]
- [ ] GNN hardness predictor: 85%+ accuracy on 3-SAT phase transition
- [ ] Conjecture engine: first batch of 10 formally-stated novel conjectures

## Milestone 3 — New Ground (Week 12)
- [ ] New lower bound result in a restricted circuit model (even a tiny improvement)
- [ ] At least one conjecture formally verified by Lean
- [ ] Williams-style pipeline: faster circuit-SAT algorithm → new lower bound
- [ ] Meta-learner: demonstrable improvement in proof search efficiency

## Milestone 4 — Publish (Month 6)
- [ ] Arxiv preprint: "AI-Assisted Circuit Lower Bound Discovery"
- [ ] Lean library of formalized complexity theory lemmas (public)
- [ ] Submit to CCC or STOC workshop

## Milestone 5 — The Long Game (Ongoing)
- [ ] ACC0 → TC0 lower bound (would be historic)
- [ ] Superpolynomial lower bound for any NP function in general circuits
- [ ] P ≠ NP

---

*The universe does love recursion.*
