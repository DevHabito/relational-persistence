import Mathlib

/-!
# RP-F005: real exact gain-one delayed-feedback witness

For the frozen scalar model x[t+1] = x[t] - x[t-d], compare delay
d = 0 with delay d = 1. The delay-one augmented transition is
(current, previous) ↦ (current - previous, current).

The proof is over all real initial pairs, not merely rational test
vectors. It is NOT a theorem about arbitrary gains, physical response
times, noisy systems, or all discrete-time stability criteria.
-/

namespace RelationalPersistence

structure FeedbackPair where
  current : ℝ
  previous : ℝ

/-- A genuine one-time-step state delay at feedback gain one. -/
def delayedFeedbackStep (s : FeedbackPair) : FeedbackPair :=
  ⟨s.current - s.previous, s.current⟩

/-- Six or more iterates use the original recursive delayed operator. -/
def delayedFeedbackIter : Nat → FeedbackPair → FeedbackPair
  | 0, s => s
  | n + 1, s => delayedFeedbackStep (delayedFeedbackIter n s)

/-- The no-delay gain-one operator annihilates any scalar state. -/
def undelayedFeedbackStep (x : ℝ) : ℝ := x - x

def undelayedFeedbackIter : Nat → ℝ → ℝ
  | 0, x => x
  | n + 1, x => undelayedFeedbackStep (undelayedFeedbackIter n x)

def feedbackSquaredEnergy (s : FeedbackPair) : ℝ :=
  s.current ^ 2 + s.previous ^ 2

/-- The delayed transition's cube is negative identity on all real states. -/
theorem delayed_feedback_three_is_negative (s : FeedbackPair) :
    (delayedFeedbackIter 3 s).current = -s.current ∧
    (delayedFeedbackIter 3 s).previous = -s.previous := by
  cases s with
  | mk a b =>
    constructor <;>
      dsimp [delayedFeedbackIter, delayedFeedbackStep] <;>
      ring

/-- The delayed transition's sixth power is exactly identity over ℝ². -/
theorem delayed_feedback_six_is_identity (s : FeedbackPair) :
    delayedFeedbackIter 6 s = s := by
  cases s with
  | mk a b =>
    dsimp [delayedFeedbackIter, delayedFeedbackStep] <;>
      congr 1 <;> ring

theorem undelayed_feedback_one_is_zero (x : ℝ) :
    undelayedFeedbackStep x = 0 := by
  simp [undelayedFeedbackStep]

theorem undelayed_feedback_six_is_zero (x : ℝ) :
    undelayedFeedbackIter 6 x = 0 := by
  simp [undelayedFeedbackIter, undelayedFeedbackStep]

theorem delayed_feedback_primary_witness :
    (delayedFeedbackIter 6 ⟨1, 1⟩).current = (1 : ℝ) := by
  rw [delayed_feedback_six_is_identity]

/-- Precommitted residual contrast: exactly one vs zero after six steps. -/
theorem delayed_feedback_registered_separation :
    (1 / 2 : ℝ) ≤
      (delayedFeedbackIter 6 ⟨1, 1⟩).current ^ 2 -
      (undelayedFeedbackIter 6 1) ^ 2 := by
  rw [delayed_feedback_six_is_identity]
  norm_num [undelayed_feedback_six_is_zero]

/-- A period-six identity rules out strict six-step energy contraction. -/
theorem delayed_feedback_no_uniform_strict_six_contraction
    (q : ℝ) (hq : q < 1) :
    ¬ (∀ s : FeedbackPair,
      feedbackSquaredEnergy (delayedFeedbackIter 6 s) ≤
        q * feedbackSquaredEnergy s) := by
  intro h
  have hs := h ⟨1, 1⟩
  rw [delayed_feedback_six_is_identity] at hs
  dsimp [feedbackSquaredEnergy] at hs
  nlinarith

end RelationalPersistence
