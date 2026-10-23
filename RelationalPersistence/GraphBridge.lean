import RelationalPersistence.TwentyStep

/-!
# Coordinate-to-graph correspondence

This module ties the explicit six-coordinate maps used by the rational
certificate to the original combinatorial-Laplacian update function.
It does not interpret the coordinates as empirical measurements.
-/
namespace RelationalPersistence

def coordinates (x : SixState) (v : Fin 6) : ℚ :=
  if v.val = 0 then x.a
  else if v.val = 1 then x.b
  else if v.val = 2 then x.c
  else if v.val = 3 then x.d
  else if v.val = 4 then x.e
  else x.f

theorem coordinates_total (x : SixState) :
    (∑ v : Fin 6, coordinates x v) = total x := by
  norm_num [coordinates, total, Fin.sum_univ_succ]
  ring

theorem path_step_matches_graph (x : SixState) (v : Fin 6) :
    coordinates (pathStep x) v = update pathAdj (coordinates x) v := by
  fin_cases v <;>
    norm_num [coordinates, pathStep, update, pathAdj, Fin.sum_univ_succ] <;>
    ring

theorem star_step_matches_graph (x : SixState) (v : Fin 6) :
    coordinates (starStep x) v = update starAdj (coordinates x) v := by
  fin_cases v <;>
    norm_num [coordinates, starStep, update, starAdj, Fin.sum_univ_succ] <;>
    ring

def graphIterate (adj : Fin 6 → Fin 6 → ℚ) :
    Nat → (Fin 6 → ℚ) → (Fin 6 → ℚ)
  | 0, x => x
  | n + 1, x => fun v => update adj (graphIterate adj n x) v

theorem path_iterate_matches_graph (n : Nat) (x : SixState) :
    coordinates (iterate pathStep n x) =
      graphIterate pathAdj n (coordinates x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      funext v
      change coordinates (pathStep (iterate pathStep n x)) v =
        update pathAdj (graphIterate pathAdj n (coordinates x)) v
      rw [path_step_matches_graph, ih]

theorem star_iterate_matches_graph (n : Nat) (x : SixState) :
    coordinates (iterate starStep n x) =
      graphIterate starAdj n (coordinates x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      funext v
      change coordinates (starStep (iterate starStep n x)) v =
        update starAdj (graphIterate starAdj n (coordinates x)) v
      rw [star_step_matches_graph, ih]

end RelationalPersistence
