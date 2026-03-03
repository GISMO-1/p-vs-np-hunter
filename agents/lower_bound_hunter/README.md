# lower_bound_hunter

Implements computational lower-bound workflows around four classical techniques:

- Williams algorithms-to-lower-bounds pipeline (Williams 2011; Gödel Prize 2024).
- Gate elimination for small fan-in formulas (Schnorr 1976; Paul 1977).
- Monotone approximation method for CLIQUE (Razborov 1985; Erdős-Rado 1960 sunflower lemma).
- Random restrictions / switching-lemma experiments (Håstad 1986).

## Interface

- `hunt(circuit_class: CircuitModel, target_function: str) -> LowerBoundResult`
- `validate_known_results() -> ValidationReport`
- `handle_message(msg: dict) -> dict`

Results are persisted under `data/lower_bounds/`.
