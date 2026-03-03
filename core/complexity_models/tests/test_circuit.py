from core.complexity_models.circuit import (
    BooleanCircuit,
    CircuitClass,
    Gate,
    GateType,
    validate_circuit_class,
)


def test_ac0_circuit_xor_via_and_or_not_truth_table() -> None:
    gates = [
        Gate("x1", GateType.INPUT),
        Gate("x2", GateType.INPUT),
        Gate("nx1", GateType.NOT, ("x1",)),
        Gate("nx2", GateType.NOT, ("x2",)),
        Gate("a", GateType.AND, ("x1", "nx2")),
        Gate("b", GateType.AND, ("nx1", "x2")),
        Gate("out", GateType.OR, ("a", "b")),
    ]
    c = BooleanCircuit(gates, "out")
    validate_circuit_class(c, CircuitClass.AC0)
    table = c.truth_table()
    assert table[(False, False)] is False
    assert table[(False, True)] is True
    assert table[(True, False)] is True
    assert table[(True, True)] is False
    assert c.depth() == 3


def test_monotone_validation_rejects_not_gate() -> None:
    gates = [
        Gate("x", GateType.INPUT),
        Gate("nx", GateType.NOT, ("x",)),
    ]
    c = BooleanCircuit(gates, "nx")
    try:
        validate_circuit_class(c, CircuitClass.MONOTONE)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Monotone" in str(exc)


def test_acc0_mod_gate_parity() -> None:
    gates = [
        Gate("x1", GateType.INPUT),
        Gate("x2", GateType.INPUT),
        Gate("x3", GateType.INPUT),
        Gate("parity", GateType.MOD, ("x1", "x2", "x3"), modulus=2, residue=1),
    ]
    c = BooleanCircuit(gates, "parity")
    validate_circuit_class(c, CircuitClass.ACC0)
    assert c.evaluate({"x1": False, "x2": False, "x3": False}) is False
    assert c.evaluate({"x1": True, "x2": False, "x3": False}) is True
    assert c.evaluate({"x1": True, "x2": True, "x3": False}) is False


def test_invalid_reference_is_rejected() -> None:
    gates = [Gate("x", GateType.INPUT), Gate("bad", GateType.AND, ("x", "y"))]
    try:
        BooleanCircuit(gates, "bad")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown" in str(exc)
