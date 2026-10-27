import Mathlib

/-!
# RP-U001-A01: finite Bool reachability after a single component loss

These are predeclared toy graphs with six named vertices, two fixed
terminals (0 and 5), and exactly seven undirected edges EACH.
Reachability is checked for a fixed number of graph-expansion steps,
sufficient for a simple path on six vertices.

This computational certificate is ONLY about the specific finite
listed graphs. The BFS/DFS Python implementations separately compute
all two-node and higher loss subsets and their stronger operational
function. Classical graph connectivity is NOT a newly discovered
ecological law. No real forest or medical system was measured.
-/

namespace RelationalPersistence.FunctionalContinuity

abbrev Edge := Nat × Nat

def edgesA : List Edge :=
  [(0, 1), (1, 2), (2, 5), (0, 3), (3, 4), (4, 5), (1, 3)]

def edgesB : List Edge :=
  [(0, 1), (0, 3), (1, 2), (3, 2), (2, 5), (2, 4), (4, 5)]

def isEdge (edges : List Edge) (u v : Nat) : Bool :=
  edges.any (fun e =>
    (e.1 == u && e.2 == v) || (e.1 == v && e.2 == u))

def expansion (edges : List Edge) (removed : Nat) (visited : List Nat) : List Nat :=
  ([0, 1, 2, 3, 4, 5] : List Nat).filter (fun vertex =>
    vertex != removed &&
      (visited.contains vertex ||
        visited.any (fun u => isEdge edges u vertex)))

def stillConnected (edges : List Edge) (removed : Nat) : Bool :=
  let initial : List Nat := [0]
  let after1 := expansion edges removed initial
  let after2 := expansion edges removed after1
  let after3 := expansion edges removed after2
  let after4 := expansion edges removed after3
  let after5 := expansion edges removed after4
  after5.contains 5

/-- Graph A retains the declared one-path function after any ONE
    nonterminal vertex deletion. Entirely finite Bool certificate. -/
theorem graphA_one_component_loss :
    stillConnected edgesA 1 = true ∧
    stillConnected edgesA 2 = true ∧
    stillConnected edgesA 3 = true ∧
    stillConnected edgesA 4 = true := by
  decide

/-- Graph B has the specifically preregistered bottleneck at node 2.
    This does not say the graph never carries a function. -/
theorem graphB_one_component_loss :
    stillConnected edgesB 1 = true ∧
    stillConnected edgesB 2 = false ∧
    stillConnected edgesB 3 = true ∧
    stillConnected edgesB 4 = true := by
  decide

/-- Both initial networks have the designated source-to-target route. -/
theorem same_initial_reachability :
    stillConnected edgesA 6 = true ∧
    stillConnected edgesB 6 = true := by
  decide

end RelationalPersistence.FunctionalContinuity
