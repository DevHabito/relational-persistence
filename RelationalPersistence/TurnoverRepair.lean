import RelationalPersistence.FunctionalContinuity

/-!
# RP-U002-A01: exact finite bottleneck repair / identity turnover

Prerequisite RP-U001 gave the specific B graph:
0-1, 0-3, 1-2, 3-2, 2-5, 2-4, 4-5.
Delete original node 2 at t=1 and replace it with NEW node 8
at t=2, adding edges to its old neighbors in ASCENDING order:
(8,1), then (8,3), then (8,4), then (8,5).

Proof is deliberately only a finite Bool computation about the
explicit snapshots and declared reachability evaluator. It does
NOT verify arbitrary algorithms, the Python simulator, real
biology or a new graph theorem. Old node identity 2 is absent
from ALL post-failure snapshots.
-/

namespace RelationalPersistence.TurnoverRepair

abbrev Edge := Nat × Nat

def remainingB : List Edge :=
  [(0, 1), (0, 3), (4, 5)]

def atT1 : List Edge := remainingB

def atT2 : List Edge := remainingB ++ [(8, 1)]

def atT3 : List Edge := atT2 ++ [(8, 3)]

def atT4 : List Edge := atT3 ++ [(8, 4)]

def atT5 : List Edge := atT4 ++ [(8, 5)]

def replacementVertices : List Nat := [0, 1, 3, 4, 5, 8]

def expand (edges : List Edge) (visited : List Nat) : List Nat :=
  replacementVertices.filter (fun vertex =>
    visited.contains vertex ||
      visited.any (fun u =>
        RelationalPersistence.FunctionalContinuity.isEdge edges u vertex))

def connectivity (edges : List Edge) : Bool :=
  let visited0 : List Nat := [0]
  let visited1 := expand edges visited0
  let visited2 := expand edges visited1
  let visited3 := expand edges visited2
  let visited4 := expand edges visited3
  let visited5 := expand edges visited4
  visited5.contains 5

/-- Node replacement plus ONE and TWO restored relationships do not
recover the fixed B graph's specified terminal connectivity. -/
theorem original_bottleneck_is_not_repaired_by_node_count_alone :
    connectivity atT1 = false ∧
    connectivity atT2 = false ∧
    connectivity atT3 = false := by
  decide

/-- Reattaching the third old relationship reconnects source and target.
This is a concrete finite witness, not a general repair-time theorem. -/
theorem third_and_fourth_links_restore_defined_function :
    connectivity atT4 = true ∧
    connectivity atT5 = true := by
  decide

/-- The number of present components at t=2 is identical to baseline.
The original identity 2 was replaced by distinct identity 8, and the
declared B bottleneck function has NOT recovered. -/
theorem equal_component_count_does_not_force_functional_continuity :
    replacementVertices.length = 6 ∧
    replacementVertices.contains 2 = false ∧
    replacementVertices.contains 8 = true ∧
    connectivity atT2 = false ∧
    RelationalPersistence.FunctionalContinuity.stillConnected
      RelationalPersistence.FunctionalContinuity.edgesB 6 = true := by
  decide

end RelationalPersistence.TurnoverRepair
