"""RP-U001-A01 — finite functional continuity after non-adaptive component loss.

Pre-registered on main commit 81ce6d1 BEFORE any code or numerical execution.
Two specifically chosen graph examples, NOT measured ecological networks
and NOT a universal theory. Exhaustive 16 fixed vertex-removal subsets
per graph; independent BFS and simple-path oracles.

The source and destination terminals always survive, no rewiring or regrowth.
"""

from __future__ import annotations

from collections import deque
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import argparse
import json
import os

PREREG = "81ce6d186c3ba1a86c25297a30fb0f6a27cb7d4e"
PROTOCOL = "RP-U001-A01"
VERTICES = frozenset(range(6))
SOURCE = 0
TARGET = 5
REMOVABLE = (1, 2, 3, 4)

GRAPH_EDGES = {
    "A": ((0, 1), (1, 2), (2, 5), (0, 3),
          (3, 4), (4, 5), (1, 3)),
    "B": ((0, 1), (0, 3), (1, 2), (3, 2),
          (2, 5), (2, 4), (4, 5)),
}
# This exact permutation is frozen and fixes source 0 / target 5.
RELABEL = {0: 0, 1: 3, 2: 1, 3: 4, 4: 2, 5: 5}
REGISTERED_COUNTS = {
    "A": (1, 4, 2, 0, 0),
    "B": (1, 3, 2, 0, 0),
}
REGISTERED_TWO_DISJOINT_SINGLE_LOSS = 0


def canonical_edges(edges):
    result = frozenset(tuple(sorted((u, v))) for u, v in edges)
    if any(u == v or u not in VERTICES or v not in VERTICES
           for u, v in result):
        raise ValueError("Original source graph is not a simple six-vertex graph")
    if len(result) != len(tuple(edges)):
        raise ValueError("Duplicate original source edge")
    return result


def check_baseline(edges) -> None:
    if len(edges) != 7:
        raise ValueError("Incorrect registered graph edge count")
    if not all(sum(v in e for e in edges) == 2 for v in (SOURCE, TARGET)):
        raise ValueError("Source/target terminal degree must equal two")


def neighbors_from_edges(edges, removed):
    allowed = VERTICES.difference(removed)
    links = {v: set() for v in allowed}
    for u, v in edges:
        if u in allowed and v in allowed:
            links[u].add(v)
            links[v].add(u)
    return links


def reachable_bfs(edges, removed) -> bool:
    """Oracle A: breadth-first traversal on independently built adjacency."""
    if SOURCE in removed or TARGET in removed:
        raise ValueError("Registered experiment never removes terminals")
    links = neighbors_from_edges(edges, removed)
    visited = {SOURCE}
    frontier = deque([SOURCE])
    while frontier:
        current = frontier.popleft()
        if current == TARGET:
            return True
        for neighbor in sorted(links[current]):
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)
    return False


def enumerate_simple_paths(edges, removed) -> tuple[tuple[int, ...], ...]:
    """Oracle B: depth-first simple-path enumeration, not BFS reuse."""
    if SOURCE in removed or TARGET in removed:
        raise ValueError("Registered terminals cannot be deleted")
    # Deliberately do not call neighbors_from_edges/reachable_bfs.
    acceptable = VERTICES - set(removed)
    paths = []
    def visit(history):
        v = history[-1]
        if v == TARGET:
            paths.append(tuple(history))
            return
        for next_v in sorted(acceptable):
            if next_v != v and next_v not in history and (
                (v, next_v) in edges or (next_v, v) in edges
            ):
                visit(history + [next_v])
    visit([SOURCE])
    return tuple(paths)


def reachable_paths(edges, removed) -> bool:
    return bool(enumerate_simple_paths(edges, removed))


def two_vertex_disjoint_paths(edges, removed) -> bool:
    paths = enumerate_simple_paths(edges, removed)
    return any(
        set(p[1:-1]).isdisjoint(q[1:-1])
        for i, p in enumerate(paths) for q in paths[i + 1:]
    )


def relabel_edges(edges):
    return canonical_edges((RELABEL[u], RELABEL[v]) for u, v in edges)


def subsets_of_size(k):
    return tuple(combinations(REMOVABLE, k))


def exhaustive_one_graph(edges, relabel=False):
    data = []
    for k in range(5):
        recorded = []
        for removed in subsets_of_size(k):
            transformed = (
                tuple(sorted(RELABEL[v] for v in removed))
                if relabel else removed
            )
            cut = frozenset(transformed)
            bfs = reachable_bfs(edges, cut)
            dfs = reachable_paths(edges, cut)
            if bfs != dfs:
                raise AssertionError("Independent reachability oracles disagree")
            recorded.append({
                "removed": list(removed), # Only artificial node IDs.
                "bfs_reachable": bfs, "dfs_reachable": dfs,
                "two_disjoint_paths": two_vertex_disjoint_paths(edges, cut),
                "surviving_vertex_fraction": str(Fraction(6 - k, 6)),
            })
        passes = sum(item["bfs_reachable"] for item in recorded)
        data.append({
            "k": k, "tested_subsets": len(recorded),
            "function_retained_subsets": passes,
            "function_retention_fraction": str(Fraction(passes, len(recorded))),
            "exact_set_outcomes": recorded,
        })
    return data


def audit():
    report = {
        "protocol": PROTOCOL,
        "preregistration_commit": PREREG,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "original_decision": "REGISTERED_FINITE_CONTRAST_REJECTED",
        "scope": "six-node deterministic in-silico graphs, no recovery or dynamics",
        "measured_ecological_or_technological_data_used": False,
        "cross_domain_physical_law_claimed": False,
        "empirical_bio_function_preservation_verified": False,
        "new_mathematical_principle_claimed": False,
        "graphs": {},
        "negative_control_strict_superiority_all_k": False,
        "registered_two_disjoint_path_control": {},
        "errors": [],
    }
    try:
        if set(RELABEL) != VERTICES or set(RELABEL.values()) != VERTICES:
            raise AssertionError("Registered relabeling is not a permutation")
        for name, raw in GRAPH_EDGES.items():
            edges = canonical_edges(raw)
            check_baseline(edges)
            actual = exhaustive_one_graph(edges)
            translated = exhaustive_one_graph(relabel_edges(edges), relabel=True)
            if any(
                [(entry["k"], entry["function_retained_subsets"])
                 for entry in actual] !=
                [(entry["k"], entry["function_retained_subsets"])
                 for entry in translated],
            ):
                raise AssertionError("Internal-vertex relabeling changed outcomes")
            for left, right in zip(actual, translated):
                if [(x["removed"], x["bfs_reachable"]) for x in
                    left["exact_set_outcomes"]] != [
                    (x["removed"], x["bfs_reachable"])
                    for x in right["exact_set_outcomes"]
                ]:
                    raise AssertionError("Original set-level relabeling differs")
            counts = tuple(row["function_retained_subsets"] for row in actual)
            if counts != REGISTERED_COUNTS[name]:
                raise AssertionError("Frozen per-k functional counts rejected")
            if any(row["tested_subsets"] != (1, 4, 6, 4, 1)[k]
                   for k, row in enumerate(actual)):
                raise AssertionError("Not every registered subset was enumerated")
            baseline = actual[0]["exact_set_outcomes"][0]
            if not baseline["bfs_reachable"]:
                raise AssertionError("Initial function not present")
            disjoint = {
                "initial_has_two_disjoint_routes": baseline["two_disjoint_paths"],
                "single_deletion_cases_retaining_two_disjoint_routes": sum(
                    case["two_disjoint_paths"]
                    for case in actual[1]["exact_set_outcomes"]
                ),
            }
            if disjoint["initial_has_two_disjoint_routes"] != (name == "A"):
                raise AssertionError("Stronger initial function control rejected")
            if disjoint["single_deletion_cases_retaining_two_disjoint_routes"] != 0:
                raise AssertionError("Disjoint-route removal control rejected")
            report["graphs"][name] = {
                "vertices": 6, "edges": 7,
                "source_terminal_degree": 2, "target_terminal_degree": 2,
                "counts_by_removed_vertex_count": list(counts),
                "all_full_sweep_records": actual,
                "relabeling_casewise_verified": True,
            }
            report["registered_two_disjoint_path_control"][name] = disjoint
        if (report["graphs"]["A"]["counts_by_removed_vertex_count"][2] !=
                report["graphs"]["B"]["counts_by_removed_vertex_count"][2]):
            raise AssertionError("Frozen k=2 equality negative control rejected")
        report["negative_control_strict_superiority_all_k"] = True
        report["original_decision"] = "FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED"
    except (AssertionError, ValueError) as exc:
        report["errors"].append(f"{type(exc).__name__}: {str(exc)[:300]}")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Original experiment output exists; refuse replacement")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = audit()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "protocol": PROTOCOL, "verdict": result["original_decision"],
        "A": result["graphs"].get("A", {}).get("counts_by_removed_vertex_count"),
        "B": result["graphs"].get("B", {}).get("counts_by_removed_vertex_count"),
        "errors": result["errors"]
    }, sort_keys=True))
    if result["original_decision"] != "FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
