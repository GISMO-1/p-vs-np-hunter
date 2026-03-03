# SAT Oracle Agent

Generates SAT benchmarks (random, planted, Tseitin, pigeonhole), solves them via DPLL/CaDiCaL, computes hardness fingerprints, and predicts hardness.

## Interface
- `generate(instance_type, n_vars, **kwargs) -> SATInstance`
- `solve(instance) -> SolveResult`
- `fingerprint(instance) -> HardnessFingerprint`
- `predict_hardness(instance) -> HardnessPrediction`
- `handle_message(message)` follows repository-wide agent schema.

## Mathematical references
- Cook 1971 (SAT as NP-complete baseline)
- Tseitin 1968 (graph contradiction formulas)
- Ben-Sasson/Wigderson 2001 (resolution hardness proxies)
