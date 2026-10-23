import RelationalPersistence.RealTwentyStep

/-!
# RP-F001: worst-case Euclidean norm consequences over real states

The registered deterministic observable is the largest Euclidean norm ratio
after twenty synchronous updates on the mean-zero subspace.
Rather than silently using a rational supremum, we quantify over **all**
real states and characterize uniform bounds directly.

A path state with ratio > 1/5 implies that every uniform path bound
exceeds 1/5. The star has the uniform upper bound 3/20.
These statements jointly imply a worst-case gap > 1/20, conditional
on the correspondence of these maps with the registered graph updates.

This is a theorem about a declared classical consensus model, not new physics.
-/

namespace RelationalPersistence

def euclideanNorm (x : RealSixState) : ℝ :=
  Real.sqrt (realEnergy x)

def isTwentyStepBound (step : RealSixState → RealSixState)
    (bound : ℝ) : Prop :=
  ∀ x : RealSixState, realTotal x = 0 →
    euclideanNorm (realIterate step 20 x) ≤ bound * euclideanNorm x

theorem star_twenty_norm_bound :
    isTwentyStepBound realStarStep (3/20 : ℝ) := by
  intro x hz
  have h := realStar_twenty_uniform_bound x hz
  have ho := Real.sq_sqrt (realEnergy_nonneg (realIterate realStarStep 20 x))
  have hi := Real.sq_sqrt (realEnergy_nonneg x)
  have hno : 0 ≤ Real.sqrt (realEnergy (realIterate realStarStep 20 x)) :=
    Real.sqrt_nonneg _
  have hni : 0 ≤ Real.sqrt (realEnergy x) := Real.sqrt_nonneg _
  unfold euclideanNorm
  nlinarith

theorem path_twenty_norm_witness :
    (1/5 : ℝ) * euclideanNorm realPathStart <
      euclideanNorm (realIterate realPathStep 20 realPathStart) := by
  have h := realPath_twenty_witness_bound
  have ho := Real.sq_sqrt (realEnergy_nonneg (realIterate realPathStep 20 realPathStart))
  have hi := Real.sq_sqrt (realEnergy_nonneg realPathStart)
  have hno : 0 ≤ Real.sqrt (realEnergy (realIterate realPathStep 20 realPathStart)) :=
    Real.sqrt_nonneg _
  have hni : 0 < Real.sqrt (realEnergy realPathStart) := by
    rw [realPath_start_energy]
    positivity
  unfold euclideanNorm
  nlinarith

theorem every_path_upper_bound_exceeds_fifth (r : ℝ)
    (h : isTwentyStepBound realPathStep r) : (1/5 : ℝ) < r := by
  have hW := path_twenty_norm_witness
  have hR := h realPathStart realPath_start_mean_zero
  have hpositive : 0 < euclideanNorm realPathStart := by
    unfold euclideanNorm
    rw [realPath_start_energy]
    positivity
  have hstrict : (1/5 : ℝ) * euclideanNorm realPathStart <
      r * euclideanNorm realPathStart := lt_of_lt_of_le hW hR
  nlinarith

/-- A real-vector worst-case separation without redefining the observable:
every valid uniform path bound exceeds the certified star bound by > 0.05. -/
theorem rp001_real_worst_case_gap (r : ℝ)
    (h : isTwentyStepBound realPathStep r) :
    (1/20 : ℝ) < r - (3/20 : ℝ) := by
  have hpath := every_path_upper_bound_exceeds_fifth r h
  linarith

end RelationalPersistence
