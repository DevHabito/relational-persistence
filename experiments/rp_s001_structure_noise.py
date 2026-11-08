"""RP-S001-P01: exact finite graph reliability under fixed-size edge failures.

Protocol-only commit 5f61ae5a3dc239bb0017fa09ced81a52d49df493
preceded source implementation and any primary outcome calculation.
These are classical graph/reliability phenomena, not a novel physics theorem.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import json

STUDY = "RP-S001-P01"
PROTOCOL_COMMIT = "5f61ae5a3dc239bb0017fa09ced81a52d49df493"
VERTICES = tuple(range(6))
SOURCE, TARGET = 0, 5
EDGES = tuple((x, y) for x in VERTICES for y in VERTICES if x < y and (x, y) != (0, 5))
ORIGINAL_EDGE_COUNT = 8
FAIL_COUNT = 2
FAIL_SUBSETS = tuple(combinations(range(ORIGINAL_EDGE_COUNT), FAIL_COUNT))
TIMES = 3
TOTAL_SOURCE_GRAPHS = 3003


class StudyError(ValueError):
    pass


def graph_valid_basic(graph: tuple[tuple[int, int], ...]) -> bool:
    if not isinstance(graph, tuple) or len(graph) != ORIGINAL_EDGE_COUNT:
        return False
    if tuple(sorted(set(graph))) != graph or any(edge not in EDGES for edge in graph):
        return False
    return True


def degree_vector(graph: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    if not graph_valid_basic(graph):
        raise StudyError("INVALID_GRAPH_FOR_DEGREE")
    counts = [0] * len(VERTICES)
    for x, y in graph:
        counts[x] += 1
        counts[y] += 1
    return tuple(counts)


def bfs_reachable(graph: tuple[tuple[int, int], ...], start: int = SOURCE,
                  dest: int = TARGET) -> bool:
    queue = deque([start])
    seen = {start}
    while queue:
        current = queue.popleft()
        if current == dest:
            return True
        for x, y in graph:
            nxt = y if x == current else x if y == current else None
            if nxt is not None and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def dfs_path_reachable(graph: tuple[tuple[int, int], ...], start: int = SOURCE,
                       dest: int = TARGET) -> bool:
    """Separate simple-path oracle, not BFS or the same adjacency helper."""
    def visit(v: int, used: frozenset[int]) -> bool:
        if v == dest:
            return True
        for candidate in VERTICES:
            edge = tuple(sorted((v, candidate)))
            if candidate != v and candidate not in used and edge in graph:
                if visit(candidate, used | {candidate}):
                    return True
        return False
    return visit(start, frozenset({start}))


def connected_whole_graph(graph: tuple[tuple[int, int], ...]) -> bool:
    return all(bfs_reachable(graph, SOURCE, v) for v in VERTICES)


def exact_st_edge_cut(graph: tuple[tuple[int, int], ...]) -> int:
    """Enumerate all 16 source-side vertex subsets; classical min-cut."""
    if not graph_valid_basic(graph):
        raise StudyError("INVALID_GRAPH_FOR_EDGE_CUT")
    other = (1, 2, 3, 4)
    cuts = []
    for mask in range(1 << len(other)):
        left = {SOURCE} | {node for i, node in enumerate(other) if mask & (1 << i)}
        crossing = sum((x in left) != (y in left) for x, y in graph)
        cuts.append(crossing)
    return min(cuts)


def remove_by_indices(graph: tuple[tuple[int, int], ...],
                      removed: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if any(i < 0 or i >= len(graph) for i in removed) or len(set(removed)) != len(removed):
        raise StudyError("INVALID_REMOVAL_INDICES")
    return tuple(edge for index, edge in enumerate(graph) if index not in removed)


def certified_survival_count(graph: tuple[tuple[int, int], ...]) -> tuple[int, tuple[bool, ...]]:
    if not graph_valid_basic(graph):
        raise StudyError("INVALID_GRAPH_IN_SURVIVAL")
    outcomes = []
    for indices in FAIL_SUBSETS:
        remainder = remove_by_indices(graph, indices)
        bfs = bfs_reachable(remainder)
        dfs = dfs_path_reachable(remainder)
        if bfs != dfs:
            raise StudyError("BFS_DFS_ORACLES_DISAGREE")
        outcomes.append(bfs)
    if len(outcomes) != 28:
        raise StudyError("WRONG_FAILURE_UNIVERSE")
    return sum(outcomes), tuple(outcomes)


def deletion_mincut_check(graph: tuple[tuple[int, int], ...]) -> int:
    if not bfs_reachable(graph):
        return 0
    if any(not bfs_reachable(remove_by_indices(graph, (i,))) for i in range(8)):
        return 1
    if any(not bfs_reachable(remove_by_indices(graph, sub)) for sub in FAIL_SUBSETS):
        return 2
    return 3  # lower bound >=3, sufficient for two-edge terminal-degree graphs


def admissible_source_graphs() -> tuple[tuple[tuple[int, int], ...], ...]:
    candidates = 0
    answer = []
    for graph in combinations(EDGES, ORIGINAL_EDGE_COUNT):
        candidates += 1
        degree = degree_vector(graph)
        if degree[SOURCE] != 2 or degree[TARGET] != 2:
            continue
        if not connected_whole_graph(graph):
            continue
        by_cut = exact_st_edge_cut(graph)
        by_deletions = deletion_mincut_check(graph)
        if by_cut != by_deletions:
            raise StudyError("MINCUT_INDEPENDENT_CHECK_DISAGREES")
        if by_cut != 2:
            continue
        if any(not bfs_reachable(remove_by_indices(graph, (i,))) for i in range(8)):
            raise StudyError("SOURCE_MINCUT_TWO_HAS_BRIDGE_FOR_TERMINALS")
        answer.append(graph)
    if candidates != TOTAL_SOURCE_GRAPHS:
        raise StudyError("COMPLETE_ENUMERATION_SIZE_MISMATCH")
    if len(answer) != len(set(answer)):
        raise StudyError("DUPLICATE_SOURCE_GRAPH")
    return tuple(answer)


def rational_record(p: Fraction) -> dict[str, int]:
    return {"numerator": p.numerator, "denominator": p.denominator}


def temporal_controls(outcomes: tuple[bool, ...]) -> dict:
    if len(outcomes) != len(FAIL_SUBSETS):
        raise StudyError("TEMPORAL_INPUT_NOT_28_PATTERNS")
    successes = sum(outcomes)
    if not 0 <= successes <= 28:
        raise StudyError("SURVIVAL_COUNT_OUT_OF_BOUNDS")
    frozen = Fraction(successes, 28)
    renewed = frozen**TIMES
    # Independently enumerate exact 28^3 schedules (not a sample).
    independent_success = sum(all(outcomes[index] for index in schedule)
                              for schedule in product(range(28), repeat=TIMES))
    if independent_success != successes**TIMES:
        raise StudyError("DIRECT_SCHEDULE_ORACLE_DISAGREES")
    result = {
        "one_time_survival": rational_record(frozen),
        "frozen_two_edge_failure_set_sustained_3": rational_record(frozen),
        "independent_new_failure_set_each_tick_sustained_3": rational_record(renewed),
        "three_step_independent_successful_schedules": independent_success,
        "three_step_total_schedules": 28**TIMES,
        "strict_temporal_gap": frozen > renewed,
        "same_uniform_per_tick_failure_distribution": True,
        "emergent_physical_time_tested": False,
    }
    if result["strict_temporal_gap"] != (0 < successes < 28):
        raise StudyError("TEMPORAL_GAP_IDENTITY_FAILED")
    return result


def run() -> dict:
    graphs = admissible_source_graphs()
    strata: dict[tuple[int, ...], list] = defaultdict(list)
    all_results = {}
    by_k = Counter()
    for graph in graphs:
        degree = degree_vector(graph)
        if exact_st_edge_cut(graph) != 2:
            raise StudyError("SOURCE_CUT_NOT_TWO")
        k, outcomes = certified_survival_count(graph)
        by_k[k] += 1
        strata[degree].append(graph)
        all_results[graph] = (k, outcomes)
    first = None
    pair_candidates = []
    dispersion = {}
    for degree, group in sorted(strata.items()):
        group.sort()
        distinct = tuple(sorted({all_results[graph][0] for graph in group}))
        dispersion[degree] = (len(group), min(distinct), max(distinct))
        if len(distinct) <= 1:
            continue
        # Lex earliest pair within group with unequal exact numerators:
        # never optimize for a favorable or largest observed difference.
        for a, b in combinations(group, 2):
            if all_results[a][0] != all_results[b][0]:
                pair_candidates.append((a, b, degree))
                break
    if pair_candidates:
        a, b, degree = min(pair_candidates, key=lambda entry: (entry[0], entry[1]))
        first = {
            "graph_A_edges": [list(e) for e in a],
            "graph_B_edges": [list(e) for e in b],
            "full_labeled_degree_vector": list(degree),
            "shared_terminal_minimum_edge_cut": 2,
            "graph_A_surviving_two_edge_subsets": all_results[a][0],
            "graph_B_surviving_two_edge_subsets": all_results[b][0],
            "graph_A_survival_fraction": rational_record(Fraction(all_results[a][0], 28)),
            "graph_B_survival_fraction": rational_record(Fraction(all_results[b][0], 28)),
            "graph_A_three_step_disturbance_controls": temporal_controls(all_results[a][1]),
            "graph_B_three_step_disturbance_controls": temporal_controls(all_results[b][1]),
        }
    if not graphs or sum(len(g) for g in strata.values()) != len(graphs):
        raise StudyError("SOURCE_PARTITION_CONSERVATION_FAILED")
    if sum(by_k.values()) != len(graphs):
        raise StudyError("RELIABILITY_HISTOGRAM_CONSERVATION_FAILED")
    if sum(len(group) >= 2 for group in strata.values()) > len(strata):
        raise StudyError("DEGREE_GROUP_COUNT_IMPOSSIBLE")
    nonsingular = sum(1 for k in all_results if 0 < all_results[k][0] < 28)
    return {
        "study": STUDY,
        "protocol_commit": PROTOCOL_COMMIT,
        "source_is_synthetic": True,
        "source_vertices": 6, "source_edges": 8,
        "forbidden_direct_terminal_edge": [0, 5],
        "terminal_degrees": [2, 2],
        "source_terminal_mincut": 2,
        "exact_failure_subsets_per_graph": 28,
        "full_family_unfiltered_graphs": TOTAL_SOURCE_GRAPHS,
        "admissible_source_graphs": len(graphs),
        "full_labeled_degree_classes": len(strata),
        "degree_classes_with_at_least_two_members": sum(len(g) >= 2 for g in strata.values()),
        "degree_classes_with_nonconstant_survival": sum(lo != hi for _, lo, hi in dispersion.values()),
        "maximum_within_degree_class_surviving_numerator_gap": max((hi - lo for _,lo,hi in dispersion.values()), default=0),
        "survival_numerator_histogram": {str(k): by_k[k] for k in sorted(by_k)},
        "graphs_with_nondegenerate_one_time_survival": nonsingular,
        "primary_decision": ("SUMMARY_SUFFICIENCY_COUNTEREXAMPLE" if first else
                             "NO_FINITE_COUNTEREXAMPLE"),
        "temporal_decision": ("TEMPORAL_CORRELATION_CONTRAST" if nonsingular else
                              "NO_TEMPORAL_CONTRAST"),
        "first_lexicographic_primary_witness": first,
        "independent_BFS_and_DFS_oracles_checked": True,
        "independent_vertex_cut_and_deletion_cut_oracles_checked": True,
        "any_real_source_data_used": False,
        "new_graph_theorem_or_physical_law_claimed": False,
        "originality_verified_against_all_literature": False,
    }


if __name__ == "__main__":
    path = Path("rp-s001-p01-first-run/audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    report = run()
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
