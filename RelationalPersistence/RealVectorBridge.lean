import RelationalPersistence.RealGraphBridge
import RelationalPersistence.RealResidualNorm

/-!
# RP-F001: Complete finite-coordinate interpretation over real vectors

This module supplies explicit inverses between a six-coordinate state and
`Fin 6 → ℝ`. The energy is exactly the squared Euclidean coordinate norm.
The graph updates are the same synchronous Laplacian recurrences proved in
`RealGraphBridge`, and the horizon is the pre-registered twenty steps.

The result is conditional classical graph consensus mathematics. It makes
no empirical inference, new physical-law claim, or novelty claim.
-/

namespace RelationalPersistence

/-- Every real-valued vector on six labeled vertices has a six-field state. -/
def fromGraphVector (f : Fin 6 → ℝ) : RealSixState :=
  ⟨f 0, f 1, f 2, f 3, f 4, f 5⟩

theorem graph_coordinates_surjective (f : Fin 6 → ℝ) :
    realCoordinates (fromGraphVector f) = f := by
  funext v
  fin_cases v <;> simp [realCoordinates, fromGraphVector]

theorem graph_coordinates_injective (x : RealSixState) :
    fromGraphVector (realCoordinates x) = x := by
  cases x
  rfl

theorem graph_coordinate_energy (x : RealSixState) :
    (∑ v : Fin 6, (realCoordinates x v) ^ 2) = realEnergy x := by
  norm_num [realCoordinates, realEnergy, Fin.sum_univ_succ]
  ring

noncomputable def graphEuclideanNorm (f : Fin 6 → ℝ) : ℝ :=
  Real.sqrt (∑ v : Fin 6, (f v) ^ 2)

theorem graph_coordinate_norm (x : RealSixState) :
    graphEuclideanNorm (realCoordinates x) = euclideanNorm x := by
  unfold graphEuclideanNorm euclideanNorm
  rw [graph_coordinate_energy]

theorem graph_zero_sum_iff (f : Fin 6 → ℝ) :
    (∑ v : Fin 6, f v) = 0 ↔ realTotal (fromGraphVector f) = 0 := by
  have hs := realCoordinates_realTotal (fromGraphVector f)
  rw [graph_coordinates_surjective] at hs
  rw [hs]

/-- A graph-level worst-case residual bound for the exact finite dynamics. -/
def isGraphTwentyStepBound (adj : Fin 6 → Fin 6 → ℝ) (bound : ℝ) : Prop :=
  ∀ f : Fin 6 → ℝ, (∑ v : Fin 6, f v) = 0 →
    graphEuclideanNorm (realGraphIterate adj 20 f) ≤
      bound * graphEuclideanNorm f

theorem graph_star_twenty_uniform_bound :
    isGraphTwentyStepBound realStarAdj (3/20 : ℝ) := by
  intro f hz
  let x : RealSixState := fromGraphVector f
  have hrepr : realCoordinates x = f := graph_coordinates_surjective f
  have hzero : realTotal x = 0 := (graph_zero_sum_iff f).mp hz
  have hiter : realGraphIterate realStarAdj 20 f =
      realCoordinates (realIterate realStarStep 20 x) := by
    rw [← hrepr]
    exact (real_star_iterate_matches_graph 20 x).symm
  have hleft : graphEuclideanNorm (realGraphIterate realStarAdj 20 f) =
      euclideanNorm (realIterate realStarStep 20 x) := by
    rw [hiter]
    exact graph_coordinate_norm _
  have hright : euclideanNorm x = graphEuclideanNorm f := by
    rw [← hrepr]
    exact (graph_coordinate_norm x).symm
  calc
    graphEuclideanNorm (realGraphIterate realStarAdj 20 f)
        = euclideanNorm (realIterate realStarStep 20 x) := hleft
    _ ≤ (3/20 : ℝ) * euclideanNorm x := star_twenty_norm_bound x hzero
    _ = (3/20 : ℝ) * graphEuclideanNorm f := by rw [hright]

/-- A mean-zero graph vector with a 20-step ratio exceeding 1/5. -/
theorem graph_path_twenty_witness :
    (1/5 : ℝ) * graphEuclideanNorm (realCoordinates realPathStart) <
      graphEuclideanNorm (realGraphIterate realPathAdj 20
        (realCoordinates realPathStart)) := by
  have h := path_twenty_norm_witness
  have hiter := real_path_iterate_matches_graph 20 realPathStart
  rw [← hiter, graph_coordinate_norm, graph_coordinate_norm]
  exact h

theorem every_graph_path_bound_exceeds_fifth (r : ℝ)
    (h : isGraphTwentyStepBound realPathAdj r) : (1/5 : ℝ) < r := by
  have hW := graph_path_twenty_witness
  have hz : (∑ v : Fin 6, realCoordinates realPathStart v) = 0 := by
    rw [realCoordinates_realTotal, realPath_start_mean_zero]
  have hR := h (realCoordinates realPathStart) hz
  have hpositive : 0 < graphEuclideanNorm (realCoordinates realPathStart) := by
    rw [graph_coordinate_norm]
    unfold euclideanNorm
    rw [realPath_start_energy]
    positivity
  have hstrict : (1/5 : ℝ) * graphEuclideanNorm (realCoordinates realPathStart) <
      r * graphEuclideanNorm (realCoordinates realPathStart) :=
    lt_of_lt_of_le hW hR
  nlinarith

/-- Every uniform real path residual bound exceeds the proven star bound
by strictly more than the registered numerical decision threshold 0.05. -/
theorem rp001_graph_worst_case_gap (r : ℝ)
    (h : isGraphTwentyStepBound realPathAdj r) :
    (1/20 : ℝ) < r - (3/20 : ℝ) := by
  have hp := every_graph_path_bound_exceeds_fifth r h
  linarith

end RelationalPersistence
