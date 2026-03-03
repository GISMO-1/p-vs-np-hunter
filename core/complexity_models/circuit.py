from __future__ import annotations

"""Boolean circuit models for AC0, monotone, and ACC0.

Mathematical background:
- AC0 and parity lower bounds: Håstad, J. (1986), "Almost optimal lower bounds for small depth circuits".
- ACC0 and modular gates: Razborov-Smolensky method overview in Smolensky (1987).
- Monotone circuits and lower bounds: Razborov (1985) monotone complexity of CLIQUE.
"""

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

Assignment = Mapping[str, bool]


class GateType(str, Enum):
    """Supported Boolean gate families for restricted circuit classes."""

    INPUT = "INPUT"
    CONST = "CONST"
    NOT = "NOT"
    AND = "AND"
    OR = "OR"
    MOD = "MOD"


@dataclass(frozen=True)
class Gate:
    """Immutable gate description.

    For MOD gates, `modulus` and `residue` define acceptance by
    sum(inputs) % modulus == residue.
    """

    name: str
    gate_type: GateType
    inputs: Tuple[str, ...] = ()
    value: bool | None = None
    modulus: int | None = None
    residue: int = 0


class BooleanCircuit:
    """Executable Boolean circuit DAG with explicit output gate."""

    def __init__(self, gates: Sequence[Gate], output_gate: str):
        self._gate_map: Dict[str, Gate] = {g.name: g for g in gates}
        if len(self._gate_map) != len(gates):
            raise ValueError("Gate names must be unique")
        if output_gate not in self._gate_map:
            raise ValueError(f"Unknown output gate '{output_gate}'")
        self.output_gate = output_gate
        self._validate_references()

    @property
    def gates(self) -> Mapping[str, Gate]:
        return self._gate_map

    def input_variables(self) -> List[str]:
        return sorted(
            gate.name
            for gate in self._gate_map.values()
            if gate.gate_type == GateType.INPUT
        )

    def evaluate(self, assignment: Assignment) -> bool:
        memo: Dict[str, bool] = {}

        def eval_gate(name: str) -> bool:
            if name in memo:
                return memo[name]
            gate = self._gate_map[name]
            if gate.gate_type == GateType.INPUT:
                if name not in assignment:
                    raise ValueError(f"Missing input assignment for '{name}'")
                result = bool(assignment[name])
            elif gate.gate_type == GateType.CONST:
                if gate.value is None:
                    raise ValueError(f"CONST gate '{name}' missing value")
                result = gate.value
            elif gate.gate_type == GateType.NOT:
                self._assert_arity(gate, 1)
                result = not eval_gate(gate.inputs[0])
            elif gate.gate_type == GateType.AND:
                result = all(eval_gate(i) for i in gate.inputs)
            elif gate.gate_type == GateType.OR:
                result = any(eval_gate(i) for i in gate.inputs)
            elif gate.gate_type == GateType.MOD:
                if gate.modulus is None or gate.modulus <= 0:
                    raise ValueError(f"MOD gate '{name}' needs positive modulus")
                s = sum(1 for i in gate.inputs if eval_gate(i))
                result = (s % gate.modulus) == gate.residue
            else:
                raise ValueError(f"Unsupported gate type: {gate.gate_type}")
            memo[name] = result
            return result

        return eval_gate(self.output_gate)

    def truth_table(self) -> Dict[Tuple[bool, ...], bool]:
        variables = self.input_variables()
        table: Dict[Tuple[bool, ...], bool] = {}
        for bits in product((False, True), repeat=len(variables)):
            assignment = dict(zip(variables, bits, strict=True))
            table[bits] = self.evaluate(assignment)
        return table

    def depth(self) -> int:
        memo: Dict[str, int] = {}

        def node_depth(name: str) -> int:
            if name in memo:
                return memo[name]
            gate = self._gate_map[name]
            if gate.gate_type in (GateType.INPUT, GateType.CONST):
                memo[name] = 0
                return 0
            child_depth = max((node_depth(c) for c in gate.inputs), default=0)
            memo[name] = child_depth + 1
            return memo[name]

        return node_depth(self.output_gate)

    def size(self) -> int:
        return len(self._gate_map)

    def _assert_arity(self, gate: Gate, arity: int) -> None:
        if len(gate.inputs) != arity:
            raise ValueError(
                f"Gate '{gate.name}' has arity {len(gate.inputs)} expected {arity}"
            )

    def _validate_references(self) -> None:
        for gate in self._gate_map.values():
            for input_name in gate.inputs:
                if input_name not in self._gate_map:
                    raise ValueError(f"Gate '{gate.name}' references unknown '{input_name}'")


class CircuitClass(str, Enum):
    AC0 = "AC0"
    MONOTONE = "MONOTONE"
    ACC0 = "ACC0"


def validate_circuit_class(circuit: BooleanCircuit, cls: CircuitClass) -> None:
    """Validate class membership by syntactic gate constraints.

    The constraints model standard definitions used in Håstad (AC0),
    Razborov (monotone), and Razborov-Smolensky (ACC0 with MOD_m gates).
    """

    gates = circuit.gates.values()
    if cls == CircuitClass.AC0:
        allowed = {GateType.INPUT, GateType.CONST, GateType.NOT, GateType.AND, GateType.OR}
        for gate in gates:
            if gate.gate_type not in allowed:
                raise ValueError(f"AC0 forbids gate type {gate.gate_type}")
    elif cls == CircuitClass.MONOTONE:
        allowed = {GateType.INPUT, GateType.CONST, GateType.AND, GateType.OR}
        for gate in gates:
            if gate.gate_type not in allowed:
                raise ValueError(f"Monotone circuits forbid gate type {gate.gate_type}")
    elif cls == CircuitClass.ACC0:
        allowed = {
            GateType.INPUT,
            GateType.CONST,
            GateType.NOT,
            GateType.AND,
            GateType.OR,
            GateType.MOD,
        }
        for gate in gates:
            if gate.gate_type not in allowed:
                raise ValueError(f"ACC0 forbids gate type {gate.gate_type}")
    else:
        raise ValueError(f"Unknown class {cls}")
