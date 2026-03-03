"""Core Boolean circuit complexity models and lower-bound primitives."""

from .circuit import (
    BooleanCircuit,
    CircuitClass,
    Gate,
    GateType,
    validate_circuit_class,
)
from .switching_lemma import (
    DNF,
    decision_tree_depth,
    exact_depth_tail_probability,
    monte_carlo_depth_tail_probability,
    switching_lemma_upper_bound,
)

__all__ = [
    "BooleanCircuit",
    "CircuitClass",
    "Gate",
    "GateType",
    "validate_circuit_class",
    "DNF",
    "decision_tree_depth",
    "exact_depth_tail_probability",
    "monte_carlo_depth_tail_probability",
    "switching_lemma_upper_bound",
]
