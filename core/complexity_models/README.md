# core/complexity_models

Boolean circuit simulator for AC0, monotone, and ACC0 classes, with an exact lower-bound primitive based on Håstad's switching lemma.

## Implemented components
- `circuit.py`: gate-level circuit DAG evaluator, truth tables, size/depth, and class validators.
- `switching_lemma.py`: DNF random restriction machinery, exact decision tree depth computation, exact/Monte Carlo tail probability estimation, and the theorem upper bound `(5pw)^t`.

## References
- Håstad (1986): AC0 lower bounds and switching lemma.
- Razborov (1985): monotone lower bounds.
- Smolensky (1987): ACC0 / modular gate landscape.
