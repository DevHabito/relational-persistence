import RelationalPersistence.StarSharpEnergy
import RelationalPersistence.RealVectorBridge

/-!
# RP-F002: exact star residual in graph Euclidean norm

The fixed six-node star and the 1/10 update gain are exactly those in
RP-001. This proof isolates a classical finite-dimensional fact:
the worst-case twenty-step norm contraction on mean-zero real vectors
is (9/10)^20. The equality is *attained*, not just bounded.

The attainable-set supremum below is mathematically scoped to this graph,
this model and this horizon. It does not establish any physical law.
-/

namespace RelationalPersistence

def starSharpRatio : ℝ := (9 / 10 : ℝ) ^ 20

theorem starSharpRatio_nonneg : 0 ≤ starSharpRatio := by
  unfold starSharpRatio
  positivity

/-- A sharper bound than the earlier conservative three-twentieths bound. -/
theorem star_sharp_norm_upper (x : RealSixState)
    (hz : realTotal x = 0) :
    euclideanNorm (realIterate realStarStep 20 x) ≤
      starSharpRatio * euclideanNorm x := by
  have h := realStar_energy_power_bound 20 x hz
  have hcoeff : (81 / 100 : ℝ) ^ 20 = starSharpRatio ^ 2 := by
    norm_num [starSharpRatio]
  have ho := Real.sq_sqrt (realEnergy_nonneg (realIterate realStarStep 20 x))
  have hi := Real.sq_sqrt (realEnergy_nonneg x)
  have hlo : 0 ≤ euclideanNorm (realIterate realStarStep 20 x) := by
    unfold euclideanNorm
    positivity
  have hli : 0 ≤ euclideanNorm x := by
    unfold euclideanNorm
    positivity
  have hk : 0 ≤ starSharpRatio := starSharpRatio_nonneg
  rw [hcoeff] at h
  unfold euclideanNorm at hlo hli ⊢
  nlinarith

/-- The nonzero leaf-to-leaf mode attains the norm coefficient exactly. -/
theorem star_sharp_norm_attained :
    euclideanNorm (realIterate realStarStep 20 (starEigenLine 1)) =
      starSharpRatio * euclideanNorm (starEigenLine 1) := by
  rw [starEigenLine_iterate]
  have hsq : starSharpRatio ^ 2 =
      ((9 / 10 : ℝ) ^ 20) ^ 2 := rfl
  have ho : 0 ≤ euclideanNorm (starEigenLine ((9 / 10 : ℝ) ^ 20 * 1)) := by
    unfold euclideanNorm
    positivity
  have hi : 0 ≤ euclideanNorm (starEigenLine 1) := by
    unfold euclideanNorm
    positivity
  have hk : 0 ≤ starSharpRatio := starSharpRatio_nonneg
  have hs1 : euclideanNorm (starEigenLine ((9 / 10 : ℝ) ^ 20 * 1)) ^ 2 =
      2 * starSharpRatio ^ 2 := by
    unfold euclideanNorm
    rw [Real.sq_sqrt (realEnergy_nonneg _), starEigenLine_energy]
    simp [starSharpRatio]
  have hs2 : euclideanNorm (starEigenLine 1) ^ 2 = 2 := by
    unfold euclideanNorm
    rw [Real.sq_sqrt (realEnergy_nonneg _), starEigenLine_energy]
    norm_num
  nlinarith

/-- All graph vectors are covered by the finite-coordinate representation. -/
theorem graph_star_sharp_upper :
    isGraphTwentyStepBound realStarAdj starSharpRatio := by
  intro f hz
  let x := fromGraphVector f
  have hre : realCoordinates x = f := graph_coordinates_surjective f
  have hzero : realTotal x = 0 := (graph_zero_sum_iff f).mp hz
  have hiter : realGraphIterate realStarAdj 20 f =
      realCoordinates (realIterate realStarStep 20 x) := by
    rw [← hre]
    exact (real_star_iterate_matches_graph 20 x).symm
  have hleft : graphEuclideanNorm (realGraphIterate realStarAdj 20 f) =
      euclideanNorm (realIterate realStarStep 20 x) := by
    rw [hiter]
    exact graph_coordinate_norm _
  have hright : euclideanNorm x = graphEuclideanNorm f := by
    rw [← hre]
    exact (graph_coordinate_norm x).symm
  calc
    graphEuclideanNorm (realGraphIterate realStarAdj 20 f)
        = euclideanNorm (realIterate realStarStep 20 x) := hleft
    _ ≤ starSharpRatio * euclideanNorm x := star_sharp_norm_upper x hzero
    _ = starSharpRatio * graphEuclideanNorm f := by rw [hright]

/-- The sharp coefficient is reached by an admissible, nonzero graph state. -/
theorem graph_star_sharp_attained :
    ∃ f : Fin 6 → ℝ,
      (∑ v : Fin 6, f v) = 0 ∧ 0 < graphEuclideanNorm f ∧
      graphEuclideanNorm (realGraphIterate realStarAdj 20 f) =
        starSharpRatio * graphEuclideanNorm f := by
  let f := realCoordinates (starEigenLine 1)
  refine ⟨f, ?_, ?_, ?_⟩
  · change (∑ v : Fin 6, realCoordinates (starEigenLine 1) v) = 0
    rw [realCoordinates_realTotal, starEigenLine_zero_mean]
  · change 0 < graphEuclideanNorm (realCoordinates (starEigenLine 1))
    rw [graph_coordinate_norm]
    unfold euclideanNorm
    rw [starEigenLine_energy]
    norm_num
  · change graphEuclideanNorm (realGraphIterate realStarAdj 20
        (realCoordinates (starEigenLine 1))) =
        starSharpRatio * graphEuclideanNorm (realCoordinates (starEigenLine 1))
    rw [← real_star_iterate_matches_graph, graph_coordinate_norm,
        graph_coordinate_norm]
    exact star_sharp_norm_attained

/-- Achievable, nonzero, mean-zero twenty-step residual norm ratios. -/
def starResidualRatios : Set ℝ :=
  {r | ∃ f : Fin 6 → ℝ,
    (∑ v : Fin 6, f v) = 0 ∧
    0 < graphEuclideanNorm f ∧
    r * graphEuclideanNorm f =
      graphEuclideanNorm (realGraphIterate realStarAdj 20 f)}

theorem star_ratio_isGreatest :
    IsGreatest starResidualRatios starSharpRatio := by
  constructor
  · obtain ⟨f, hz, hp, heq⟩ := graph_star_sharp_attained
    exact ⟨f, hz, hp, heq.symm⟩
  · intro r hr
    obtain ⟨f, hz, hp, heq⟩ := hr
    have hu := graph_star_sharp_upper f hz
    rw [← heq] at hu
    nlinarith

theorem star_residual_supremum :
    sSup starResidualRatios = starSharpRatio := by
  exact star_ratio_isGreatest.csSup_eq

end RelationalPersistence
