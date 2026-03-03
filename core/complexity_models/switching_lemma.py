from __future__ import annotations

"""Håstad switching lemma utilities for bounded-width DNFs under random restrictions.

Reference theorem implemented:
Håstad, J. (1986). For width-w DNF/CNF F and random p-restriction rho,
Pr[ DT_depth(F|rho) >= t ] <= (5 p w)^t for p <= 1/2.

This module provides exact (for small n) and Monte-Carlo evaluation pipelines that
can be used as a verified lower-bound primitive for AC0 experiments.
"""

from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from random import Random
from typing import Dict, Mapping, Sequence, Tuple

Literal = Tuple[str, bool]  # (variable, polarity) where polarity=True means variable
Term = Tuple[Literal, ...]
Restriction = Dict[str, bool | None]


@dataclass(frozen=True)
class DNF:
    """A finite disjunction of conjunction terms over Boolean literals."""

    terms: Tuple[Term, ...]

    def variables(self) -> Tuple[str, ...]:
        vars_set = {var for term in self.terms for var, _ in term}
        return tuple(sorted(vars_set))

    def width(self) -> int:
        return max((len(term) for term in self.terms), default=0)

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return any(
            all(assignment[var] == polarity for var, polarity in term)
            for term in self.terms
        )

    def restrict(self, rho: Mapping[str, bool | None]) -> RestrictedDNF:
        restricted_terms: list[Term] = []
        has_true_term = False
        for term in self.terms:
            new_term: list[Literal] = []
            contradicted = False
            for var, polarity in term:
                fixed = rho.get(var)
                if fixed is None:
                    new_term.append((var, polarity))
                elif fixed != polarity:
                    contradicted = True
                    break
            if contradicted:
                continue
            if not new_term:
                has_true_term = True
                break
            restricted_terms.append(tuple(new_term))
        if has_true_term:
            return RestrictedDNF(constant=True, terms=())
        return RestrictedDNF(constant=None, terms=tuple(restricted_terms))


@dataclass(frozen=True)
class RestrictedDNF:
    constant: bool | None
    terms: Tuple[Term, ...]

    def variables(self) -> Tuple[str, ...]:
        vars_set = {var for term in self.terms for var, _ in term}
        return tuple(sorted(vars_set))

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        if self.constant is not None:
            return self.constant
        return any(
            all(assignment[var] == polarity for var, polarity in term)
            for term in self.terms
        )


def random_restriction(variables: Sequence[str], p: float, rng: Random) -> Restriction:
    rho: Restriction = {}
    for var in variables:
        r = rng.random()
        if r < p:
            rho[var] = None
        else:
            rho[var] = rng.choice((False, True))
    return rho


def exact_restriction_distribution(
    variables: Sequence[str], p: float
) -> Dict[Tuple[Tuple[str, bool | None], ...], float]:
    """Enumerate all restrictions with exact probability mass."""

    distribution: Dict[Tuple[Tuple[str, bool | None], ...], float] = {}
    per_var = [(None, p), (False, (1.0 - p) / 2.0), (True, (1.0 - p) / 2.0)]
    for values in product(per_var, repeat=len(variables)):
        prob = 1.0
        restriction_items: list[Tuple[str, bool | None]] = []
        for var, (val, val_prob) in zip(variables, values, strict=True):
            prob *= val_prob
            restriction_items.append((var, val))
        distribution[tuple(restriction_items)] = prob
    return distribution


def decision_tree_depth(restricted: RestrictedDNF) -> int:
    """Compute exact minimal decision tree depth by exhaustive recursion.

    Mathematical grounding: This computes the exact query complexity of the restricted
    function, which is the quantity bounded by Håstad's switching lemma.
    """

    vars_tuple = restricted.variables()
    if restricted.constant is not None or not vars_tuple:
        return 0

    @lru_cache(maxsize=None)
    def recurse(state: Tuple[Term, ...], variables: Tuple[str, ...]) -> int:
        current = RestrictedDNF(constant=None, terms=state)
        if not variables:
            values = [current.evaluate({})]
            return 0 if all(v == values[0] for v in values) else 0
        if _is_constant_on_cube(current, variables):
            return 0
        best = float("inf")
        for var in variables:
            remaining = tuple(v for v in variables if v != var)
            low = _restrict_state(state, {var: False})
            high = _restrict_state(state, {var: True})
            branch_depth = 1 + max(
                recurse(low.terms if low.constant is None else tuple(), remaining),
                recurse(high.terms if high.constant is None else tuple(), remaining),
            )
            best = min(best, branch_depth)
        return int(best)

    return recurse(restricted.terms, vars_tuple)


def switching_lemma_upper_bound(width: int, p: float, t: int) -> float:
    if t < 0:
        raise ValueError("t must be non-negative")
    if p < 0.0 or p > 1.0:
        raise ValueError("p must be in [0,1]")
    return (5.0 * p * width) ** t


def exact_depth_tail_probability(dnf: DNF, p: float, t: int) -> float:
    variables = dnf.variables()
    distribution = exact_restriction_distribution(variables, p)
    tail = 0.0
    for items, prob in distribution.items():
        rho = dict(items)
        depth = decision_tree_depth(dnf.restrict(rho))
        if depth >= t:
            tail += prob
    return tail


def monte_carlo_depth_tail_probability(
    dnf: DNF, p: float, t: int, trials: int, seed: int = 0
) -> float:
    rng = Random(seed)
    variables = dnf.variables()
    hits = 0
    for _ in range(trials):
        rho = random_restriction(variables, p, rng)
        if decision_tree_depth(dnf.restrict(rho)) >= t:
            hits += 1
    return hits / trials


def _restrict_state(
    state: Tuple[Term, ...], rho: Mapping[str, bool | None]
) -> RestrictedDNF:
    return DNF(state).restrict(rho)


def _is_constant_on_cube(restricted: RestrictedDNF, variables: Sequence[str]) -> bool:
    if restricted.constant is not None:
        return True
    values = set()
    for bits in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, bits, strict=True))
        values.add(restricted.evaluate(assignment))
        if len(values) > 1:
            return False
    return True
