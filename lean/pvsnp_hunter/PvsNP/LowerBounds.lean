import Mathlib
import PvsNP.Circuits

namespace PvsNP

axiom parity : DecisionProblem
axiom clique : DecisionProblem

axiom hastad_parity_lower_bound : parity ∉ ({f | ∃ c : AC0, CircuitComputes c f} : Set DecisionProblem)
-- TODO: replace axiom with a formalized proof via switching lemma.

axiom razborov_clique_lower_bound : clique ∉ MonotonePolySize
-- TODO: replace axiom with a formalized proof via approximation method.

axiom williams_acc0 : ∃ L : DecisionProblem, L ∈ NPClass ∧ L ∉ ({f | ∃ c : ACC0, CircuitComputes c f} : Set DecisionProblem)

end PvsNP
