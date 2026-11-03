import Mathlib

/-!
# RP-U004-F01: identical rankings for nested Boolean objectives

This is a retrospective finite-order formalization. The RP-U004 first
outcome and the objective redundancy were known before these theorems
were written. The proof protocol is docs/preregistration/RP-U004-F01.md.

F2 implies F1 in the declared graph task. This module is only about
Boolean score ordering, not arbitrary graph repair policies, numeric
losses, physical persistence or a new graph theorem.
-/

namespace RelationalPersistence.BooleanObjectiveOrder

/-- F2 cannot be true while F1 is false. -/
def nested (score : Bool × Bool) : Prop :=
  score.2 = true → score.1 = true

/-- Numeric encoding of the lexicographic priority (F1,F2). -/
def f1PriorityKey (score : Bool × Bool) : Nat :=
  (if score.1 then 2 else 0) + (if score.2 then 1 else 0)

/-- Numeric encoding of the lexicographic priority (F2,F1). -/
def f2PriorityKey (score : Bool × Bool) : Nat :=
  (if score.2 then 2 else 0) + (if score.1 then 1 else 0)

/-- Only the three stated Boolean score pairs obey F2 ⇒ F1. -/
theorem nested_scores_are_exactly_three (score : Bool × Bool) :
    nested score ↔
      score = (false, false) ∨
      score = (true, false) ∨
      score = (true, true) := by
  rcases score with ⟨first, second⟩
  cases first <;> cases second <;> decide

/-- Prioritizing F1 or F2 produces the same strict comparison. -/
theorem strict_rank_order_is_identical (a b : Bool × Bool)
    (ha : nested a) (hb : nested b) :
    (f1PriorityKey a < f1PriorityKey b ↔
     f2PriorityKey a < f2PriorityKey b) := by
  rcases a with ⟨a1, a2⟩
  rcases b with ⟨b1, b2⟩
  cases a1 <;> cases a2 <;> cases b1 <;> cases b2 <;>
    simp_all [nested, f1PriorityKey, f2PriorityKey]

/-- Both priorities detect the same exact score ties. -/
theorem rank_ties_are_identical (a b : Bool × Bool)
    (ha : nested a) (hb : nested b) :
    (f1PriorityKey a = f1PriorityKey b ↔
     f2PriorityKey a = f2PriorityKey b) := by
  rcases a with ⟨a1, a2⟩
  rcases b with ⟨b1, b2⟩
  cases a1 <;> cases a2 <;> cases b1 <;> cases b2 <;>
    simp_all [nested, f1PriorityKey, f2PriorityKey]

/-- Lexicographically comparing a future score before an immediate
score gives the same ordering under the two Boolean priority labels. -/
theorem two_step_lex_rank_is_identical
    (futureA nowA futureB nowB : Bool × Bool)
    (hfa : nested futureA) (hna : nested nowA)
    (hfb : nested futureB) (hnb : nested nowB) :
    ((f1PriorityKey futureA < f1PriorityKey futureB) ∨
      (f1PriorityKey futureA = f1PriorityKey futureB ∧
       f1PriorityKey nowA < f1PriorityKey nowB)) ↔
    ((f2PriorityKey futureA < f2PriorityKey futureB) ∨
      (f2PriorityKey futureA = f2PriorityKey futureB ∧
       f2PriorityKey nowA < f2PriorityKey nowB)) := by
  rw [strict_rank_order_is_identical futureA futureB hfa hfb,
      rank_ties_are_identical futureA futureB hfa hfb,
      strict_rank_order_is_identical nowA nowB hna hnb]

/-- The two priorities also agree on exact future+immediate ties. -/
theorem two_step_ties_are_identical
    (futureA nowA futureB nowB : Bool × Bool)
    (hfa : nested futureA) (hna : nested nowA)
    (hfb : nested futureB) (hnb : nested nowB) :
    (f1PriorityKey futureA = f1PriorityKey futureB ∧
     f1PriorityKey nowA = f1PriorityKey nowB) ↔
    (f2PriorityKey futureA = f2PriorityKey futureB ∧
     f2PriorityKey nowA = f2PriorityKey nowB) := by
  rw [rank_ties_are_identical futureA futureB hfa hfb,
      rank_ties_are_identical nowA nowB hna hnb]

end RelationalPersistence.BooleanObjectiveOrder
