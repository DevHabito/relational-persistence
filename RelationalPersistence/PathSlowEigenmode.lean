import RelationalPersistence.RealVectorBridge

/-!
# RP-F002: an exact slow eigenmode of the path P6

The classical path-graph Laplacian has eigenvalue 2 - sqrt(3) on a
non-consensus mode. This file proves an explicit eigenmode for the
fixed RP-001 synchronous update W = Id - L/10 on real six-vectors.

An exact *attained lower bound* is not the exact worst-case operator norm.
Proving that this is the largest modulus among all non-consensus modes
remains a separate obligation. No physical law is claimed.
-/

namespace RelationalPersistence

noncomputable def pathSlowGain : ℝ :=
  (8 + Real.sqrt 3) / 10

noncomputable def pathSlowLine (c : ℝ) : RealSixState :=
  ⟨c, (Real.sqrt 3 - 1) * c, (2 - Real.sqrt 3) * c,
   (Real.sqrt 3 - 2) * c, (1 - Real.sqrt 3) * c, -c⟩

theorem pathSlowLine_zero_mean (c : ℝ) :
    realTotal (pathSlowLine c) = 0 := by
  unfold realTotal pathSlowLine
  ring

theorem pathSlowGain_nonneg : 0 ≤ pathSlowGain := by
  unfold pathSlowGain
  positivity

/-- An explicit exact eigenmode, avoiding numerical eigensolvers. -/
theorem pathSlowLine_step (c : ℝ) :
    realPathStep (pathSlowLine c) =
      pathSlowLine (pathSlowGain * c) := by
  have hs : (Real.sqrt (3 : ℝ)) ^ 2 = 3 := by norm_num
  have hsc : c * (Real.sqrt (3 : ℝ)) ^ 2 = 3 * c := by
    rw [hs]
    ring
  unfold realPathStep pathSlowLine pathSlowGain
  congr 1 <;> nlinarith [hsc]

theorem pathSlowLine_iterate (n : Nat) (c : ℝ) :
    realIterate realPathStep n (pathSlowLine c) =
      pathSlowLine (pathSlowGain ^ n * c) := by
  induction n with
  | zero =>
      simp [realIterate]
  | succ n ih =>
      change realPathStep (realIterate realPathStep n (pathSlowLine c)) =
        pathSlowLine (pathSlowGain ^ (n + 1) * c)
      rw [ih, pathSlowLine_step]
      congr 1
      rw [pow_succ]
      ring

theorem pathSlowLine_energy_scale (c : ℝ) :
    realEnergy (pathSlowLine c) =
      c ^ 2 * realEnergy (pathSlowLine 1) := by
  unfold realEnergy pathSlowLine
  ring

theorem pathSlowLine_nonzero :
    0 < realEnergy (pathSlowLine 1) := by
  unfold realEnergy pathSlowLine
  positivity

theorem pathSlowLine_norm_scale (c : ℝ) :
    euclideanNorm (pathSlowLine c) =
      |c| * euclideanNorm (pathSlowLine 1) := by
  unfold euclideanNorm
  rw [pathSlowLine_energy_scale]
  rw [Real.sqrt_mul (sq_nonneg _), Real.sqrt_sq_eq_abs]

theorem path_slow_twenty_norm_attained :
    euclideanNorm (realIterate realPathStep 20 (pathSlowLine 1)) =
      pathSlowGain ^ 20 * euclideanNorm (pathSlowLine 1) := by
  rw [pathSlowLine_iterate, pathSlowLine_norm_scale]
  simp only [mul_one]
  rw [abs_of_nonneg (pow_nonneg pathSlowGain_nonneg 20)]

/-- The exact slow-mode ratio is attained by a valid nonzero graph vector. -/
theorem graph_path_slow_witness :
    ∃ f : Fin 6 → ℝ,
      (∑ v : Fin 6, f v) = 0 ∧
      0 < graphEuclideanNorm f ∧
      graphEuclideanNorm (realGraphIterate realPathAdj 20 f) =
        pathSlowGain ^ 20 * graphEuclideanNorm f := by
  let f := realCoordinates (pathSlowLine 1)
  refine ⟨f, ?_, ?_, ?_⟩
  · change (∑ v : Fin 6, realCoordinates (pathSlowLine 1) v) = 0
    rw [realCoordinates_realTotal, pathSlowLine_zero_mean]
  · change 0 < graphEuclideanNorm (realCoordinates (pathSlowLine 1))
    rw [graph_coordinate_norm]
    unfold euclideanNorm
    exact Real.sqrt_pos.2 pathSlowLine_nonzero
  · change graphEuclideanNorm (realGraphIterate realPathAdj 20
        (realCoordinates (pathSlowLine 1))) =
        pathSlowGain ^ 20 * graphEuclideanNorm (realCoordinates (pathSlowLine 1))
    rw [← real_path_iterate_matches_graph, graph_coordinate_norm,
        graph_coordinate_norm]
    exact path_slow_twenty_norm_attained

end RelationalPersistence
