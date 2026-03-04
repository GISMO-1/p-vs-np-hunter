# Computational Findings — pvsnp-hunter

## Status
All findings below are computational observations on finite inputs (n ≤ 15). None are proofs. Each statement remains a hypothesis-level computational result until formal verification (e.g., Lean-checked theorem statements plus verified lemmas) is completed.

## Finding 1: PHP shows superlinear GF(3) vs sublinear GF(2) degree growth

For the PHP analysis window n = 2,\dots,15, the recorded approximate polynomial degrees are:

| n | deg\_GF(2) | deg\_GF(3) | gap = GF(3) − GF(2) |
|---:|---:|---:|---:|
| 2 | 2 | 2 | 0 |
| 3 | 2 | 2 | 0 |
| 4 | 2 | 2 | 0 |
| 5 | 3 | 3 | 0 |
| 6 | 3 | 3 | 0 |
| 7 | 4 | 5 | 1 |
| 8 | 4 | 5 | 1 |
| 9 | 5 | 7 | 2 |
| 10 | 6 | 9 | 3 |
| 11 | 7 | 11 | 4 |
| 12 | 8 | 12 | 4 |
| 13 | 9 | 13 | 4 |
| 14 | 10 | 14 | 4 |
| 15 | 11 | 15 | 4 |

Power-law fits on this finite window give exponents:
- GF(2): \(\alpha = 0.9534\)
- GF(3): \(\alpha = 1.2079\)

The first occurrence of the largest observed gap is at n=11 with gap=4 (and this same gap value persists through n=15).

Interpretation (conditional): if this cross-field separation continued in a theorem-strength asymptotic form matching Smolensky-style polynomial method hypotheses, it would support hardness against ACC0[p] in the incompatible-modulus setting. In this restricted sense, the computation is consistent with the direction of known PHP lower-bound phenomena.

However, this dataset does **not** prove the Beame–Impagliazzo–Krajíček–Pitassi–Pudlák–Woods (1992) PHP lower bounds. It is only an empirical signature on small n. To become a theorem, one would need (at minimum):
1. Exact (not merely heuristic) approximation-degree guarantees for the analyzed PHP encoding.
2. A rigorous transfer theorem from those degree bounds to the relevant circuit lower bound statement.
3. A formal proof chain (ideally Lean-checked) with explicit asymptotics.

Honest caveat: all values are finite-n computations, and the approximator may not coincide with exact minimum approximation degree.

## Finding 2: Clique and Independent Set show linear degree growth in all tested fields

Using the corrected graph-edge encoding (n edge variables where n = \(\binom{k}{2}\)), the computed degrees for valid n in the range 3 ≤ n ≤ 15 are:

| n (edges) | k (vertices) | clique GF(2) | clique GF(3) | indep. set GF(2) | indep. set GF(3) |
|---:|---:|---:|---:|---:|---:|
| 3 | 3 | 3 | 3 | 3 | 3 |
| 6 | 4 | 6 | 6 | 6 | 6 |
| 10 | 5 | 9 | 10 | 9 | 10 |
| 15 | 6 | 15 | 14 | 15 | 14 |

The fitted exponents are close to linear for both fields (clique: GF(2) \(\alpha\approx0.9762\), GF(3) \(\alpha\approx0.9650\); independent set identical on this dataset).

Interpretation (conditional): if these trends reflected true asymptotic lower bounds under the required hypotheses of the polynomial method, they would indicate hardness signatures across ACC0[p] for multiple primes p rather than a single-field artifact.

This is also consistent with (but does not derive from) Razborov's monotone lower bound for CLIQUE, which is a different technique with different proof obligations.

Honest caveat: this is a small-graph regime only (k up to 6 vertices). Asymptotic behavior may differ.

## Finding 3: Majority shows permanent GF(2) degree plateau at 2 on tested range

For majority on n = 4,\dots,15:
- GF(2) degree is constant at 2 for every tested n.
- GF(3) degrees are: 2, 3, 2, 3, 2, 3, 4, 5, 6, 7, 8, 9 (for n=4..15), i.e., approximately linear growth over the tested range and reaching degree 9 at n=15.

Interpretation:
- The data indicates an efficient low-degree GF(2) polynomial approximation signature for majority in this computation.
- This is consistent with known complexity-theoretic context in which majority is computable in TC0 (so "easy for threshold circuits" is expected).
- The GF(3) growth pattern suggests possible field-specific hardness behavior against ACC0[3], subject to theorem-level conditions not yet established.

Honest caveat: the GF(2) plateau at degree 2 could be a property of the approximator rather than the exact minimum degree; independent verification is required.

## What These Findings Suggest (Carefully Stated)

Across PHP, clique/independent set, and majority, the observed polynomial-degree patterns are consistent with the known qualitative circuit-complexity hierarchy. In particular, the PHP GF(3)/GF(2) split and the near-linear clique/independent-set growth provide quantitative computational evidence that can prioritize formal-proof search directions, but do not themselves establish new lower-bound theorems.

## Next Steps

- Extend PHP analysis to n=20 and quantify computational feasibility (runtime/memory plus exactness diagnostics).
- Attempt Lean formalization of the Smolensky-criterion application template for PHP.
- Determine whether the majority GF(2) degree-2 plateau survives exact (non-heuristic) computation.
- Run the same degree analysis on TC0-complete functions and compare polynomial-degree signatures.

## References
- Razborov (1987)
- Smolensky (1987)
- Beame, Impagliazzo, Krajíček, Pitassi, Pudlák, Woods (1992)
- Williams (2011)
- Håstad (1986)
