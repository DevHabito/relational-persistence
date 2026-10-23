import RelationalPersistence.TwentyStep

/-!
# RP-F001: twenty-step bounds over the real numbers

The rational certificates are extended by constructing the same finite
polynomial dynamics over `ℝ`. The quantified star inequality includes
all real six-coordinate mean-zero states, not only rational ones.

This module establishes **squared Euclidean norm** inequalities.
A separate graph correspondence and operator-norm interpretation connect
them to the preregistered RP-001 metric. No empirical assertion follows.
-/

namespace RelationalPersistence

structure RealSixState where
  a : ℝ
  b : ℝ
  c : ℝ
  d : ℝ
  e : ℝ
  f : ℝ

def realTotal (x : RealSixState) : ℝ :=
  x.a + x.b + x.c + x.d + x.e + x.f

def realEnergy (x : RealSixState) : ℝ :=
  x.a ^ 2 + x.b ^ 2 + x.c ^ 2 + x.d ^ 2 + x.e ^ 2 + x.f ^ 2

def realPathStep (x : RealSixState) : RealSixState :=
  ⟨(9*x.a + x.b)/10, (x.a + 8*x.b + x.c)/10,
   (x.b + 8*x.c + x.d)/10, (x.c + 8*x.d + x.e)/10,
   (x.d + 8*x.e + x.f)/10, (x.e + 9*x.f)/10⟩

def realStarStep (x : RealSixState) : RealSixState :=
  ⟨(5*x.a + x.b + x.c + x.d + x.e + x.f)/10,
   (x.a + 9*x.b)/10, (x.a + 9*x.c)/10,
   (x.a + 9*x.d)/10, (x.a + 9*x.e)/10,
   (x.a + 9*x.f)/10⟩

def realIterate (step : RealSixState → RealSixState) : Nat → RealSixState → RealSixState
  | 0, x => x
  | n + 1, x => step (realIterate step n x)

theorem realStar_preserves_total (x : RealSixState) :
    realTotal (realStarStep x) = realTotal x := by
  unfold realTotal realStarStep
  ring

theorem realStar_energy_identity (x : RealSixState) :
    (81/100 : ℝ) * realEnergy x - realEnergy (realStarStep x) -
      (39/50 : ℝ) * x.a ^ 2 =
        -(realTotal x) * (26*x.a + realTotal x)/100 := by
  unfold realEnergy realStarStep realTotal
  ring

theorem realStar_one_step_bound (x : RealSixState) (hz : realTotal x = 0) :
    realEnergy (realStarStep x) ≤ (81/100 : ℝ) * realEnergy x := by
  have hid := realStar_energy_identity x
  rw [hz] at hid
  simp only [neg_zero, zero_mul, zero_div] at hid
  nlinarith [sq_nonneg x.a]

theorem realStar_iterate_total (n : Nat) (x : RealSixState) :
    realTotal (realIterate realStarStep n x) = realTotal x := by
  induction n with
  | zero => rfl
  | succ n ih =>
      change realTotal (realStarStep (realIterate realStarStep n x)) = realTotal x
      rw [realStar_preserves_total, ih]

theorem realStar_energy_power_bound (n : Nat) (x : RealSixState)
    (hz : realTotal x = 0) :
    realEnergy (realIterate realStarStep n x) ≤
      (81/100 : ℝ)^n * realEnergy x := by
  induction n with
  | zero => simp [realIterate]
  | succ n ih =>
      have hz' : realTotal (realIterate realStarStep n x) = 0 := by
        rw [realStar_iterate_total, hz]
      calc
        realEnergy (realIterate realStarStep (n+1) x)
          = realEnergy (realStarStep (realIterate realStarStep n x)) := rfl
        _ ≤ (81/100 : ℝ) * realEnergy (realIterate realStarStep n x) :=
          realStar_one_step_bound _ hz'
        _ ≤ (81/100 : ℝ) * ((81/100 : ℝ)^n * realEnergy x) :=
          mul_le_mul_of_nonneg_left ih (by norm_num)
        _ = (81/100 : ℝ)^(n+1) * realEnergy x := by
          rw [pow_succ]
          ring

theorem realEnergy_nonneg (x : RealSixState) : 0 ≤ realEnergy x := by
  unfold realEnergy
  positivity

theorem realStar_twenty_uniform_bound (x : RealSixState)
    (hz : realTotal x = 0) :
    realEnergy (realIterate realStarStep 20 x) ≤
      (3/20 : ℝ)^2 * realEnergy x := by
  have h := realStar_energy_power_bound 20 x hz
  have hf : (81/100 : ℝ)^20 ≤ (3/20 : ℝ)^2 := by norm_num
  calc
    _ ≤ (81/100 : ℝ)^20 * realEnergy x := h
    _ ≤ (3/20 : ℝ)^2 * realEnergy x :=
      mul_le_mul_of_nonneg_right hf (realEnergy_nonneg x)

def realPathStart : RealSixState := ⟨1, 1, 1, -1, -1, -1⟩

theorem realPath_start_mean_zero : realTotal realPathStart = 0 := by
  norm_num [realTotal, realPathStart]

theorem realPath_start_energy : realEnergy realPathStart = 6 := by
  norm_num [realEnergy, realPathStart]

private def realPathState0 : RealSixState := realPathStart
private theorem realPathCertificate0 : realIterate realPathStep 0 realPathStart = realPathState0 := rfl

private def realPathState1 : RealSixState := ⟨1, 1, (4 / 5 : ℝ), (-4 / 5 : ℝ), -1, -1⟩
private theorem realPathCertificate1 : realIterate realPathStep 1 realPathStart = realPathState1 := by
  change realPathStep (realIterate realPathStep 0 realPathStart) = realPathState1
  rw [realPathCertificate0]
  norm_num [realPathStep, realPathState0, realPathState1, realPathStart]

private def realPathState2 : RealSixState := ⟨1, (49 / 50 : ℝ), (33 / 50 : ℝ), (-33 / 50 : ℝ), (-49 / 50 : ℝ), -1⟩
private theorem realPathCertificate2 : realIterate realPathStep 2 realPathStart = realPathState2 := by
  change realPathStep (realIterate realPathStep 1 realPathStart) = realPathState2
  rw [realPathCertificate1]
  norm_num [realPathStep, realPathState1, realPathState2]

private def realPathState3 : RealSixState := ⟨(499 / 500 : ℝ), (19 / 20 : ℝ), (14 / 25 : ℝ), (-14 / 25 : ℝ), (-19 / 20 : ℝ), (-499 / 500 : ℝ)⟩
private theorem realPathCertificate3 : realIterate realPathStep 3 realPathStart = realPathState3 := by
  change realPathStep (realIterate realPathStep 2 realPathStart) = realPathState3
  rw [realPathCertificate2]
  norm_num [realPathStep, realPathState2, realPathState3]

private def realPathState4 : RealSixState := ⟨(2483 / 2500 : ℝ), (4579 / 5000 : ℝ), (487 / 1000 : ℝ), (-487 / 1000 : ℝ), (-4579 / 5000 : ℝ), (-2483 / 2500 : ℝ)⟩
private theorem realPathCertificate4 : realIterate realPathStep 4 realPathStart = realPathState4 := by
  change realPathStep (realIterate realPathStep 3 realPathStart) = realPathState4
  rw [realPathCertificate3]
  norm_num [realPathStep, realPathState3, realPathState4]

private def realPathState5 : RealSixState := ⟨(49273 / 50000 : ℝ), (44033 / 50000 : ℝ), (2703 / 6250 : ℝ), (-2703 / 6250 : ℝ), (-44033 / 50000 : ℝ), (-49273 / 50000 : ℝ)⟩
private theorem realPathCertificate5 : realIterate realPathStep 5 realPathStart = realPathState5 := by
  change realPathStep (realIterate realPathStep 4 realPathStart) = realPathState5
  rw [realPathCertificate4]
  norm_num [realPathStep, realPathState4, realPathState5]

private def realPathState6 : RealSixState := ⟨(48749 / 50000 : ℝ), (423161 / 500000 : ℝ), (195401 / 500000 : ℝ), (-195401 / 500000 : ℝ), (-423161 / 500000 : ℝ), (-48749 / 50000 : ℝ)⟩
private theorem realPathCertificate6 : realIterate realPathStep 6 realPathStart = realPathState6 := by
  change realPathStep (realIterate realPathStep 5 realPathStart) = realPathState6
  rw [realPathCertificate5]
  norm_num [realPathStep, realPathState5, realPathState6]

private def realPathState7 : RealSixState := ⟨(4810571 / 5000000 : ℝ), (4068179 / 5000000 : ℝ), (223871 / 625000 : ℝ), (-223871 / 625000 : ℝ), (-4068179 / 5000000 : ℝ), (-4810571 / 5000000 : ℝ)⟩
private theorem realPathCertificate7 : realIterate realPathStep 7 realPathStart = realPathState7 := by
  change realPathStep (realIterate realPathStep 6 realPathStart) = realPathState7
  rw [realPathCertificate6]
  norm_num [realPathStep, realPathState6, realPathState7]

private def realPathState8 : RealSixState := ⟨(23681659 / 25000000 : ℝ), (39146971 / 50000000 : ℝ), (3320991 / 10000000 : ℝ), (-3320991 / 10000000 : ℝ), (-39146971 / 50000000 : ℝ), (-23681659 / 25000000 : ℝ)⟩
private theorem realPathCertificate8 : realIterate realPathStep 8 realPathStart = realPathState8 := by
  change realPathStep (realIterate realPathStep 7 realPathStart) = realPathState8
  rw [realPathCertificate7]
  norm_num [realPathStep, realPathState7, realPathState8]

private def realPathState9 : RealSixState := ⟨(465416833 / 500000000 : ℝ), (377144041 / 500000000 : ℝ), (19422707 / 62500000 : ℝ), (-19422707 / 62500000 : ℝ), (-377144041 / 500000000 : ℝ), (-465416833 / 500000000 : ℝ)⟩
private theorem realPathCertificate9 : realIterate realPathStep 9 realPathStart = realPathState9 := by
  change realPathStep (realIterate realPathStep 8 realPathStart) = realPathState9
  rw [realPathCertificate8]
  norm_num [realPathStep, realPathState8, realPathState9]

private def realPathState10 : RealSixState := ⟨(2282947769 / 2500000000 : ℝ), (3637950817 / 5000000000 : ℝ), (1464815633 / 5000000000 : ℝ), (-1464815633 / 5000000000 : ℝ), (-3637950817 / 5000000000 : ℝ), (-2282947769 / 2500000000 : ℝ)⟩
private theorem realPathCertificate10 : realIterate realPathStep 10 realPathStart = realPathState10 := by
  change realPathStep (realIterate realPathStep 9 realPathStart) = realPathState10
  rw [realPathCertificate9]
  norm_num [realPathStep, realPathState9, realPathState10]

private def realPathState11 : RealSixState := ⟨(44731010659 / 50000000000 : ℝ), (35134317707 / 50000000000 : ℝ), (1736457531 / 6250000000 : ℝ), (-1736457531 / 6250000000 : ℝ), (-35134317707 / 50000000000 : ℝ), (-44731010659 / 50000000000 : ℝ)⟩
private theorem realPathCertificate11 : realIterate realPathStep 11 realPathStart = realPathState11 := by
  change realPathStep (realIterate realPathStep 10 realPathStart) = realPathState11
  rw [realPathCertificate10]
  norm_num [realPathStep, realPathState10, realPathState11]

private def realPathState12 : RealSixState := ⟨(218856706819 / 250000000000 : ℝ), (339697212563 / 500000000000 : ℝ), (132375939443 / 500000000000 : ℝ), (-132375939443 / 500000000000 : ℝ), (-339697212563 / 500000000000 : ℝ), (-218856706819 / 250000000000 : ℝ)⟩
private theorem realPathCertificate12 : realIterate realPathStep 12 realPathStart = realPathState12 := by
  change realPathStep (realIterate realPathStep 11 realPathStart) = realPathState12
  rw [realPathCertificate11]
  norm_num [realPathStep, realPathState11, realPathState12]

private def realPathState13 : RealSixState := ⟨(855823587061 / 1000000000000 : ℝ), (657533410717 / 1000000000000 : ℝ), (158291098583 / 625000000000 : ℝ), (-158291098583 / 625000000000 : ℝ), (-657533410717 / 1000000000000 : ℝ), (-855823587061 / 1000000000000 : ℝ)⟩
private theorem realPathCertificate13 : realIterate realPathStep 13 realPathStart = realPathState13 := by
  change realPathStep (realIterate realPathStep 12 realPathStart) = realPathState13
  rw [realPathCertificate12]
  norm_num [realPathStep, realPathState12, realPathState13]

private def realPathState14 : RealSixState := ⟨(4179972847133 / 5000000000000 : ℝ), (31846783152649 / 50000000000000 : ℝ), (12151968574233 / 50000000000000 : ℝ), (-12151968574233 / 50000000000000 : ℝ), (-31846783152649 / 50000000000000 : ℝ), (-4179972847133 / 5000000000000 : ℝ)⟩
private theorem realPathCertificate14 : realIterate realPathStep 14 realPathStart = realPathState14 := by
  change realPathStep (realIterate realPathStep 13 realPathStart) = realPathState14
  rw [realPathCertificate13]
  norm_num [realPathStep, realPathState13, realPathState14]

private def realPathState15 : RealSixState := ⟨(408044339394619 / 500000000000000 : ℝ), (61745192453351 / 100000000000000 : ℝ), (2922764079307 / 12500000000000 : ℝ), (-2922764079307 / 12500000000000 : ℝ), (-61745192453351 / 100000000000000 : ℝ), (-408044339394619 / 500000000000000 : ℝ)⟩
private theorem realPathCertificate15 : realIterate realPathStep 15 realPathStart = realPathState15 := by
  change realPathStep (realIterate realPathStep 14 realPathStart) = realPathState15
  rw [realPathCertificate14]
  norm_num [realPathStep, realPathState14, realPathState15]

private def realPathState16 : RealSixState := ⟨(1990562508409163 / 2500000000000000 : ℝ), (2994762600700939 / 5000000000000000 : ℝ), (225419980894543 / 1000000000000000 : ℝ), (-225419980894543 / 1000000000000000 : ℝ), (-2994762600700939 / 5000000000000000 : ℝ), (-1990562508409163 / 2500000000000000 : ℝ)⟩
private theorem realPathCertificate16 : realIterate realPathStep 16 realPathStart = realPathState16 := by
  change realPathStep (realIterate realPathStep 15 realPathStart) = realPathState16
  rw [realPathCertificate15]
  norm_num [realPathStep, realPathState15, realPathState16]

private def realPathState17 : RealSixState := ⟨(38824887752065873 / 50000000000000000 : ℝ), (29066325726898553 / 50000000000000000 : ℝ), (1360557741501243 / 6250000000000000 : ℝ), (-1360557741501243 / 6250000000000000 : ℝ), (-29066325726898553 / 50000000000000000 : ℝ), (-38824887752065873 / 50000000000000000 : ℝ)⟩
private theorem realPathCertificate17 : realIterate realPathStep 17 realPathStart = realPathState17 := by
  change realPathStep (realIterate realPathStep 16 realPathStart) = realPathState17
  rw [realPathCertificate16]
  norm_num [realPathStep, realPathState16, realPathState17]

private def realPathState18 : RealSixState := ⟨(37849031549549141 / 50000000000000000 : ℝ), (282239955499264241 / 500000000000000000 : ℝ), (105257559250968161 / 500000000000000000 : ℝ), (-105257559250968161 / 500000000000000000 : ℝ), (-282239955499264241 / 500000000000000000 : ℝ), (-37849031549549141 / 50000000000000000 : ℝ)⟩
private theorem realPathCertificate18 : realIterate realPathStep 18 realPathStart = realPathState18 := by
  change realPathStep (realIterate realPathStep 17 realPathStart) = realPathState18
  rw [realPathCertificate17]
  norm_num [realPathStep, realPathState17, realPathState18]

private def realPathState19 : RealSixState := ⟨(3688652794958686931 / 5000000000000000000 : ℝ), (2741667518740573499 / 5000000000000000000 : ℝ), (127380358782005171 / 625000000000000000 : ℝ), (-127380358782005171 / 625000000000000000 : ℝ), (-2741667518740573499 / 5000000000000000000 : ℝ), (-3688652794958686931 / 5000000000000000000 : ℝ)⟩
private theorem realPathCertificate19 : realIterate realPathStep 19 realPathStart = realPathState19 := by
  change realPathStep (realIterate realPathStep 18 realPathStart) = realPathState19
  rw [realPathCertificate18]
  norm_num [realPathStep, realPathState18, realPathState19]

private def realPathState20 : RealSixState := ⟨(17969771336684377939 / 25000000000000000000 : ℝ), (26641035815139316291 / 50000000000000000000 : ℝ), (394998704421314523 / 2000000000000000000 : ℝ), (-394998704421314523 / 2000000000000000000 : ℝ), (-26641035815139316291 / 50000000000000000000 : ℝ), (-17969771336684377939 / 25000000000000000000 : ℝ)⟩
private theorem realPathCertificate20 : realIterate realPathStep 20 realPathStart = realPathState20 := by
  change realPathStep (realIterate realPathStep 19 realPathStart) = realPathState20
  rw [realPathCertificate19]
  norm_num [realPathStep, realPathState19, realPathState20]


theorem realPath_twenty_witness_bound :
    (1/5 : ℝ)^2 * realEnergy realPathStart <
      realEnergy (realIterate realPathStep 20 realPathStart) := by
  rw [realPathCertificate20, realPath_start_energy]
  norm_num [realEnergy, realPathState20]

/-- The **real** twenty-step squared-norm separation certificate. -/
theorem rp001_real_twenty_step_certificate :
    (1/5 : ℝ)^2 * realEnergy realPathStart <
      realEnergy (realIterate realPathStep 20 realPathStart) ∧
    (∀ x : RealSixState, realTotal x = 0 →
      realEnergy (realIterate realStarStep 20 x) ≤
        (3/20 : ℝ)^2 * realEnergy x) := by
  exact ⟨realPath_twenty_witness_bound, realStar_twenty_uniform_bound⟩

end RelationalPersistence
