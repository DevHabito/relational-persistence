import Mathlib

/-!
# Finite witnesses for relational persistence

These theorems concern a specified finite consensus model and a scalar index.
They are mathematical results, not empirical or fundamental-physics claims.
The one-step topology witness is not the registered twenty-step RP-001 result.
-/

namespace RelationalPersistence

/-- A proposed scalar index, not an observed physical persistence quantity. -/
def scalarIndex (capacity noise latency : ℚ) : ℚ :=
  capacity / (noise * latency)

/-- Positivity is a mathematical property of the declared index. -/
theorem scalarIndex_pos {b i τ : ℚ}
    (hb : 0 < b) (hi : 0 < i) (hτ : 0 < τ) :
    0 < scalarIndex b i τ := by
  unfold scalarIndex
  exact div_pos hb (mul_pos hi hτ)

/-- The saturating transform lies in the unit interval under explicit assumptions. -/
theorem normalizedIndex_bounds {b i τ : ℚ}
    (hb : 0 ≤ b) (hi : 0 < i) (hτ : 0 < τ) :
    0 ≤ b / (b + i * τ) ∧ b / (b + i * τ) ≤ 1 := by
  have hprod : 0 < i * τ := mul_pos hi hτ
  have hden : 0 < b + i * τ := add_pos_of_nonneg_of_pos hb hprod
  constructor
  · exact div_nonneg hb (le_of_lt hden)
  · apply (div_le_iff₀ hden).2
    nlinarith

/-- Adjacency of a path on six labeled vertices (the labels are not a metric). -/
def pathAdj (v w : Fin 6) : ℚ :=
  if v.val + 1 = w.val ∨ w.val + 1 = v.val then 1 else 0

/-- Adjacency of the six-vertex star centered at vertex zero. -/
def starAdj (v w : Fin 6) : ℚ :=
  if (v.val = 0 ∧ w.val ≠ 0) ∨ (w.val = 0 ∧ v.val ≠ 0) then 1 else 0

/-- One synchronous graph-Laplacian consensus update with gain 1/10. -/
def update (adj : Fin 6 → Fin 6 → ℚ)
    (x : Fin 6 → ℚ) (v : Fin 6) : ℚ :=
  x v - (1 / 10 : ℚ) * ∑ w : Fin 6, adj v w * (x v - x w)

/-- The same zero-mean initial perturbation is used on both networks. -/
def initial (v : Fin 6) : ℚ :=
  if v.val = 0 then 1 else if v.val = 1 then -1 else 0

/-- Exact rational evaluation at vertex zero of the path after one update. -/
theorem path_update_vertex_zero :
    update pathAdj initial 0 = (4 / 5 : ℚ) := by
  norm_num [update, pathAdj, initial, Fin.sum_univ_succ]

/-- Exact rational evaluation at vertex zero of the star after one update. -/
theorem star_update_vertex_zero :
    update starAdj initial 0 = (2 / 5 : ℚ) := by
  norm_num [update, starAdj, initial, Fin.sum_univ_succ]

/-- Equal declared scalar inputs do not fix a one-step network response. -/
theorem equal_scalar_inputs_different_update :
    scalarIndex 1 (1 / 100) 1 = scalarIndex 1 (1 / 100) 1 ∧
    update pathAdj initial 0 ≠ update starAdj initial 0 := by
  constructor
  · rfl
  · rw [path_update_vertex_zero, star_update_vertex_zero]
    norm_num

/-- A separate exact scalar-dynamics witness: distinct response gains. -/
theorem distinct_gains_twenty_steps :
    (1 / 2 : ℚ) ^ 20 ≠ (9 / 10 : ℚ) ^ 20 := by
  norm_num

end RelationalPersistence
