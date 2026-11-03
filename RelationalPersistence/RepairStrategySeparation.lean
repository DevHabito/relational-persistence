import RelationalPersistence.FunctionalContinuity

/-!
# RP-U003-F01: finite, previously observed F1/F2 policy separation

The exact frozen case and the non-blind audit status are in
`docs/preregistration/RP-U003-F01.md`.

All statements below concern TWO explicit six-vertex synthetic states.
They do not prove the Python policy algorithm, Menger's theorem, or any
cross-network or physical statement. Enumerated paths and vertex cuts
are separately evaluated to guard this fixed graph witness.
-/

namespace RelationalPersistence.RepairStrategySeparation

abbrev Edge := Nat × Nat

private def isEdge (edges : List Edge) (u v : Nat) : Bool :=
  RelationalPersistence.FunctionalContinuity.isEdge edges u v

/-- The seven undirected source edges, before loss of vertex 3. -/
def sourceEdges : List Edge :=
  [(0, 1), (0, 2), (1, 3), (1, 4), (1, 5), (2, 3), (3, 5)]

/-- Remove vertex 3 and its incident edges; it never reappears. -/
def remainingEdges : List Edge :=
  sourceEdges.filter (fun e => e.1 != 3 && e.2 != 3)

/-- The six present identities after replacing original 3 with NEW 9. -/
def presentVertices : List Nat := [0, 1, 2, 4, 5, 9]

/-- Frozen GREEDY1 first two choices: 1, then 2. -/
def greedyRepaired : List Edge := [(9, 1), (9, 2)]

/-- Frozen LOOKAHEAD2 first two choices: 2, then 5. -/
def lookaheadRepaired : List Edge := [(9, 2), (9, 5)]

def greedyAtT3 : List Edge := remainingEdges ++ greedyRepaired
def lookaheadAtT3 : List Edge := remainingEdges ++ lookaheadRepaired

/-- Bounded graph closure; at most five edges occur in a simple path of six vertices. -/
private def expand (edges : List Edge) (removed : Nat) (seen : List Nat) : List Nat :=
  presentVertices.filter (fun vertex =>
    vertex != removed &&
      (seen.contains vertex || seen.any (fun u => isEdge edges u vertex)))

/-- Exact terminal reachability for the two six-vertex frozen states. -/
def reachable (edges : List Edge) (removed : Nat) : Bool :=
  let s0 : List Nat := [0]
  let s1 := expand edges removed s0
  let s2 := expand edges removed s1
  let s3 := expand edges removed s2
  let s4 := expand edges removed s3
  let s5 := expand edges removed s4
  s5.contains 5

/-- Exhaustive simple-path enumeration over the fixed present vertices. -/
private def pathsFrom (edges : List Edge) : Nat → List Nat → List (List Nat)
  | 0, _ => []
  | fuel + 1, path =>
    if path.getLast? == some 5 then [path]
    else
      presentVertices.flatMap (fun next =>
        if path.contains next || !(isEdge edges (path.getLast!) next) then []
        else pathsFrom edges fuel (path ++ [next]))

/-- All simple terminal paths; no path can use more than five edges. -/
def simpleTerminalPaths (edges : List Edge) : List (List Nat) :=
  pathsFrom edges 6 [0]

private def internalVertices (path : List Nat) : List Nat :=
  path.filter (fun vertex => vertex != 0 && vertex != 5)

private def internallyDisjoint (first second : List Nat) : Bool :=
  (internalVertices first).all (fun vertex =>
    !((internalVertices second).contains vertex))

/-- F2 oracle A: enumerate pairs of distinct internally disjoint simple routes. -/
def f2ByPaths (edges : List Edge) : Bool :=
  let paths := simpleTerminalPaths edges
  paths.any (fun p =>
    paths.any (fun q => p != q && internallyDisjoint p q))

/-- F2 oracle B: finite one-internal-vertex deletion check, with F1. -/
def f2ByCuts (edges : List Edge) : Bool :=
  reachable edges 10 &&
    ([1, 2, 4, 9] : List Nat).all (fun vertex => reachable edges vertex)

/-- Check the exact source filtration and matched reconstruction budgets. -/
theorem frozen_repair_costs_and_replacement :
    remainingEdges = [(0, 1), (0, 2), (1, 4), (1, 5)] ∧
    presentVertices.length = 6 ∧
    presentVertices.contains 3 = false ∧
    presentVertices.contains 9 = true ∧
    greedyRepaired.length = 2 ∧
    lookaheadRepaired.length = 2 ∧
    greedyAtT3.length = lookaheadAtT3.length := by
  decide

/-- Same F1 outcome for both repaired states. -/
theorem both_policies_retain_f1 :
    reachable greedyAtT3 10 = true ∧
    reachable lookaheadAtT3 10 = true := by
  decide

/-- Independent F2 encodings agree on EACH fixed repaired state. -/
theorem independent_f2_oracles_agree :
    f2ByPaths greedyAtT3 = f2ByCuts greedyAtT3 ∧
    f2ByPaths lookaheadAtT3 = f2ByCuts lookaheadAtT3 := by
  decide

/-- Two explicit internally disjoint routes occur in the path enumeration. -/
theorem lookahead_has_two_explicit_routes :
    ([0, 1, 5] : List Nat) ∈ simpleTerminalPaths lookaheadAtT3 ∧
    ([0, 2, 9, 5] : List Nat) ∈ simpleTerminalPaths lookaheadAtT3 ∧
    internallyDisjoint [0, 1, 5] [0, 2, 9, 5] = true := by
  decide

/-- The one-step rule has a terminal cut at internal vertex 1. -/
theorem greedy_needs_vertex_one :
    reachable greedyAtT3 1 = false := by
  decide

/-- In this exact example, the path oracle distinguishes the strategies. -/
theorem equal_f1_but_distinct_f2 :
    f2ByPaths greedyAtT3 = false ∧
    f2ByPaths lookaheadAtT3 = true := by
  decide

/-- The separate cut oracle independently gives the same contrast. -/
theorem cut_oracle_separation :
    f2ByCuts greedyAtT3 = false ∧
    f2ByCuts lookaheadAtT3 = true := by
  decide

end RelationalPersistence.RepairStrategySeparation
