# Mathematical Foundations

This document states the core complexity-theoretic results and barriers that anchor the pvsnp-hunter research program.

## 1) Three Foundational Barriers

### 1.1 Relativization (Baker–Gill–Solovay, 1975)

A proof technique **relativizes** if the same argument remains valid when every Turing machine in the argument is given oracle access to an arbitrary oracle \(A\). Formally, a relativizing argument proving \(\mathsf{P} \neq \mathsf{NP}\) would also prove \(\mathsf{P}^A \neq \mathsf{NP}^A\) for all \(A\). Baker, Gill, and Solovay constructed oracles \(A, B\) such that:

- \(\mathsf{P}^A = \mathsf{NP}^A\)
- \(\mathsf{P}^B \neq \mathsf{NP}^B\)

Therefore, any purely relativizing method cannot resolve \(\mathsf{P}\) vs \(\mathsf{NP}\).

### 1.2 Natural Proofs (Razborov–Rudich, 1994)

Let \(\mathcal{P}\) be a property of Boolean functions used to separate hard functions from an easy circuit class \(\mathcal{C}\). A proof strategy is *natural* when \(\mathcal{P}\) is:

1. **Constructive**: membership in \(\mathcal{P}\) is efficiently decidable from the truth table.
2. **Large**: a non-negligible fraction of all Boolean functions satisfy \(\mathcal{P}\).
3. **Useful**: all functions computed by \(\mathcal{C}\) fail \(\mathcal{P}\).

Razborov and Rudich show that strong pseudorandom generators imply such natural properties cannot prove superpolynomial lower bounds against \(\mathsf{P}/\mathsf{poly}\).

### 1.3 Algebrization (Aaronson–Wigderson, 2009)

Algebrization strengthens relativization by allowing low-degree algebraic extensions of oracle access. They show many known non-relativizing techniques still algebrize and remain insufficient for central class separations, including \(\mathsf{P}\) vs \(\mathsf{NP}\). Thus, successful methods must also avoid the algebrization trap.

## 2) Williams' Algorithms-to-Lower-Bounds Paradigm

### Theorem (Williams, 2011; representative statement)

For typical nonuniform classes \(\mathcal{C}\) (including ACC\(^0\)-type settings), a nontrivial SAT algorithm for \(\mathcal{C}\)-circuits yields circuit lower bounds against \(\mathcal{C}\). In particular, Williams proved:

\[
\mathsf{NEXP} \not\subseteq \mathsf{ACC}^0.
\]

The proof route is an inversion principle: **faster satisfiability for a circuit class implies that class is too weak to represent all NEXP computation**.

Operationally in this repo, this appears as the lower_bound_hunter pipeline that treats SAT-exponent improvements as evidence-producing candidates for lower-bound transitions.

## 3) Håstad's Switching Lemma (Formal Statement Form)

Let \(F\) be a width-\(w\) DNF (or CNF) and let \(\rho\) be a random \(p\)-restriction that leaves each variable unset independently with probability \(p\), otherwise fixing it uniformly in \(\{0,1\}\). Then for every \(t \ge 1\):

\[
\Pr_{\rho}\left[\mathrm{DT\_depth}(F\upharpoonright\rho) \ge t\right] \le (c p w)^t,
\]

for an absolute constant \(c\). This is the quantitative engine behind exponential AC\(^0\) lower bounds for parity.

## 4) Razborov's Approximation Method for Monotone Circuits

Razborov (1985) proves superpolynomial monotone lower bounds for CLIQUE by approximating monotone circuits with combinatorial objects whose behavior diverges on carefully chosen positive/negative distributions. The method compares acceptance probabilities and uses sunflower-style combinatorics to control approximators, yielding separation between monotone circuit capability and CLIQUE complexity.

## 5) Circuit Model Hierarchy

We use the standard containment chain:

\[
\mathsf{AC}^0 \subseteq \mathsf{ACC}^0 \subseteq \mathsf{TC}^0 \subseteq \mathsf{P}/\mathsf{poly}.
\]

- **AC\(^0\)**: constant depth, polynomial size, unbounded fan-in AND/OR/NOT.
- **ACC\(^0\)**: AC\(^0\) plus MOD\(_m\) gates (fixed \(m\)).
- **TC\(^0\)**: constant depth threshold circuits.
- **P/poly**: polynomial-size nonuniform circuits.

## 6) Our Attack Strategy vs. the Barriers

1. **Against natural proofs**: prioritize Williams-style algorithmic inversion, where progress comes from SAT algorithms and structure-sensitive transformations rather than large constructive properties.
2. **Against relativization**: integrate nonuniform circuit analysis and proof artifacts tied to specific circuit representations, not oracle-generic diagonalization alone.
3. **Against algebrization**: combine combinatorial lower-bound engines (switching lemma, monotone approximation) with formalized proof obligations in Lean, restricting reliance on algebraic-oracle-friendly templates.

## 7) References

1. Baker, T. P., Gill, J., & Solovay, R. (1975). *Relativizations of the P =? NP question*. SIAM Journal on Computing, 4(4), 431–442.
2. Razborov, A. A. (1985). *Lower bounds on the monotone complexity of some Boolean functions*. Doklady Akademii Nauk SSSR, 281(4), 798–801.
3. Håstad, J. (1986). *Almost optimal lower bounds for small depth circuits*. In STOC 1986.
4. Smolensky, R. (1987). *Algebraic methods in the theory of lower bounds for Boolean circuit complexity*. In STOC 1987.
5. Razborov, A. A., & Rudich, S. (1994). *Natural proofs*. Journal of Computer and System Sciences, 55(1), 24–35.
6. Williams, R. (2011). *Nonuniform ACC circuit lower bounds*. Computational Complexity, 20(3), 437–472.
7. Aaronson, S., & Wigderson, A. (2009). *Algebrization: A new barrier in complexity theory*. ACM Transactions on Computation Theory, 1(1), Article 2.
8. Erdős, P., & Rado, R. (1960). *Intersection theorems for systems of sets*. Journal of the London Mathematical Society, 35(1), 85–90.
9. Schnorr, C. P. (1976). *A lower bound on the number of additions in monotone computations*.
