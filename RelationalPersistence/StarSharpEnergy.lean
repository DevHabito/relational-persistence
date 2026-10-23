import RelationalPersistence.RealTwentyStep

/-!
# RP-F002: an attained sharp energy bound for the six-vertex star

These results concern the fixed, classical unweighted star consensus update
with gain 1/10 and its twenty-step action on mean-zero real vectors.

The earlier uniform squared-energy estimate (81/100)^20 is not merely an
upper bound: a nonzero eigenmode attains it. Thus it is the least possible
uniform coefficient for the declared squared-energy inequality.

This does not formalize all graph spectra, the path's exact eigenvalue,
an operator-norm supremum, empirical data, or fundamental physics.
-/

namespace RelationalPersistence

/-- A leaf-to-leaf disagreement mode; its center coordinate vanishes. -/
def starEigenLine (c : ℝ) : RealSixState :=
  ⟨0, c, -c, 0, 0, 0⟩

theorem starEigenLine_zero_mean (c : ℝ) :
    realTotal (starEigenLine c) = 0 := by
  simp [realTotal, starEigenLine]

theorem starEigenLine_energy (c : ℝ) :
    realEnergy (starEigenLine c) = 2 * c ^ 2 := by
  simp [realEnergy, starEigenLine]
  ring

/-- This leaf-disagreement mode is an exact eigenvector of the update. -/
theorem starEigenLine_step (c : ℝ) :
    realStarStep (starEigenLine c) =
      starEigenLine ((9 / 10 : ℝ) * c) := by
  ext <;> simp [realStarStep, starEigenLine] <;> ring

theorem starEigenLine_iterate (n : Nat) (c : ℝ) :
    realIterate realStarStep n (starEigenLine c) =
      starEigenLine ((9 / 10 : ℝ) ^ n * c) := by
  induction n with
  | zero =>
      simp [realIterate]
  | succ n ih =>
      change realStarStep (realIterate realStarStep n (starEigenLine c)) =
        starEigenLine ((9 / 10 : ℝ) ^ (n + 1) * c)
      rw [ih, starEigenLine_step]
      congr 1
      rw [pow_succ]
      ring

/-- Uniform twenty-step squared-energy bounds on the mean-zero subspace. -/
def isStarSquaredEnergyBound (bound : ℝ) : Prop :=
  ∀ x : RealSixState, realTotal x = 0 →
    realEnergy (realIterate realStarStep 20 x) ≤ bound * realEnergy x

theorem star_squared_energy_upper_bound :
    isStarSquaredEnergyBound ((81 / 100 : ℝ) ^ 20) := by
  intro x hx
  exact realStar_energy_power_bound 20 x hx

/-- No smaller coefficient can uniformly bound the squared energy:
the explicit leaf disagreement mode saturates the estimate. -/
theorem star_squared_energy_lower_bound (bound : ℝ)
    (hbound : isStarSquaredEnergyBound bound) :
    (81 / 100 : ℝ) ^ 20 ≤ bound := by
  have h := hbound (starEigenLine 1) (starEigenLine_zero_mean 1)
  rw [starEigenLine_iterate, starEigenLine_energy, starEigenLine_energy] at h
  have hp : ((9 / 10 : ℝ) ^ 20) ^ 2 = (81 / 100 : ℝ) ^ 20 := by
    norm_num
  norm_num at h
  rw [hp] at h
  linarith

/-- Sharpness is two-sided, with no numerical approximation. -/
theorem star_twenty_squared_energy_optimal :
    isStarSquaredEnergyBound ((81 / 100 : ℝ) ^ 20) ∧
      (∀ bound : ℝ, isStarSquaredEnergyBound bound →
        (81 / 100 : ℝ) ^ 20 ≤ bound) := by
  exact ⟨star_squared_energy_upper_bound,
    star_squared_energy_lower_bound⟩

end RelationalPersistence
