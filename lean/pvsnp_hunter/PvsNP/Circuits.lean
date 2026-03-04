import Mathlib
import PvsNP.Basic

namespace PvsNP

inductive AC0 where
  | mk (size depth : Nat)

inductive MonotoneCircuit where
  | mk (size depth : Nat)

inductive ACC0 where
  | mk (size depth modulus : Nat)

def CircuitComputes {a : Type} (_c : a) (_f : DecisionProblem) : Prop := True

def CircuitComplexity (_f : DecisionProblem) : Nat := 0

def MonotonePolySize : Set DecisionProblem := {f | exists k : Nat, True}

end PvsNP
