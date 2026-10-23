import RelationalPersistence.FiniteWitness
/-!
# RP-F001: rational twenty-step contraction certificate

Six coordinates are kept explicit to make exact finite computations auditable.
Theorems below concern these declared rational maps. The squared-energy
bounds give a path witness > 1/5 and a universal star bound ≤ 3/20
on the mean-zero subspace. No measured physical claim is made.
-/
namespace RelationalPersistence

structure SixState where
  a : ℚ
  b : ℚ
  c : ℚ
  d : ℚ
  e : ℚ
  f : ℚ
  deriving DecidableEq

def total (x : SixState) : ℚ :=
  x.a + x.b + x.c + x.d + x.e + x.f

def energy (x : SixState) : ℚ :=
  x.a ^ 2 + x.b ^ 2 + x.c ^ 2 + x.d ^ 2 + x.e ^ 2 + x.f ^ 2

def pathStep (x : SixState) : SixState :=
  ⟨(9*x.a + x.b)/10, (x.a + 8*x.b + x.c)/10,
   (x.b + 8*x.c + x.d)/10, (x.c + 8*x.d + x.e)/10,
   (x.d + 8*x.e + x.f)/10, (x.e + 9*x.f)/10⟩

def starStep (x : SixState) : SixState :=
  ⟨(5*x.a + x.b + x.c + x.d + x.e + x.f)/10,
   (x.a + 9*x.b)/10, (x.a + 9*x.c)/10,
   (x.a + 9*x.d)/10, (x.a + 9*x.e)/10,
   (x.a + 9*x.f)/10⟩

def iterate (step : SixState → SixState) : Nat → SixState → SixState
  | 0, x => x
  | n + 1, x => step (iterate step n x)

theorem star_preserves_total (x : SixState) :
    total (starStep x) = total x := by
  unfold total starStep
  ring

theorem star_energy_identity (x : SixState) :
    (81/100 : ℚ) * energy x - energy (starStep x) -
      (39/50 : ℚ) * x.a ^ 2 =
        -(total x) * (26*x.a + total x)/100 := by
  unfold energy starStep total
  ring

theorem star_one_step_bound (x : SixState) (hz : total x = 0) :
    energy (starStep x) ≤ (81/100 : ℚ) * energy x := by
  have hid := star_energy_identity x
  rw [hz] at hid
  simp only [neg_zero, zero_mul, zero_div] at hid
  nlinarith [sq_nonneg x.a]

theorem star_iterate_total (n : Nat) (x : SixState) :
    total (iterate starStep n x) = total x := by
  induction n with
  | zero => rfl
  | succ n ih =>
      change total (starStep (iterate starStep n x)) = total x
      rw [star_preserves_total, ih]

theorem star_energy_power_bound (n : Nat) (x : SixState)
    (hz : total x = 0) :
    energy (iterate starStep n x) ≤
      (81/100 : ℚ)^n * energy x := by
  induction n with
  | zero => simp [iterate]
  | succ n ih =>
      have hz' : total (iterate starStep n x) = 0 := by
        rw [star_iterate_total, hz]
      calc
        energy (iterate starStep (n+1) x)
          = energy (starStep (iterate starStep n x)) := rfl
        _ ≤ (81/100 : ℚ) * energy (iterate starStep n x) :=
          star_one_step_bound _ hz'
        _ ≤ (81/100 : ℚ) * ((81/100 : ℚ)^n * energy x) :=
          mul_le_mul_of_nonneg_left ih (by norm_num)
        _ = (81/100 : ℚ)^(n+1) * energy x := by
          rw [pow_succ]
          ring

theorem energy_nonneg (x : SixState) : 0 ≤ energy x := by
  unfold energy
  positivity

theorem star_twenty_uniform_bound (x : SixState)
    (hz : total x = 0) :
    energy (iterate starStep 20 x) ≤ (3/20 : ℚ)^2 * energy x := by
  have h := star_energy_power_bound 20 x hz
  have hf : (81/100 : ℚ)^20 ≤ (3/20 : ℚ)^2 := by norm_num
  calc
    _ ≤ (81/100 : ℚ)^20 * energy x := h
    _ ≤ (3/20 : ℚ)^2 * energy x :=
      mul_le_mul_of_nonneg_right hf (energy_nonneg x)

def pathStart : SixState := ⟨1, 1, 1, -1, -1, -1⟩

theorem path_start_mean_zero : total pathStart = 0 := by
  norm_num [total, pathStart]

theorem path_start_energy : energy pathStart = 6 := by
  norm_num [energy, pathStart]

private def pathState0 : SixState := pathStart
private theorem pathCertificate0 : iterate pathStep 0 pathStart = pathState0 := rfl

private def pathState1 : SixState := ⟨1, 1, (4 / 5 : ℚ), (-4 / 5 : ℚ), -1, -1⟩
private theorem pathCertificate1 : iterate pathStep 1 pathStart = pathState1 := by
  change pathStep (iterate pathStep 0 pathStart) = pathState1
  rw [pathCertificate0]
  norm_num [pathStep, pathState0, pathState1, pathStart]

private def pathState2 : SixState := ⟨1, (49 / 50 : ℚ), (33 / 50 : ℚ), (-33 / 50 : ℚ), (-49 / 50 : ℚ), -1⟩
private theorem pathCertificate2 : iterate pathStep 2 pathStart = pathState2 := by
  change pathStep (iterate pathStep 1 pathStart) = pathState2
  rw [pathCertificate1]
  norm_num [pathStep, pathState1, pathState2]

private def pathState3 : SixState := ⟨(499 / 500 : ℚ), (19 / 20 : ℚ), (14 / 25 : ℚ), (-14 / 25 : ℚ), (-19 / 20 : ℚ), (-499 / 500 : ℚ)⟩
private theorem pathCertificate3 : iterate pathStep 3 pathStart = pathState3 := by
  change pathStep (iterate pathStep 2 pathStart) = pathState3
  rw [pathCertificate2]
  norm_num [pathStep, pathState2, pathState3]

private def pathState4 : SixState := ⟨(2483 / 2500 : ℚ), (4579 / 5000 : ℚ), (487 / 1000 : ℚ), (-487 / 1000 : ℚ), (-4579 / 5000 : ℚ), (-2483 / 2500 : ℚ)⟩
private theorem pathCertificate4 : iterate pathStep 4 pathStart = pathState4 := by
  change pathStep (iterate pathStep 3 pathStart) = pathState4
  rw [pathCertificate3]
  norm_num [pathStep, pathState3, pathState4]

private def pathState5 : SixState := ⟨(49273 / 50000 : ℚ), (44033 / 50000 : ℚ), (2703 / 6250 : ℚ), (-2703 / 6250 : ℚ), (-44033 / 50000 : ℚ), (-49273 / 50000 : ℚ)⟩
private theorem pathCertificate5 : iterate pathStep 5 pathStart = pathState5 := by
  change pathStep (iterate pathStep 4 pathStart) = pathState5
  rw [pathCertificate4]
  norm_num [pathStep, pathState4, pathState5]

private def pathState6 : SixState := ⟨(48749 / 50000 : ℚ), (423161 / 500000 : ℚ), (195401 / 500000 : ℚ), (-195401 / 500000 : ℚ), (-423161 / 500000 : ℚ), (-48749 / 50000 : ℚ)⟩
private theorem pathCertificate6 : iterate pathStep 6 pathStart = pathState6 := by
  change pathStep (iterate pathStep 5 pathStart) = pathState6
  rw [pathCertificate5]
  norm_num [pathStep, pathState5, pathState6]

private def pathState7 : SixState := ⟨(4810571 / 5000000 : ℚ), (4068179 / 5000000 : ℚ), (223871 / 625000 : ℚ), (-223871 / 625000 : ℚ), (-4068179 / 5000000 : ℚ), (-4810571 / 5000000 : ℚ)⟩
private theorem pathCertificate7 : iterate pathStep 7 pathStart = pathState7 := by
  change pathStep (iterate pathStep 6 pathStart) = pathState7
  rw [pathCertificate6]
  norm_num [pathStep, pathState6, pathState7]

private def pathState8 : SixState := ⟨(23681659 / 25000000 : ℚ), (39146971 / 50000000 : ℚ), (3320991 / 10000000 : ℚ), (-3320991 / 10000000 : ℚ), (-39146971 / 50000000 : ℚ), (-23681659 / 25000000 : ℚ)⟩
private theorem pathCertificate8 : iterate pathStep 8 pathStart = pathState8 := by
  change pathStep (iterate pathStep 7 pathStart) = pathState8
  rw [pathCertificate7]
  norm_num [pathStep, pathState7, pathState8]

private def pathState9 : SixState := ⟨(465416833 / 500000000 : ℚ), (377144041 / 500000000 : ℚ), (19422707 / 62500000 : ℚ), (-19422707 / 62500000 : ℚ), (-377144041 / 500000000 : ℚ), (-465416833 / 500000000 : ℚ)⟩
private theorem pathCertificate9 : iterate pathStep 9 pathStart = pathState9 := by
  change pathStep (iterate pathStep 8 pathStart) = pathState9
  rw [pathCertificate8]
  norm_num [pathStep, pathState8, pathState9]

private def pathState10 : SixState := ⟨(2282947769 / 2500000000 : ℚ), (3637950817 / 5000000000 : ℚ), (1464815633 / 5000000000 : ℚ), (-1464815633 / 5000000000 : ℚ), (-3637950817 / 5000000000 : ℚ), (-2282947769 / 2500000000 : ℚ)⟩
private theorem pathCertificate10 : iterate pathStep 10 pathStart = pathState10 := by
  change pathStep (iterate pathStep 9 pathStart) = pathState10
  rw [pathCertificate9]
  norm_num [pathStep, pathState9, pathState10]

private def pathState11 : SixState := ⟨(44731010659 / 50000000000 : ℚ), (35134317707 / 50000000000 : ℚ), (1736457531 / 6250000000 : ℚ), (-1736457531 / 6250000000 : ℚ), (-35134317707 / 50000000000 : ℚ), (-44731010659 / 50000000000 : ℚ)⟩
private theorem pathCertificate11 : iterate pathStep 11 pathStart = pathState11 := by
  change pathStep (iterate pathStep 10 pathStart) = pathState11
  rw [pathCertificate10]
  norm_num [pathStep, pathState10, pathState11]

private def pathState12 : SixState := ⟨(218856706819 / 250000000000 : ℚ), (339697212563 / 500000000000 : ℚ), (132375939443 / 500000000000 : ℚ), (-132375939443 / 500000000000 : ℚ), (-339697212563 / 500000000000 : ℚ), (-218856706819 / 250000000000 : ℚ)⟩
private theorem pathCertificate12 : iterate pathStep 12 pathStart = pathState12 := by
  change pathStep (iterate pathStep 11 pathStart) = pathState12
  rw [pathCertificate11]
  norm_num [pathStep, pathState11, pathState12]

private def pathState13 : SixState := ⟨(855823587061 / 1000000000000 : ℚ), (657533410717 / 1000000000000 : ℚ), (158291098583 / 625000000000 : ℚ), (-158291098583 / 625000000000 : ℚ), (-657533410717 / 1000000000000 : ℚ), (-855823587061 / 1000000000000 : ℚ)⟩
private theorem pathCertificate13 : iterate pathStep 13 pathStart = pathState13 := by
  change pathStep (iterate pathStep 12 pathStart) = pathState13
  rw [pathCertificate12]
  norm_num [pathStep, pathState12, pathState13]

private def pathState14 : SixState := ⟨(4179972847133 / 5000000000000 : ℚ), (31846783152649 / 50000000000000 : ℚ), (12151968574233 / 50000000000000 : ℚ), (-12151968574233 / 50000000000000 : ℚ), (-31846783152649 / 50000000000000 : ℚ), (-4179972847133 / 5000000000000 : ℚ)⟩
private theorem pathCertificate14 : iterate pathStep 14 pathStart = pathState14 := by
  change pathStep (iterate pathStep 13 pathStart) = pathState14
  rw [pathCertificate13]
  norm_num [pathStep, pathState13, pathState14]

private def pathState15 : SixState := ⟨(408044339394619 / 500000000000000 : ℚ), (61745192453351 / 100000000000000 : ℚ), (2922764079307 / 12500000000000 : ℚ), (-2922764079307 / 12500000000000 : ℚ), (-61745192453351 / 100000000000000 : ℚ), (-408044339394619 / 500000000000000 : ℚ)⟩
private theorem pathCertificate15 : iterate pathStep 15 pathStart = pathState15 := by
  change pathStep (iterate pathStep 14 pathStart) = pathState15
  rw [pathCertificate14]
  norm_num [pathStep, pathState14, pathState15]

private def pathState16 : SixState := ⟨(1990562508409163 / 2500000000000000 : ℚ), (2994762600700939 / 5000000000000000 : ℚ), (225419980894543 / 1000000000000000 : ℚ), (-225419980894543 / 1000000000000000 : ℚ), (-2994762600700939 / 5000000000000000 : ℚ), (-1990562508409163 / 2500000000000000 : ℚ)⟩
private theorem pathCertificate16 : iterate pathStep 16 pathStart = pathState16 := by
  change pathStep (iterate pathStep 15 pathStart) = pathState16
  rw [pathCertificate15]
  norm_num [pathStep, pathState15, pathState16]

private def pathState17 : SixState := ⟨(38824887752065873 / 50000000000000000 : ℚ), (29066325726898553 / 50000000000000000 : ℚ), (1360557741501243 / 6250000000000000 : ℚ), (-1360557741501243 / 6250000000000000 : ℚ), (-29066325726898553 / 50000000000000000 : ℚ), (-38824887752065873 / 50000000000000000 : ℚ)⟩
private theorem pathCertificate17 : iterate pathStep 17 pathStart = pathState17 := by
  change pathStep (iterate pathStep 16 pathStart) = pathState17
  rw [pathCertificate16]
  norm_num [pathStep, pathState16, pathState17]

private def pathState18 : SixState := ⟨(37849031549549141 / 50000000000000000 : ℚ), (282239955499264241 / 500000000000000000 : ℚ), (105257559250968161 / 500000000000000000 : ℚ), (-105257559250968161 / 500000000000000000 : ℚ), (-282239955499264241 / 500000000000000000 : ℚ), (-37849031549549141 / 50000000000000000 : ℚ)⟩
private theorem pathCertificate18 : iterate pathStep 18 pathStart = pathState18 := by
  change pathStep (iterate pathStep 17 pathStart) = pathState18
  rw [pathCertificate17]
  norm_num [pathStep, pathState17, pathState18]

private def pathState19 : SixState := ⟨(3688652794958686931 / 5000000000000000000 : ℚ), (2741667518740573499 / 5000000000000000000 : ℚ), (127380358782005171 / 625000000000000000 : ℚ), (-127380358782005171 / 625000000000000000 : ℚ), (-2741667518740573499 / 5000000000000000000 : ℚ), (-3688652794958686931 / 5000000000000000000 : ℚ)⟩
private theorem pathCertificate19 : iterate pathStep 19 pathStart = pathState19 := by
  change pathStep (iterate pathStep 18 pathStart) = pathState19
  rw [pathCertificate18]
  norm_num [pathStep, pathState18, pathState19]

private def pathState20 : SixState := ⟨(17969771336684377939 / 25000000000000000000 : ℚ), (26641035815139316291 / 50000000000000000000 : ℚ), (394998704421314523 / 2000000000000000000 : ℚ), (-394998704421314523 / 2000000000000000000 : ℚ), (-26641035815139316291 / 50000000000000000000 : ℚ), (-17969771336684377939 / 25000000000000000000 : ℚ)⟩
private theorem pathCertificate20 : iterate pathStep 20 pathStart = pathState20 := by
  change pathStep (iterate pathStep 19 pathStart) = pathState20
  rw [pathCertificate19]
  norm_num [pathStep, pathState19, pathState20]

theorem path_twenty_witness_bound :
    (1/5 : ℚ)^2 * energy pathStart <
      energy (iterate pathStep 20 pathStart) := by
  rw [pathCertificate20, path_start_energy]
  norm_num [energy, pathState20]

/-- An exact twenty-step separation certificate for rational-state dynamics.
It does NOT assert a physical law or independently prove a real-valued
operator-norm supremum. The latter needs a formal transfer theorem. -/
theorem rp001_rational_twenty_step_certificate :
    (1/5 : ℚ)^2 * energy pathStart <
      energy (iterate pathStep 20 pathStart) ∧
    (∀ x : SixState, total x = 0 →
      energy (iterate starStep 20 x) ≤ (3/20 : ℚ)^2 * energy x) := by
  exact ⟨path_twenty_witness_bound, star_twenty_uniform_bound⟩

end RelationalPersistence
