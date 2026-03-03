# Circuit Explorer Agent

This agent computes circuit complexity profiles of Boolean functions over the implemented classes in `core/complexity_models` (AC0, monotone, ACC0), and writes reproducible JSON reports to `data/circuit_families/`.

## Mathematical scope

The implementation is grounded in the following classical results:

- **AC0 switching behavior**: Håstad, *Almost optimal lower bounds for small depth circuits* (STOC 1986).
- **Monotone lower-bound framework**: Razborov, *Lower bounds on monotone complexity* (1985).
- **ACC0 with modular gates**: Smolensky, *Algebraic methods in Boolean circuit complexity* (STOC 1987).
- **Majority in threshold circuits (TC0 context for test oracle)**: Siu–Bruck–Kailath (1995).

The switching-lemma check in reports is a theoretical cross-check, computed from exact DNF restrictions using `core/complexity_models/switching_lemma.py`.

## What it computes

For each requested model class:

1. Enumerates circuits up to configured size/depth constraints.
2. Finds minimum size witness for the target function (when found).
3. Computes structural invariants:
   - symmetry group size (exact for small `n`),
   - gate elimination candidates,
   - locality score,
   - depth-size tradeoff map.
4. Serializes a full report with metadata and timestamp.

## API

- `explore(function: BooleanFunction, models: list[CircuitModel]) -> CircuitReport`
- `CircuitExplorerAgent.handle_message(message)` enforces the repository inter-agent schema.

## Running tests

```bash
pytest agents/circuit_explorer/tests -q
```
