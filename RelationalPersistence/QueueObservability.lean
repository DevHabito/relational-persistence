import Mathlib

/-!
# RP-F006-A01 — Equal observable queue state, unequal admissible waits

A fixed finite FCFS-compatible three-job witness is checked separately
with exact rational event reconstruction in Python. This file proves
ONLY the algebraic consequence once both worlds have the SAME observable
tuple but different future target waits, exactly 1 and 100 seconds.

The bound is an immediate instance of the classical triangle inequality.
This is not a new queueing theorem, a proof of the FCFS event-simulator
implementation, a physical persistence law, or an impossibility claim
about statistical prediction over observed real HPC populations.
-/

namespace RelationalPersistence

/-- An intentionally incomplete but causally public finite observation.
The Python witness also compares complete pre-origin event streams. -/
structure QueueObservation where
  qPrevious : Nat
  qLatest : Nat
  qAtOrigin : Nat
  pastStartedCount : Nat
  historicalWait : ℚ
  runningStartedAt : ℤ
  runningRequestedWalltime : Nat
  runningAge : Nat
  targetRequestedProcessors : Nat
  deriving DecidableEq, Repr

/-- Shared pre-origin information in the registered two-world witness. -/
def sharedQueueObservation : QueueObservation :=
  { qPrevious := 0
    qLatest := 0
    qAtOrigin := 0
    pastStartedCount := 1
    historicalWait := 1
    runningStartedAt := -30
    runningRequestedWalltime := 500
    runningAge := 30
    targetRequestedProcessors := 1 }

/-- Abstract future completion choice, not itself an observed feature. -/
structure QueueCompletionWorld where
  observed : QueueObservation
  futureRunningCompletion : Nat

def shortQueueWorld : QueueCompletionWorld :=
  ⟨sharedQueueObservation, 1⟩

def longQueueWorld : QueueCompletionWorld :=
  ⟨sharedQueueObservation, 100⟩

/-- The target submits at 0 and begins exactly upon current job completion. -/
def queueTargetWait (world : QueueCompletionWorld) : ℝ :=
  (world.futureRunningCompletion : ℝ)

theorem queue_world_observations_equal :
    shortQueueWorld.observed = longQueueWorld.observed := by
  rfl

theorem queue_world_target_waits_unequal :
    queueTargetWait shortQueueWorld ≠ queueTargetWait longQueueWorld := by
  norm_num [queueTargetWait, shortQueueWorld, longQueueWorld]

/-- Triangle inequality: both incompatible waits cannot be predicted
perfectly by one common real-valued output. -/
theorem queue_two_world_error_sum_lower_bound (p : ℝ) :
    (99 : ℝ) ≤ |p - 1| + |p - 100| := by
  have h := abs_sub_le (1 : ℝ) p 100
  have h99 : |(1 : ℝ) - 100| = 99 := by norm_num
  rw [h99, abs_sub_comm (1 : ℝ) p] at h
  exact h

/-- Sharp minimax worst-case absolute-error bound, in synthetic seconds. -/
theorem queue_two_world_minimax_lower_bound (p : ℝ) :
    (99 / 2 : ℝ) ≤ max |p - 1| |p - 100| := by
  have hsum := queue_two_world_error_sum_lower_bound p
  have hleft : |p - 1| ≤ max |p - 1| |p - 100| := le_max_left _ _
  have hright : |p - 100| ≤ max |p - 1| |p - 100| := le_max_right _ _
  linarith

/-- 101/2 attains the lower bound, so it is sharp for this finite pair. -/
theorem queue_two_world_minimax_attained :
    max |(101 / 2 : ℝ) - 1| |(101 / 2 : ℝ) - 100| = 99 / 2 := by
  norm_num

/-- A predictor observing only the shared input must output the same
real number for both different target waits. -/
theorem queue_no_perfect_observation_only_predictor
    (predict : QueueObservation → ℝ) :
    (99 / 2 : ℝ) ≤
      max
        |predict shortQueueWorld.observed - queueTargetWait shortQueueWorld|
        |predict longQueueWorld.observed - queueTargetWait longQueueWorld| := by
  change (99 / 2 : ℝ) ≤
    max |predict sharedQueueObservation - 1|
        |predict sharedQueueObservation - 100|
  exact queue_two_world_minimax_lower_bound (predict sharedQueueObservation)

end RelationalPersistence
