import Mathlib

/-!
# RP-F007-A01: finite hard-cap residual-service minimax calculations

The *hard cap is assumed enforced*, and the running job is nonpreemptive
with elapsed service 30 seconds at target submission. The Python
experiment independently verifies the complete finite FCFS schedules,
their event-time observations and all 470+60 integral worlds.

This Lean module proves only classical, sharp interval minimax error
bounds (real-valued predictors and real wait endpoints), and that the
two extreme worlds within EACH known-cap family have identical public
records. It does not prove the Python scheduler's trace semantics.
A merely advertised runtime is NOT a proven hard cap.
No novel queue theorem, empirical finding, or physical law is claimed.
-/

namespace RelationalPersistence

structure PublicHardCapState where
  previousQueue : Nat
  recentQueue : Nat
  queueAtOrigin : Nat
  startedHistoryCount : Nat
  historicalWait : ℚ
  runningAge : Nat
  runningHardCap : Nat
  runningHardCapEnforced : Bool
  targetRequestedProcessors : Nat
  deriving DecidableEq, Repr

def boundedPublicObservation (cap : Nat) : PublicHardCapState :=
  { previousQueue := 0
    recentQueue := 0
    queueAtOrigin := 0
    startedHistoryCount := 1
    historicalWait := 1
    runningAge := 30
    runningHardCap := cap
    runningHardCapEnforced := true
    targetRequestedProcessors := 1 }

structure BoundedServiceWorld where
  observed : PublicHardCapState
  remainingSeconds : Nat

def broadNear : BoundedServiceWorld :=
  ⟨boundedPublicObservation 500, 1⟩

def broadFar : BoundedServiceWorld :=
  ⟨boundedPublicObservation 500, 470⟩

def narrowNear : BoundedServiceWorld :=
  ⟨boundedPublicObservation 90, 1⟩

def narrowFar : BoundedServiceWorld :=
  ⟨boundedPublicObservation 90, 60⟩

def syntheticTargetWait (world : BoundedServiceWorld) : ℝ :=
  (world.remainingSeconds : ℝ)

theorem broad_same_public_state :
    broadNear.observed = broadFar.observed := by
  rfl

theorem narrow_same_public_state :
    narrowNear.observed = narrowFar.observed := by
  rfl

theorem broad_and_narrow_caps_are_distinguishable :
    broadNear.observed ≠ narrowNear.observed := by
  decide

/-- At the exact declared boundary the running job exhausts its HARD cap. -/
theorem registered_extreme_worlds_respect_caps :
    (30 + broadNear.remainingSeconds ≤ broadNear.observed.runningHardCap) ∧
    (30 + broadFar.remainingSeconds ≤ broadFar.observed.runningHardCap) ∧
    (30 + narrowNear.remainingSeconds ≤ narrowNear.observed.runningHardCap) ∧
    (30 + narrowFar.remainingSeconds ≤ narrowFar.observed.runningHardCap) := by
  decide

/-- Ordinary triangle inequality, not a newly discovered mathematical law. -/
theorem broad_endpoint_error_sum (p : ℝ) :
    (469 : ℝ) ≤ |p - 1| + |p - 470| := by
  have h := abs_sub_le (1 : ℝ) p 470
  have hv : |(1 : ℝ) - 470| = 469 := by norm_num
  rw [hv, abs_sub_comm (1 : ℝ) p] at h
  exact h

theorem narrow_endpoint_error_sum (p : ℝ) :
    (59 : ℝ) ≤ |p - 1| + |p - 60| := by
  have h := abs_sub_le (1 : ℝ) p 60
  have hv : |(1 : ℝ) - 60| = 59 := by norm_num
  rw [hv, abs_sub_comm (1 : ℝ) p] at h
  exact h

/-- Universal lower bound over all real predictions from the shared cap. -/
theorem broad_minimax_lower_bound (p : ℝ) :
    (469 / 2 : ℝ) ≤ max |p - 1| |p - 470| := by
  have hsum := broad_endpoint_error_sum p
  have hleft : |p - 1| ≤ max |p - 1| |p - 470| := le_max_left _ _
  have hright : |p - 470| ≤ max |p - 1| |p - 470| := le_max_right _ _
  linarith

theorem narrow_minimax_lower_bound (p : ℝ) :
    (59 / 2 : ℝ) ≤ max |p - 1| |p - 60| := by
  have hsum := narrow_endpoint_error_sum p
  have hleft : |p - 1| ≤ max |p - 1| |p - 60| := le_max_left _ _
  have hright : |p - 60| ≤ max |p - 1| |p - 60| := le_max_right _ _
  linarith

/-- Midpoint uniformly covers EVERY real wait in the stated interval. -/
theorem broad_midpoint_covers_every_admissible_real_wait
    (w : ℝ) (hmin : 1 ≤ w) (hmax : w ≤ 470) :
    |(471 / 2 : ℝ) - w| ≤ 469 / 2 := by
  apply abs_le.mpr
  constructor <;> linarith

theorem narrow_midpoint_covers_every_admissible_real_wait
    (w : ℝ) (hmin : 1 ≤ w) (hmax : w ≤ 60) :
    |(61 / 2 : ℝ) - w| ≤ 59 / 2 := by
  apply abs_le.mpr
  constructor <;> linarith

/-- Both minimax errors are SHARP, not merely upper estimates. -/
theorem broad_midpoint_attains_sharp_error :
    max |(471 / 2 : ℝ) - 1| |(471 / 2 : ℝ) - 470| = 469 / 2 := by
  norm_num

theorem narrow_midpoint_attains_sharp_error :
    max |(61 / 2 : ℝ) - 1| |(61 / 2 : ℝ) - 60| = 59 / 2 := by
  norm_num

/-- Any deterministic predictor seeing only the common BROAD public
observation must make the same prediction for both feasible endpoints. -/
theorem broad_observation_predictor_unavoidable_error
    (predict : PublicHardCapState → ℝ) :
    (469 / 2 : ℝ) ≤
      max
        |predict broadNear.observed - syntheticTargetWait broadNear|
        |predict broadFar.observed - syntheticTargetWait broadFar| := by
  simpa [broadNear, broadFar, syntheticTargetWait] using
    broad_minimax_lower_bound (predict (boundedPublicObservation 500))

theorem narrow_observation_predictor_unavoidable_error
    (predict : PublicHardCapState → ℝ) :
    (59 / 2 : ℝ) ≤
      max
        |predict narrowNear.observed - syntheticTargetWait narrowNear|
        |predict narrowFar.observed - syntheticTargetWait narrowFar| := by
  simpa [narrowNear, narrowFar, syntheticTargetWait] using
    narrow_minimax_lower_bound (predict (boundedPublicObservation 90))

/-- The two different hard-cap cases have different publicly visible
limits; this is NOT a same-input intervention or external field effect. -/
theorem registered_minimax_bound_difference :
    (469 / 2 : ℝ) - (59 / 2 : ℝ) = 205 := by
  norm_num

theorem registered_minimax_ratio :
    (59 / 2 : ℝ) / (469 / 2 : ℝ) = 59 / 469 := by
  norm_num

end RelationalPersistence
