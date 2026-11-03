import Mathlib

/-!
# RP-U004-F01 — Nested Boolean repair functions collapse two priority orders

This is an **after-result** formalization of the scoring redundancy described
in `docs/results/RP-U004-P01.md`. The proof scope was written down separately
in `docs/formalization/RP-U004-F01-SCOPE.md` before this module.

There are only three admissible Boolean function states because F2 implies F1.
For these states, prioritizing F1 before F2 or F2 before F1 induces the same
ranking, including the same lower-label tie break and two-step pairwise ranking.

This certifies a finite Boolean order fact. It does NOT establish global
optimality of a repair strategy, correctness of the Python implementation,
physical resilience, or a novel theorem in graph connectivity.
-/

namespace RelationalPersistence.BooleanRepairRank

/-- The task-specific Boolean state is (at least one route, two disjoint routes). -/
abbrev Outcome := Bool × Bool

/-- Two independent paths imply at least one path; false F1 with true F2 is invalid. -/
def admissible (score : Outcome) : Bool := !score.2 || score.1

/-- Numeric encoding of lexicographic F1-then-F2 preference. -/
def rankF1First (score : Outcome) : Nat :=
  (if score.1 then 2 else 0) + (if score.2 then 1 else 0)

/-- Numeric encoding of lexicographic F2-then-F1 preference. -/
def rankF2First (score : Outcome) : Nat :=
  (if score.2 then 2 else 0) + (if score.1 then 1 else 0)

/-- Only three Boolean score combinations satisfy F2 ⇒ F1. -/
theorem exactly_three_admissible_scores :
    ∀ score : Outcome,
      admissible score = true ↔
        score = (false, false) ∨
        score = (true, false) ∨
        score = (true, true) := by
  decide

/-- For every pair of admissible states, strict ranking is independent of which
    of the nested functions is listed first. -/
theorem strict_rank_order_agrees :
    ∀ a b : Outcome,
      admissible a = true →
      admissible b = true →
      (rankF1First a > rankF1First b ↔
       rankF2First a > rankF2First b) := by
  decide

/-- The two priorities also classify score ties identically. -/
theorem tie_rank_order_agrees :
    ∀ a b : Outcome,
      admissible a = true →
      admissible b = true →
      (rankF1First a = rankF1First b ↔
       rankF2First a = rankF2First b) := by
  decide

/-- A greedy candidate comparison with a lowest-label tie breaker agrees
    between the two Boolean priorities, for arbitrary labels. -/
theorem greedy_candidate_preference_agrees
    (a b : Outcome) (labelA labelB : Nat)
    (ha : admissible a = true) (hb : admissible b = true) :
    (rankF1First a > rankF1First b ∨
       (rankF1First a = rankF1First b ∧ labelA < labelB)) ↔
    (rankF2First a > rankF2First b ∨
       (rankF2First a = rankF2First b ∧ labelA < labelB)) := by
  have hStrict := strict_rank_order_agrees a b ha hb
  have hTie := tie_rank_order_agrees a b ha hb
  constructor
  · intro h
    rcases h with h | ⟨he, hl⟩
    · exact Or.inl (hStrict.mp h)
    · exact Or.inr ⟨hTie.mp he, hl⟩
  · intro h
    rcases h with h | ⟨he, hl⟩
    · exact Or.inl (hStrict.mpr h)
    · exact Or.inr ⟨hTie.mpr he, hl⟩

/-- The two-step comparator first ranks the best future Boolean score,
    then the immediate score, then the same candidate label. All future
    and immediate scores must separately satisfy F2 ⇒ F1. -/
theorem two_step_candidate_preference_agrees
    (futureA currentA futureB currentB : Outcome)
    (labelA labelB : Nat)
    (hfa : admissible futureA = true)
    (hfb : admissible futureB = true)
    (hca : admissible currentA = true)
    (hcb : admissible currentB = true) :
    (rankF1First futureA > rankF1First futureB ∨
       (rankF1First futureA = rankF1First futureB ∧
         (rankF1First currentA > rankF1First currentB ∨
           (rankF1First currentA = rankF1First currentB ∧ labelA < labelB)))) ↔
    (rankF2First futureA > rankF2First futureB ∨
       (rankF2First futureA = rankF2First futureB ∧
         (rankF2First currentA > rankF2First currentB ∨
           (rankF2First currentA = rankF2First currentB ∧ labelA < labelB)))) := by
  have hfStrict := strict_rank_order_agrees futureA futureB hfa hfb
  have hfTie := tie_rank_order_agrees futureA futureB hfa hfb
  have hcStrict := strict_rank_order_agrees currentA currentB hca hcb
  have hcTie := tie_rank_order_agrees currentA currentB hca hcb
  constructor
  · intro h
    rcases h with h | ⟨he, hc⟩
    · exact Or.inl (hfStrict.mp h)
    · apply Or.inr
      constructor
      · exact hfTie.mp he
      · rcases hc with hCurrent | ⟨heCurrent, hl⟩
        · exact Or.inl (hcStrict.mp hCurrent)
        · exact Or.inr ⟨hcTie.mp heCurrent, hl⟩
  · intro h
    rcases h with h | ⟨he, hc⟩
    · exact Or.inl (hfStrict.mpr h)
    · apply Or.inr
      constructor
      · exact hfTie.mpr he
      · rcases hc with hCurrent | ⟨heCurrent, hl⟩
        · exact Or.inl (hcStrict.mpr hCurrent)
        · exact Or.inr ⟨hcTie.mpr heCurrent, hl⟩

/-- Without the F2 ⇒ F1 premise, F1-first and F2-first can rank two
    Boolean states in opposite orders. The first state is admissible;
    the second is not a possible F1/F2 path state. -/
theorem nesting_assumption_is_necessary :
    admissible (true, false) = true ∧
    admissible (false, true) = false ∧
    rankF1First (true, false) > rankF1First (false, true) ∧
    rankF2First (true, false) < rankF2First (false, true) := by
  decide

end RelationalPersistence.BooleanRepairRank
