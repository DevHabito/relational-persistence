import Mathlib

/-!
# RP-U005: finite queue backlog as a separate operational state

These elementary Nat arithmetic facts support a strictly synthetic
four-node restoration witness. The formal statements do not identify real
network service capacity from graph connectivity, prove the Python program,
or establish a physical/biological theory.
-/

namespace RelationalPersistence

/-- Exact end-of-tick backlog when a bounded number of jobs can be served. -/
def finiteBacklogStep (backlog arrivals capacity : ℕ) : ℕ :=
  backlog + arrivals - capacity

/-- Matched intake and service leave any inherited backlog unchanged. -/
theorem balanced_service_preserves_backlog (backlog arrivals : ℕ) :
    finiteBacklogStep backlog arrivals arrivals = backlog := by
  dsimp [finiteBacklogStep]
  omega

/-- Enough service for current arrivals does not create a new backlog. -/
theorem no_backlog_when_service_covers_arrivals
    (arrivals capacity : ℕ) (h : arrivals ≤ capacity) :
    finiteBacklogStep 0 arrivals capacity = 0 := by
  dsimp [finiteBacklogStep]
  omega

/-- With an existing backlog and strict surplus service, backlog falls. -/
theorem surplus_service_strictly_decreases_positive_backlog
    (backlog arrivals capacity : ℕ)
    (hpos : 0 < backlog) (hsurplus : arrivals < capacity) :
    finiteBacklogStep backlog arrivals capacity < backlog := by
  dsimp [finiteBacklogStep]
  omega

/-- Three overloaded one-slot ticks each receiving two jobs yield three queued. -/
theorem registered_three_failed_ticks_build_backlog :
    finiteBacklogStep
      (finiteBacklogStep
        (finiteBacklogStep 0 2 1) 2 1) 2 1 = 3 := by
  decide

/-- After repair, three two-slot ticks with one new job drain a backlog of three. -/
theorem registered_surplus_three_ticks_drain :
    finiteBacklogStep
      (finiteBacklogStep
        (finiteBacklogStep 3 1 2) 1 2) 1 2 = 0 := by
  decide

/-- Repaired two-slot service exactly matching two arrivals does not drain. -/
theorem registered_balanced_three_ticks_keep_backlog :
    finiteBacklogStep
      (finiteBacklogStep
        (finiteBacklogStep 3 2 2) 2 2) 2 2 = 3 := by
  decide

end RelationalPersistence
