# ARCHITECTURE.md — Technical Deep Dive

## Core Thesis

The "algorithms-to-lower-bounds" paradigm (Williams 2011, 2024 Gödel Prize) is our primary attack vector.

**The key insight:** To prove that a circuit class C cannot compute a function f, design a faster-than-brute-force algorithm for checking C-circuit satisfiability. Faster SAT algorithm for C → lower bound for C. This is counterintuitive and it's why it works — it sidesteps the natural proofs barrier.

## The Three-Barrier Problem

Any proof strategy for P ≠ NP must navigate three known barriers:

### 1. Relativization (Baker-Gill-Solovay 1975)
Most proofs relativize — they hold even when all machines get a free oracle. Any proof of P ≠ NP must be non-relativizing.
**Our approach:** Diagonalization-based techniques that are inherently non-relativizing.

### 2. Natural Proofs (Razborov-Rudich 1994)
If a lower bound proof technique is "natural" (constructive + largeness), it implies one-way functions don't exist. But we believe one-way functions DO exist (cryptography works). So natural proofs cannot prove P ≠ NP.
**Our approach:** Williams-style inversion — use algorithm design to get lower bounds. Not natural.

### 3. Algebrization (Aaronson-Wigderson 2009)
Most proof techniques hold even when machines can evaluate polynomial extensions of oracle functions.
**Our approach:** Geometric and topological invariants that don't algebrize.

## Circuit Model Hierarchy
```
General Boolean Circuits (P/poly) ← ultimate target
         ↑
      TC0 (threshold gates, constant depth)
         ↑
     ACC0 (+ modular counting gates) ← Williams proved NEXP ⊄ ACC0
         ↑
     AC0[p] (+ mod-p gates) ← Razborov-Smolensky: parity ∉ AC0[p] for p ≠ prime
         ↑
      AC0 (AND/OR/NOT, constant depth) ← Håstad: parity ∉ AC0
         ↑
   Monotone Circuits ← Razborov: clique ∉ monotone poly-size
```

We attack from the bottom up, hardening lower bounds at each level.

## Data Flow
```
hard_instances/ ──→ sat_oracle ──→ hardness_features
                                        ↓
circuit_families/ ──→ circuit_explorer ──→ structural_invariants
                                        ↓
                              lower_bound_hunter
                                        ↓
                              conjecture_engine
                                        ↓
                              lean_formalizer ──→ verified_lemmas/
                                        ↓
                              meta_learner ──→ strategy_update
                                        ↑
                              (feedback loop)
```

## Lean 4 Integration

The proof verifier is the single source of truth. No claim is accepted without:
1. Formal statement in Lean 4 type theory
2. Complete proof term that type-checks against Mathlib4
3. Addition to the project lemma library

The kernel is tiny, trusted, and does not hallucinate.

## Compute Strategy

- **Local dev:** Single machine, small circuit families (n ≤ 25)
- **CI/CD:** Automated Lean verification on every PR
- **Distributed:** Ray cluster for large-scale circuit enumeration and SAT campaigns
- **GPU:** PyTorch/JAX for GNN-based hardness prediction and meta-learner RL

## Why This Can Work

The "algorithms to lower bounds" paradigm pioneered in Williams' ACC0 result opened the door to a rich two-way connection between algorithmic techniques and lower bound techniques  — and that connection has only deepened since. Systems like AlphaProof and Harmonic's Aristotle have shown that AI can solve problems open for nearly 30 years using Lean-verified search.  We combine both: algorithmic lower bound discovery + AI-guided formal proof search.

The frontier is real and moving. As recently as April 2025, new win-win circuit lower bounds were published showing that either E^NP requires super-linear series-parallel circuits or coNP requires exponential monotone circuits  — conditional results that narrow the target. We build the machine that finds the unconditional ones.
