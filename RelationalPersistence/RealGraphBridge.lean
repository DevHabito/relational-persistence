import RelationalPersistence.RealTwentyStep
import RelationalPersistence.GraphBridge

/-!
# Real graph correspondence for RP-F001

This declares the same unweighted path and star adjacency on Fin 6,
now over real scalars, and checks the exact correspondence between
Laplacian updates and the certified twenty-step state recurrences.
The operation is a synchronous step with gain 1/10; no empirical
calibration is inferred from this correspondence.
-/

namespace RelationalPersistence

def realPathAdj (v w : Fin 6) : ℝ :=
  if v.val + 1 = w.val ∨ w.val + 1 = v.val then 1 else 0

def realStarAdj (v w : Fin 6) : ℝ :=
  if (v.val = 0 ∧ w.val ≠ 0) ∨ (w.val = 0 ∧ v.val ≠ 0) then 1 else 0

theorem realPathAdj_matches_rational (v w : Fin 6) :
    realPathAdj v w = (pathAdj v w : ℝ) := by
  simp [realPathAdj, pathAdj]

theorem realStarAdj_matches_rational (v w : Fin 6) :
    realStarAdj v w = (starAdj v w : ℝ) := by
  simp [realStarAdj, starAdj]

def realUpdate (adj : Fin 6 → Fin 6 → ℝ)
    (x : Fin 6 → ℝ) (v : Fin 6) : ℝ :=
  x v - (1 / 10 : ℝ) * ∑ w : Fin 6, adj v w * (x v - x w)

def realCoordinates (x : RealSixState) (v : Fin 6) : ℝ :=
  if v.val = 0 then x.a
  else if v.val = 1 then x.b
  else if v.val = 2 then x.c
  else if v.val = 3 then x.d
  else if v.val = 4 then x.e
  else x.f

theorem realCoordinates_realTotal (x : RealSixState) :
    (∑ v : Fin 6, realCoordinates x v) = realTotal x := by
  norm_num [realCoordinates, realTotal, Fin.sum_univ_succ]
  ring

theorem real_path_step_matches_graph (x : RealSixState) (v : Fin 6) :
    realCoordinates (realPathStep x) v = realUpdate realPathAdj (realCoordinates x) v := by
  fin_cases v <;>
    norm_num [realCoordinates, realPathStep, realUpdate, realPathAdj, Fin.sum_univ_succ] <;>
    ring

theorem real_star_step_matches_graph (x : RealSixState) (v : Fin 6) :
    realCoordinates (realStarStep x) v = realUpdate realStarAdj (realCoordinates x) v := by
  fin_cases v <;>
    norm_num [realCoordinates, realStarStep, realUpdate, realStarAdj, Fin.sum_univ_succ] <;>
    ring

def realGraphIterate (adj : Fin 6 → Fin 6 → ℝ) :
    Nat → (Fin 6 → ℝ) → (Fin 6 → ℝ)
  | 0, x => x
  | n + 1, x => fun v => realUpdate adj (realGraphIterate adj n x) v

theorem real_path_iterate_matches_graph (n : Nat) (x : RealSixState) :
    realCoordinates (realIterate realPathStep n x) =
      realGraphIterate realPathAdj n (realCoordinates x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      funext v
      change realCoordinates (realPathStep (realIterate realPathStep n x)) v =
        realUpdate realPathAdj (realGraphIterate realPathAdj n (realCoordinates x)) v
      rw [real_path_step_matches_graph, ih]

theorem real_star_iterate_matches_graph (n : Nat) (x : RealSixState) :
    realCoordinates (realIterate realStarStep n x) =
      realGraphIterate realStarAdj n (realCoordinates x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      funext v
      change realCoordinates (realStarStep (realIterate realStarStep n x)) v =
        realUpdate realStarAdj (realGraphIterate realStarAdj n (realCoordinates x)) v
      rw [real_star_step_matches_graph, ih]

end RelationalPersistence
