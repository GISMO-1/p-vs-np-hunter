from core.complexity_models.switching_lemma import (
    DNF,
    decision_tree_depth,
    exact_depth_tail_probability,
    monte_carlo_depth_tail_probability,
    switching_lemma_upper_bound,
)


def test_decision_tree_depth_simple_dnf() -> None:
    # f = x1 OR x2 has deterministic query depth 2 in the worst case
    dnf = DNF(terms=((("x1", True),), (("x2", True),)))
    assert decision_tree_depth(dnf.restrict({"x1": None, "x2": None})) == 2


def test_switching_lemma_bound_holds_on_small_exact_instance() -> None:
    # width-2 DNF over 3 vars
    dnf = DNF(terms=((("x1", True), ("x2", True)), (("x2", False), ("x3", True))))
    p = 0.1
    t = 2
    empirical = exact_depth_tail_probability(dnf, p=p, t=t)
    bound = switching_lemma_upper_bound(width=dnf.width(), p=p, t=t)
    assert empirical <= bound + 1e-12


def test_monte_carlo_agrees_with_exact_on_small_formula() -> None:
    dnf = DNF(terms=((("x1", True),), (("x2", True), ("x3", False))))
    p = 0.2
    t = 1
    exact = exact_depth_tail_probability(dnf, p=p, t=t)
    mc = monte_carlo_depth_tail_probability(dnf, p=p, t=t, trials=5000, seed=7)
    assert abs(exact - mc) < 0.05


def test_switching_bound_input_validation() -> None:
    try:
        switching_lemma_upper_bound(width=2, p=1.5, t=1)
        assert False, "expected ValueError"
    except ValueError:
        pass
