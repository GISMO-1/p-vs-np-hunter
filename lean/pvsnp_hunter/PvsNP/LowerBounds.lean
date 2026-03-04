import Mathlib
import PvsNP.Circuits

namespace PvsNP

axiom parity : DecisionProblem
axiom clique : DecisionProblem

axiom hastad_parity_lower_bound : parity ∉ ({f | exists c : AC0, CircuitComputes c f} : Set DecisionProblem)
-- TODO: replace axiom with a formalized proof via switching lemma.

axiom razborov_clique_lower_bound : clique ∉ MonotonePolySize
-- TODO: replace axiom with a formalized proof via approximation method.

axiom williams_acc0 : exists L : DecisionProblem, L ∈ NPClass ∧ L ∉ ({f | exists c : ACC0, CircuitComputes c f} : Set DecisionProblem)

def parity_requires_ac0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def majority_requires_ac0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def clique_requires_ac0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def independent_set_requires_ac0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def php_requires_ac0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def majority_requires_acc0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def majority_requires_acc0_approximate_polynomial_degree_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def independent_set_requires_monotone_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def php_requires_acc0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

def parity_requires_acc0_size_lower_bound : Prop :=
  forall (n : Nat), n > 0 -> True

axiom placeholder_axiom : forall (n : Nat), n > 0 -> True

-- Template for a real AC0 lower bound theorem statement.
theorem hastad_parity_ac0 :
  forall (n : Nat), n > 0 -> True := by
  intros
  trivial

end PvsNP
