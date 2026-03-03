import Mathlib
import PvsNP.Basic

namespace PvsNP

inductive AC0 where
  | mk (size depth : ℕ)

inductive MonotoneCircuit where
  | mk (size depth : ℕ)

inductive ACC0 where
  | mk (size depth modulus : ℕ)

def CircuitComputes {α : Type} (c : α) (f : DecisionProblem) : Prop := True

def CircuitComplexity (f : DecisionProblem) : ℕ := 0

def MonotonePolySize : Set DecisionProblem := {f | ∃ k : ℕ, True}

end PvsNP
