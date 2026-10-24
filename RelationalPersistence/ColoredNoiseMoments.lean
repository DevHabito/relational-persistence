import Mathlib

/-!
# RP-F004: exact colored-noise stationary moment algebra

The mathematical interpretation of these second moments is specified
in docs/preregistration/RP-F004-A01.md. No probability-space construction
or convergence theorem is formalized here: the results are algebraic
statements about a two-equation moment recurrence over the rationals.

All update coefficients are fixed before proof checking.
-/

namespace RelationalPersistence

structure CorrelatedMoments where
  variance : ℚ
  crossCovariance : ℚ
deriving DecidableEq

/-- A = 1/2, noise marginal variance = 1/100, r = 2p - 1. -/
def correlatedMomentStep (r : ℚ) (m : CorrelatedMoments) :
    CorrelatedMoments :=
  ⟨(1 / 4 : ℚ) * m.variance + m.crossCovariance + (1 / 100 : ℚ),
   r * ((1 / 2 : ℚ) * m.crossCovariance + (1 / 100 : ℚ))⟩

/-- Independent signs (stay probability p = 1/2). -/
def whiteNoiseFixed : CorrelatedMoments :=
  ⟨1 / 75, 0⟩

/-- Persistent signs (stay probability p = 3/4). -/
def persistentNoiseFixed : CorrelatedMoments :=
  ⟨1 / 45, 1 / 150⟩

theorem white_noise_fixed_point :
    correlatedMomentStep 0 whiteNoiseFixed = whiteNoiseFixed := by
  norm_num [correlatedMomentStep, whiteNoiseFixed]

theorem persistent_noise_fixed_point :
    correlatedMomentStep (1 / 2) persistentNoiseFixed =
      persistentNoiseFixed := by
  norm_num [correlatedMomentStep, persistentNoiseFixed]

/-- There cannot be a different rational fixed point for independent noise. -/
theorem white_noise_fixed_point_unique (m : CorrelatedMoments)
    (h : correlatedMomentStep 0 m = m) :
    m = whiteNoiseFixed := by
  cases m with
  | mk v c =>
    have hv : (1 / 4 : ℚ) * v + c + (1 / 100 : ℚ) = v := by
      have hcomp := congrArg CorrelatedMoments.variance h
      simpa [correlatedMomentStep] using hcomp
    have hc : (0 : ℚ) * ((1 / 2 : ℚ) * c + (1 / 100 : ℚ)) = c := by
      have hcomp := congrArg CorrelatedMoments.crossCovariance h
      simpa [correlatedMomentStep] using hcomp
    have hc0 : c = (0 : ℚ) := by linarith
    have hv0 : v = (1 / 75 : ℚ) := by linarith
    simp [whiteNoiseFixed, hv0, hc0]

/-- Uniqueness for the correlated (p = 3/4) second-moment recurrence. -/
theorem persistent_noise_fixed_point_unique (m : CorrelatedMoments)
    (h : correlatedMomentStep (1 / 2) m = m) :
    m = persistentNoiseFixed := by
  cases m with
  | mk v c =>
    have hv : (1 / 4 : ℚ) * v + c + (1 / 100 : ℚ) = v := by
      have hcomp := congrArg CorrelatedMoments.variance h
      simpa [correlatedMomentStep] using hcomp
    have hc : (1 / 2 : ℚ) * ((1 / 2 : ℚ) * c + (1 / 100 : ℚ)) = c := by
      have hcomp := congrArg CorrelatedMoments.crossCovariance h
      simpa [correlatedMomentStep] using hcomp
    have hc0 : c = (1 / 150 : ℚ) := by linarith
    have hv0 : v = (1 / 45 : ℚ) := by linarith
    simp [persistentNoiseFixed, hv0, hc0]

/-- Same marginal noise variance, different fixed-point output variance. -/
theorem colored_noise_fixed_point_separation :
    persistentNoiseFixed.variance - whiteNoiseFixed.variance =
      (2 / 225 : ℚ) ∧
    (1 / 200 : ℚ) ≤
      persistentNoiseFixed.variance - whiteNoiseFixed.variance := by
  norm_num [persistentNoiseFixed, whiteNoiseFixed]

end RelationalPersistence
