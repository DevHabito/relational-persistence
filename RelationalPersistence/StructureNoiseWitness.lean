import Mathlib

/-!
# RP-S001-F01 — Retrospective, finite edge-failure witness

Two explicit six-vertex eight-edge graphs have the same labeled degree
vector but, under *exactly two* edge removals, different terminal reachability
counts. The proofs independently enumerate all 28 deletion pairs using
a finite (five-step) closure traversal, and certify three-step rational
temporal comparisons.

This material was written **after** the first registered RP-S001-P01 result.
It is an elementary finite combinatorial certificate, not a new theorem of
graph connectivity or a proof of the experiment's complete 540-graph family.
The prior literature on graph reliability and Menger's theorem remains primary.
-/

namespace RelationalPersistence.StructureNoiseWitness

private abbrev Edge := Nat × Nat

def graphA : List Edge :=
  [(0,1), (0,2), (1,2), (1,3), (1,4), (1,5), (2,3), (4,5)]

def graphB : List Edge :=
  [(0,1), (0,2), (1,2), (1,3), (1,4), (1,5), (2,5), (3,4)]

def labeledDegree (edges : List Edge) (v : Nat) : Nat :=
  (edges.filter (fun e => e.1 == v || e.2 == v)).length

def degreeProfile (edges : List Edge) : List Nat :=
  (List.range 6).map (labeledDegree edges)

/-- The edge list has a strictly indexed deletion rule, not a random source. -/
def deleteTwo (edges : List Edge) (i j : Nat) : List Edge :=
  (edges.zipIdx.filter (fun e => e.2 != i && e.2 != j)).map Prod.fst

def deleteOne (edges : List Edge) (i : Nat) : List Edge :=
  (edges.zipIdx.filter (fun e => e.2 != i)).map Prod.fst

def adjacent (edges : List Edge) (u v : Nat) : Bool :=
  edges.any (fun e =>
    (e.1 == u && e.2 == v) || (e.1 == v && e.2 == u))

/-- One closure step on undirected neighbors. -/
def expand (edges : List Edge) (seen : List Nat) : List Nat :=
  (List.range 6).filter (fun v =>
    seen.contains v || seen.any (fun u => adjacent edges u v))

/-- Any simple 0-to-5 path has at most 5 edges on six vertices. -/
def reachable (edges : List Edge) : Bool :=
  ((List.range 5).foldl (fun seen _ => expand edges seen) [0]).contains 5

/-- The declared 28 unordered pairs of original edge *indices*. -/
def deletionPairs : List (Nat × Nat) :=
  (List.range 8).flatMap (fun i =>
    ((List.range 8).filter (fun j => i < j)).map (fun j => (i,j)))

def survivingDoubleDeletions (edges : List Edge) : Nat :=
  (deletionPairs.filter (fun ij => reachable (deleteTwo edges ij.1 ij.2))).length

def allOneEdgeDeletionsSurvive (edges : List Edge) : Bool :=
  (List.range 8).all (fun i => reachable (deleteOne edges i))

theorem exactly_eight_edges_each :
    graphA.length = 8 ∧ graphB.length = 8 := by
  decide

theorem twenty_eight_two_edge_subsets :
    deletionPairs.length = 28 := by
  decide

theorem identical_labeled_degree_profiles :
    degreeProfile graphA = [2,5,3,2,2,2] ∧
    degreeProfile graphB = [2,5,3,2,2,2] := by
  decide

theorem both_survive_every_one_edge_removal :
    allOneEdgeDeletionsSurvive graphA = true ∧
    allOneEdgeDeletionsSurvive graphB = true := by
  decide

/-- Finite Boolean reachability after all 28 choices, not a reliability
    theorem for arbitrary graphs. -/
theorem graphA_survives_twenty_five_of_twenty_eight :
    survivingDoubleDeletions graphA = 25 := by
  decide

theorem graphB_survives_twenty_six_of_twenty_eight :
    survivingDoubleDeletions graphB = 26 := by
  decide

theorem equal_degree_but_distinct_two_edge_reliability :
    degreeProfile graphA = degreeProfile graphB ∧
    survivingDoubleDeletions graphA ≠ survivingDoubleDeletions graphB := by
  constructor
  · exact identical_labeled_degree_profiles.1.trans
      identical_labeled_degree_profiles.2.symm
  · rw [graphA_survives_twenty_five_of_twenty_eight,
        graphB_survives_twenty_six_of_twenty_eight]
    decide

/-- The same one-time failure marginal can have different sustained
    three-observation outcomes under frozen versus independently renewed
    failure patterns. This is ordinary rational probability arithmetic. -/
theorem graphA_fixed_vs_renewed_noise :
    (25 : ℚ) / 28 > ((25 : ℚ) / 28) ^ 3 := by
  norm_num

theorem graphB_fixed_vs_renewed_noise :
    (26 : ℚ) / 28 > ((26 : ℚ) / 28) ^ 3 := by
  norm_num

theorem source_probabilities_are_distinct :
    (25 : ℚ) / 28 < (26 : ℚ) / 28 := by
  norm_num

end RelationalPersistence.StructureNoiseWitness
