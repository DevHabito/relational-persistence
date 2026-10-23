import RelationalPersistence.PathSlowEigenmode
import RelationalPersistence.StarSharpNorm

/-!
# RP-F002: a sharp real P6 contraction bound via a sum-of-squares certificate

This proves a global upper bound rather than extrapolating from one eigenmode.
The six-vertex path, gain 1/10, and 20-step horizon are unchanged.

The certificate is an elementary polynomial identity, checked by the Lean
kernel, together with nonnegative square coefficients. Its eigenmode and
the resulting supremum belong to classical graph spectral theory, not a
new physical law. No measured dynamics or PMFF bridge is asserted.
-/

namespace RelationalPersistence

/-- Four faster orthogonal modes, without normalizing square roots. -/
def pathFastTwo (x : RealSixState) : ℝ :=
  x.a - x.c - x.d + x.f

def pathFastThree (x : RealSixState) : ℝ :=
  x.a - x.b - x.c + x.d + x.e - x.f

def pathFastFour (x : RealSixState) : ℝ :=
  x.a - 2*x.b + x.c + x.d - 2*x.e + x.f

def pathFastFive (t : ℝ) (x : RealSixState) : ℝ :=
  x.a - (1+t)*x.b + (2+t)*x.c -
    (2+t)*x.d + (1+t)*x.e - x.f

/-- The four nonnegative components of the sharp contraction defect. -/
noncomputable def pathSquareCertificate (t : ℝ) (x : RealSixState) : ℝ :=
  ((8*t-7)/200) * pathFastTwo x ^ 2 +
  ((3+16*t)/600) * pathFastThree x ^ 2 +
  ((9+8*t)/600) * pathFastFour x ^ 2 +
  ((4*t-6)/75) * pathFastFive t x ^ 2

/-- An algebraic quotient tracking the single relation t²=3.
It is deliberately explicit to make the finite polynomial certificate
independently auditable; it vanishes from the actual inequality. -/
private def pathCorrection (t : ℝ) (x : RealSixState) : ℝ :=
  -3*x.a^2 - 32*x.a*x.b + 32*x.a*x.c -
  32*x.a*x.d + 32*x.a*x.e +
  16*x.b^2*t + 5*x.b^2 - 32*x.b*x.c*t -
  48*x.b*x.c + 32*x.b*x.d*t + 48*x.b*x.d -
  32*x.b*x.e*t - 16*x.b*x.e + 32*x.b*x.f +
  16*x.c^2*t + 37*x.c^2 - 32*x.c*x.d*t -
  80*x.c*x.d + 32*x.c*x.e*t + 48*x.c*x.e -
  32*x.c*x.f + 16*x.d^2*t + 37*x.d^2 -
  32*x.d*x.e*t - 48*x.d*x.e + 32*x.d*x.f +
  16*x.e^2*t + 5*x.e^2 - 32*x.e*x.f - 3*x.f^2

/-- Polynomial identity prior to applying sqrt(3)²=3.
This identity is valid for every real t and six-coordinate real state. -/
private theorem pathPolynomialIdentity (t : ℝ) (x : RealSixState) :
    ((8+t)/10)^2 * realEnergy x -
      realEnergy (realPathStep x) =
      ((16*t-33)/600) * realTotal x ^ 2 +
      pathSquareCertificate t x -
      (t^2-3) * pathCorrection t x / 300 := by
  unfold realEnergy realPathStep realTotal
    pathSquareCertificate pathFastTwo pathFastThree
    pathFastFour pathFastFive pathCorrection
  ring

theorem pathSharp_sos_identity (x : RealSixState) :
    pathSlowGain^2 * realEnergy x -
      realEnergy (realPathStep x) =
      ((16*Real.sqrt 3-33)/600) * realTotal x ^ 2 +
      pathSquareCertificate (Real.sqrt 3) x := by
  have h := pathPolynomialIdentity (Real.sqrt 3) x
  have hs : (Real.sqrt (3 : ℝ))^2 = 3 := by norm_num
  rw [hs] at h
  simp only [sub_self, zero_mul, zero_div, sub_zero] at h
  simpa [pathSlowGain] using h

private theorem sqrtThree_lower : (3/2 : ℝ) ≤ Real.sqrt 3 := by
  have h : Real.sqrt ((3/2 : ℝ)^2) ≤ Real.sqrt 3 :=
    Real.sqrt_le_sqrt (by norm_num)
  norm_num at h
  exact h

theorem pathSquareCertificate_nonneg (x : RealSixState) :
    0 ≤ pathSquareCertificate (Real.sqrt 3) x := by
  have ht := sqrtThree_lower
  have hc2 : 0 ≤ ((8*Real.sqrt 3-7)/200 : ℝ) := by linarith
  have hc3 : 0 ≤ ((3+16*Real.sqrt 3)/600 : ℝ) := by linarith
  have hc4 : 0 ≤ ((9+8*Real.sqrt 3)/600 : ℝ) := by linarith
  have hc5 : 0 ≤ ((4*Real.sqrt 3-6)/75 : ℝ) := by linarith
  unfold pathSquareCertificate
  exact add_nonneg
    (add_nonneg
      (add_nonneg
        (mul_nonneg hc2 (sq_nonneg _))
        (mul_nonneg hc3 (sq_nonneg _)))
      (mul_nonneg hc4 (sq_nonneg _)))
    (mul_nonneg hc5 (sq_nonneg _))

theorem pathSharp_one_step_energy (x : RealSixState)
    (hz : realTotal x = 0) :
    realEnergy (realPathStep x) ≤
      pathSlowGain^2 * realEnergy x := by
  have h := pathSharp_sos_identity x
  rw [hz] at h
  simp only [zero_pow (by norm_num : 2 ≠ 0),
    mul_zero, zero_add] at h
  have hp := pathSquareCertificate_nonneg x
  linarith

theorem pathSharp_preserves_total (x : RealSixState) :
    realTotal (realPathStep x) = realTotal x := by
  unfold realTotal realPathStep
  ring

theorem pathSharp_iterate_total (n : Nat) (x : RealSixState) :
    realTotal (realIterate realPathStep n x) = realTotal x := by
  induction n with
  | zero => rfl
  | succ n ih =>
      change realTotal (realPathStep (realIterate realPathStep n x)) =
        realTotal x
      rw [pathSharp_preserves_total, ih]

theorem pathSharp_energy_power (n : Nat) (x : RealSixState)
    (hz : realTotal x = 0) :
    realEnergy (realIterate realPathStep n x) ≤
      (pathSlowGain^2)^n * realEnergy x := by
  induction n with
  | zero => simp [realIterate]
  | succ n ih =>
      have hz' : realTotal (realIterate realPathStep n x) = 0 := by
        rw [pathSharp_iterate_total, hz]
      calc
        realEnergy (realIterate realPathStep (n+1) x)
            = realEnergy (realPathStep (realIterate realPathStep n x)) := rfl
        _ ≤ pathSlowGain^2 * realEnergy (realIterate realPathStep n x) :=
          pathSharp_one_step_energy _ hz'
        _ ≤ pathSlowGain^2 * ((pathSlowGain^2)^n * realEnergy x) :=
          mul_le_mul_of_nonneg_left ih (sq_nonneg _)
        _ = (pathSlowGain^2)^(n+1) * realEnergy x := by
          rw [pow_succ]
          ring

theorem pathSharp_twenty_norm_upper (x : RealSixState)
    (hz : realTotal x = 0) :
    euclideanNorm (realIterate realPathStep 20 x) ≤
      pathSlowGain^20 * euclideanNorm x := by
  have h := pathSharp_energy_power 20 x hz
  have hc : (pathSlowGain^2)^20 = (pathSlowGain^20)^2 := by ring
  rw [hc] at h
  have hr := Real.sqrt_le_sqrt h
  calc
    euclideanNorm (realIterate realPathStep 20 x)
        = Real.sqrt (realEnergy (realIterate realPathStep 20 x)) := rfl
    _ ≤ Real.sqrt ((pathSlowGain^20)^2 * realEnergy x) := hr
    _ = pathSlowGain^20 * euclideanNorm x := by
      rw [Real.sqrt_mul (sq_nonneg _), Real.sqrt_sq_eq_abs,
          abs_of_nonneg (pow_nonneg pathSlowGain_nonneg 20)]
      rfl

/-- The exact upper bound quantified over all mean-zero real graph vectors. -/
theorem graph_path_sharp_upper :
    isGraphTwentyStepBound realPathAdj (pathSlowGain^20) := by
  intro f hz
  let x := fromGraphVector f
  have hre : realCoordinates x = f := graph_coordinates_surjective f
  have hzero : realTotal x = 0 := (graph_zero_sum_iff f).mp hz
  have hiter : realGraphIterate realPathAdj 20 f =
      realCoordinates (realIterate realPathStep 20 x) := by
    rw [← hre]
    exact (real_path_iterate_matches_graph 20 x).symm
  have hleft : graphEuclideanNorm (realGraphIterate realPathAdj 20 f) =
      euclideanNorm (realIterate realPathStep 20 x) := by
    rw [hiter]
    exact graph_coordinate_norm _
  have hright : euclideanNorm x = graphEuclideanNorm f := by
    rw [← hre]
    exact (graph_coordinate_norm x).symm
  calc
    graphEuclideanNorm (realGraphIterate realPathAdj 20 f)
        = euclideanNorm (realIterate realPathStep 20 x) := hleft
    _ ≤ pathSlowGain^20 * euclideanNorm x := pathSharp_twenty_norm_upper x hzero
    _ = pathSlowGain^20 * graphEuclideanNorm f := by rw [hright]

/-- The set of ratios for nonzero real zero-mean initial vectors. -/
def pathResidualRatios : Set ℝ :=
  {r | ∃ f : Fin 6 → ℝ,
    (∑ v : Fin 6, f v) = 0 ∧
    0 < graphEuclideanNorm f ∧
    r * graphEuclideanNorm f =
      graphEuclideanNorm (realGraphIterate realPathAdj 20 f)}

theorem path_ratio_isGreatest :
    IsGreatest pathResidualRatios (pathSlowGain^20) := by
  constructor
  · obtain ⟨f, hz, hp, heq⟩ := graph_path_slow_witness
    exact ⟨f, hz, hp, heq.symm⟩
  · intro r hr
    obtain ⟨f, hz, hp, heq⟩ := hr
    have hu := graph_path_sharp_upper f hz
    rw [← heq] at hu
    nlinarith

/-- Exact worst-case Euclidean residual, with global maximality proved. -/
theorem path_residual_supremum :
    sSup pathResidualRatios = pathSlowGain^20 := by
  exact path_ratio_isGreatest.csSup_eq

end RelationalPersistence
