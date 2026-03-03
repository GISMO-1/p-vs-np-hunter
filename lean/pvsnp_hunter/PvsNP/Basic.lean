import Mathlib

namespace PvsNP

abbrev BooleanFunction (n : ℕ) : Type := Fin (2 ^ n) → Bool
abbrev CircuitSize : Type := ℕ
abbrev CircuitDepth : Type := ℕ
abbrev DecisionProblem : Type := ℕ → Bool

def PolynomialTime (L : DecisionProblem) : Prop := ∃ k : ℕ, True

def NPClass : Set DecisionProblem := {L | ∃ k : ℕ, True}
def PClass : Set DecisionProblem := {L | PolynomialTime L}

end PvsNP
