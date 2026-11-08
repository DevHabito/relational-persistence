import Mathlib

/-!
# RP-U004-C01 — Retrospective additive lookup-price sensitivity

This is an algebraic observation about **already published** finite RP-U004
aggregate counts, scoped in `docs/formalization/RP-U004-C01-SCOPE.md`
before this module was written. It is NOT a prediction of real repair
outcomes, a proof of Python code, or a new optimization theorem.

The accounting price is measured in synthetic successful scenario-ticks per
instrumented truth-table lookup. No physical conversion factor is known.
-/

namespace RelationalPersistence.RepairDecisionCost

/-- Greedy F2 case-ticks minus a hypothetical constant price per lookup. -/
def greedyF2Net (price : ℚ) : ℚ := 3286 - 28450 * price

/-- Two-step F2 case-ticks minus the same hypothetical lookup price. -/
def lookaheadF2Net (price : ℚ) : ℚ := 3386 - 53410 * price

/-- The same accounting convention for the dependent F1 observable. -/
def greedyF1Net (price : ℚ) : ℚ := 16046 - 28450 * price

def lookaheadF1Net (price : ℚ) : ℚ := 16052 - 53410 * price

/-- At zero hypothetical lookup price, the published F2 difference is 100. -/
theorem f2_difference_at_zero :
    lookaheadF2Net 0 - greedyF2Net 0 = 100 := by
  norm_num [lookaheadF2Net, greedyF2Net]

/-- Strict F2 net advantage holds exactly below the rational threshold. -/
theorem f2_lookahead_advantage_iff (price : ℚ) :
    lookaheadF2Net price > greedyF2Net price ↔ price < (5 : ℚ) / 1248 := by
  unfold lookaheadF2Net greedyF2Net
  constructor <;> intro h <;> linarith

/-- At exactly the threshold, both retrospective accounting scores tie. -/
theorem f2_tie_iff (price : ℚ) :
    lookaheadF2Net price = greedyF2Net price ↔ price = (5 : ℚ) / 1248 := by
  unfold lookaheadF2Net greedyF2Net
  constructor <;> intro h <;> linarith

/-- Above the threshold, the same hypothetical accounting favors greedy. -/
theorem f2_greedy_advantage_iff (price : ℚ) :
    lookaheadF2Net price < greedyF2Net price ↔ price > (5 : ℚ) / 1248 := by
  unfold lookaheadF2Net greedyF2Net
  constructor <;> intro h <;> linarith

/-- The F1 sensitivity threshold is smaller; F1 is NOT independent evidence. -/
theorem f1_lookahead_advantage_iff (price : ℚ) :
    lookaheadF1Net price > greedyF1Net price ↔ price < (1 : ℚ) / 4160 := by
  unfold lookaheadF1Net greedyF1Net
  constructor <;> intro h <;> linarith

theorem f1_tie_iff (price : ℚ) :
    lookaheadF1Net price = greedyF1Net price ↔ price = (1 : ℚ) / 4160 := by
  unfold lookaheadF1Net greedyF1Net
  constructor <;> intro h <;> linarith

theorem f1_greedy_advantage_iff (price : ℚ) :
    lookaheadF1Net price < greedyF1Net price ↔ price > (1 : ℚ) / 4160 := by
  unfold lookaheadF1Net greedyF1Net
  constructor <;> intro h <;> linarith

end RelationalPersistence.RepairDecisionCost
