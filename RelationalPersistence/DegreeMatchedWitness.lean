import RelationalPersistence.FiniteWitness

/-!
# RP-F003: equal-degree topology witness

Two connected six-vertex graphs have the same degree at every *labeled*
vertex, but a fixed zero-sum state evolves differently in one step.
This is an exact, conditional consensus counterexample. The separate
RP-F003-A01 exhaustive twenty-step Q20 result is not proved here.
-/

namespace RelationalPersistence

private def cycleWithLeafEdges : List (Nat × Nat) :=
  [(0, 3), (0, 4), (0, 5), (1, 2), (1, 4), (2, 3)]

private def triangleWithTailEdges : List (Nat × Nat) :=
  [(0, 2), (0, 3), (0, 4), (1, 4), (1, 5), (2, 3)]

private def undirectedAdj (edges : List (Nat × Nat))
    (v w : Fin 6) : ℚ :=
  if (v.val, w.val) ∈ edges ∨ (w.val, v.val) ∈ edges then 1 else 0

def matchedCycleAdj : Fin 6 → Fin 6 → ℚ :=
  undirectedAdj cycleWithLeafEdges

def matchedTriangleAdj : Fin 6 → Fin 6 → ℚ :=
  undirectedAdj triangleWithTailEdges

/-- Each labeled vertex has the same degree in the two graphs. -/
theorem matched_degrees_at_every_vertex (v : Fin 6) :
    (∑ w : Fin 6, matchedCycleAdj v w) =
      ∑ w : Fin 6, matchedTriangleAdj v w := by
  fin_cases v <;>
    norm_num [matchedCycleAdj, matchedTriangleAdj,
      undirectedAdj, cycleWithLeafEdges, triangleWithTailEdges,
      Fin.sum_univ_succ]

/-- A fixed mean-zero perturbation, identical in both networks. -/
def matchedInitial (v : Fin 6) : ℚ :=
  if v.val = 0 then 1 else if v.val = 2 then -1 else 0

theorem matched_initial_zero_mean :
    (∑ v : Fin 6, matchedInitial v) = 0 := by
  norm_num [matchedInitial, Fin.sum_univ_succ]

theorem matched_cycle_first_component :
    update matchedCycleAdj matchedInitial 0 = (7 / 10 : ℚ) := by
  norm_num [update, matchedCycleAdj, undirectedAdj,
    cycleWithLeafEdges, matchedInitial, Fin.sum_univ_succ]

theorem matched_triangle_first_component :
    update matchedTriangleAdj matchedInitial 0 = (3 / 5 : ℚ) := by
  norm_num [update, matchedTriangleAdj, undirectedAdj,
    triangleWithTailEdges, matchedInitial, Fin.sum_univ_succ]

/-- Degree equality and equal scalar inputs do not force identical updates. -/
theorem matched_degree_graphs_have_distinct_updates :
    (∀ v : Fin 6, (∑ w : Fin 6, matchedCycleAdj v w) =
      ∑ w : Fin 6, matchedTriangleAdj v w) ∧
    scalarIndex 1 (1 / 100) 1 = scalarIndex 1 (1 / 100) 1 ∧
    update matchedCycleAdj matchedInitial 0 ≠
      update matchedTriangleAdj matchedInitial 0 := by
  constructor
  · exact matched_degrees_at_every_vertex
  constructor
  · rfl
  · rw [matched_cycle_first_component, matched_triangle_first_component]
    norm_num

end RelationalPersistence
