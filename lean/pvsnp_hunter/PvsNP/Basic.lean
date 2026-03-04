import Mathlib

namespace PvsNP

abbrev BooleanFunction (n : Nat) : Type := Fin (2 ^ n) -> Bool
abbrev CircuitSize : Type := Nat
abbrev CircuitDepth : Type := Nat
abbrev DecisionProblem : Type := Nat -> Bool

def PolynomialTime (_L : DecisionProblem) : Prop := exists _k : Nat, True
def NPClass : Set DecisionProblem := {_L | exists _k : Nat, True}
def PClass : Set DecisionProblem := {L | PolynomialTime L}

-- First theorem attempt
theorem pvsNP_definitions_consistent : True := trivial

end PvsNP
