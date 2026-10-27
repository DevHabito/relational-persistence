"""RP-U002-A01 — exact, finite node-identity turnover and incremental repair.

Preregistered alone on main at fa7f9d0 BEFORE implementation and first
experiment. Uses ONLY the two disclosed RP-U001 toy source graphs;
no biological/medical records, physical law or new graph theory.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
import os
from pathlib import Path

from experiments.rp_u001_functional_continuity import GRAPH_EDGES

PROTOCOL = "RP-U002-A01"
PREREG = "fa7f9d0133370b0e8a769d0b7d95759e402a2dc8"
INTERNAL = (1, 2, 3, 4)
HORIZON = tuple(range(6))
SOURCE = 0
TARGET = 5
REGISTERED_F1 = {
    "repair": {"A": (4, 4, 4, 4, 4, 4),
               "B": (4, 3, 3, 3, 4, 4)},
    "no_repair": {"A": (4, 4, 4, 4, 4, 4),
                  "B": (4, 3, 3, 3, 3, 3)},
}
REGISTERED_F2 = {
    "repair": {"A": (4, 0, 0, 3, 4, 4),
               "B": (0, 0, 0, 0, 0, 0)},
    "no_repair": {"A": (4, 0, 0, 0, 0, 0),
                  "B": (0, 0, 0, 0, 0, 0)},
}
REGISTERED_UPTIME_F1 = {
    "repair": {"A": 20, "B": 17},
    "no_repair": {"A": 20, "B": 15},
}
REGISTERED_UPTIME_F2 = {
    "repair": {"A": 11, "B": 0},
    "no_repair": {"A": 0, "B": 0},
}


@dataclass(frozen=True)
class Snapshot:
    vertices: frozenset[int]
    edges: frozenset[tuple[int, int]]


def edge(u: int, v: int) -> tuple[int, int]:
    if u == v or u < 0 or v < 0:
        raise ValueError("Only distinct nonnegative node IDs")
    return (u, v) if u < v else (v, u)


def originals(graph: str) -> Snapshot:
    if graph not in GRAPH_EDGES:
        raise ValueError("Unregistered source graph")
    original = GRAPH_EDGES[graph]
    baseline = Snapshot(
        frozenset(range(6)), frozenset(edge(u, v) for u, v in original)
    )
    if len(baseline.vertices) != 6 or len(baseline.edges) != 7:
        raise AssertionError("Original RP-U001 source baseline changed")
    if any(sum(vertex in e for e in baseline.edges) != 2
           for vertex in (SOURCE, TARGET)):
        raise AssertionError("Original terminal degree mismatch")
    return baseline


def original_neighbors(base: Snapshot, lost: int) -> tuple[int, ...]:
    if lost not in INTERNAL:
        raise ValueError("Only preregistered internal component failures")
    return tuple(sorted(next(iter(set(e) - {lost}))
                        for e in base.edges if lost in e))


def independent_direct(graph: str, lost: int, t: int,
                       repair: bool) -> Snapshot:
    """Oracle S1: direct algebraic old-edge filter + fixed partial reinsertion."""
    if t not in HORIZON:
        raise ValueError("Unregistered time")
    base = originals(graph)
    if lost not in INTERNAL:
        raise ValueError("Unregistered lost component")
    if t == 0:
        return base
    original_edges = {e for e in base.edges if lost not in e}
    vertices = set(base.vertices) - {lost}
    if repair and t >= 2:
        replacement = 6 + lost
        vertices.add(replacement)
        for neighbor in original_neighbors(base, lost)[:t - 1]:
            original_edges.add(edge(replacement, neighbor))
    return Snapshot(frozenset(vertices), frozenset(original_edges))


def independent_event_replay(graph: str, lost: int,
                             repair: bool) -> dict[int, Snapshot]:
    """Oracle S2: mutating event replay, independent of direct construction."""
    base = originals(graph)
    planned_neighbors = original_neighbors(base, lost)
    vertices = set(base.vertices)
    connections = set(base.edges)
    steps = {0: Snapshot(frozenset(vertices), frozenset(connections))}
    for t in range(1, 6):
        if t == 1:
            vertices.remove(lost)
            connections = {e for e in connections if lost not in e}
        elif repair:
            replacement = 6 + lost
            if t == 2:
                vertices.add(replacement)
            ordinal = t - 2
            if ordinal < len(planned_neighbors):
                connections.add(edge(replacement, planned_neighbors[ordinal]))
        steps[t] = Snapshot(frozenset(vertices), frozenset(connections))
    return steps


def validate_history(graph: str, lost: int, repair: bool,
                     steps: dict[int, Snapshot]) -> None:
    original = originals(graph)
    neighbors = original_neighbors(original, lost)
    if set(steps) != set(HORIZON):
        raise AssertionError("Full time history absent")
    for t in HORIZON:
        a = steps[t]
        b = independent_direct(graph, lost, t, repair)
        if a != b:
            raise AssertionError("Independent direct/state replay disagreement")
        if any(u not in a.vertices or v not in a.vertices for u, v in a.edges):
            raise AssertionError("Dangling edge to absent component")
        if SOURCE not in a.vertices or TARGET not in a.vertices:
            raise AssertionError("Protected terminal absent")
        if t > 0 and lost in a.vertices:
            raise AssertionError("Failed identity returned")
        if t == 0 and a != original:
            raise AssertionError("Source graph changed at t0")
        if t > 0 and (6 + lost in a.vertices) != (repair and t >= 2):
            raise AssertionError("Replacement identity lifecycle inconsistent")
        if t >= 2 and repair:
            if len(a.vertices) != 6:
                raise AssertionError("Replacement did not restore original node COUNT")
            replacement = 6 + lost
            incident = {v for u, v in a.edges if u == replacement}
            incident |= {u for u, v in a.edges if v == replacement}
            if incident != set(neighbors[:t - 1]):
                raise AssertionError("An edge was not the next allowed original relation")
        if t >= 1 and not repair and len(a.vertices) != 5:
            raise AssertionError("No-repair control restored a component")
        if t >= 2:
            delta = a.edges - steps[t - 1].edges
            if len(delta) > 1:
                raise AssertionError("Repair exceeds one new edge per time tick")


def connected_bfs(state: Snapshot, excluded: frozenset[int] = frozenset()) -> bool:
    """Oracle F1-A: mutable queue search over the currently extant graph."""
    allowed = state.vertices - excluded
    if SOURCE not in allowed or TARGET not in allowed:
        return False
    links = {v: set() for v in allowed}
    for u, v in state.edges:
        if u in allowed and v in allowed:
            links[u].add(v)
            links[v].add(u)
    frontier = deque([SOURCE])
    visited = {SOURCE}
    while frontier:
        current = frontier.popleft()
        if current == TARGET:
            return True
        for nxt in sorted(links[current]):
            if nxt not in visited:
                visited.add(nxt)
                frontier.append(nxt)
    return False


def enumerate_paths(state: Snapshot) -> tuple[tuple[int, ...], ...]:
    """Oracle F1-B / F2-A: independently enumerate all simple s-t routes."""
    paths = []
    if SOURCE not in state.vertices or TARGET not in state.vertices:
        return ()
    def walk(route):
        last = route[-1]
        if last == TARGET:
            paths.append(tuple(route))
            return
        for nxt in sorted(state.vertices):
            if nxt not in route and edge(last, nxt) in state.edges:
                walk(route + [nxt])
    walk([SOURCE])
    return tuple(paths)


def two_routes_by_path_pairs(state: Snapshot) -> bool:
    paths = enumerate_paths(state)
    return any(
        not (set(p[1:-1]) & set(q[1:-1]))
        for i, p in enumerate(paths) for q in paths[i + 1:]
    )


def two_routes_by_cut_tests(state: Snapshot) -> bool:
    """Independent F2 oracle via classical single-interior-vertex cuts.

    Works for THESE source families: there is never a direct (0,5) link.
    No claim of an independent proof of Menger's theorem.
    """
    if edge(SOURCE, TARGET) in state.edges:
        raise AssertionError("Registered source family has no direct terminal edge")
    if not connected_bfs(state):
        return False
    return all(connected_bfs(state, frozenset([vertex]))
               for vertex in state.vertices - {SOURCE, TARGET})


def single_history(graph: str, lost: int, repair: bool) -> dict:
    states = independent_event_replay(graph, lost, repair)
    validate_history(graph, lost, repair, states)
    snapshots = []
    for t in HORIZON:
        state = states[t]
        f1a = connected_bfs(state)
        f1b = bool(enumerate_paths(state))
        if f1a != f1b:
            raise AssertionError("Independent F1 reachability oracles disagree")
        f2a = two_routes_by_path_pairs(state)
        f2b = two_routes_by_cut_tests(state)
        if f2a != f2b:
            raise AssertionError("Independent F2 disjoint-route oracles disagree")
        if f2a and not f1a:
            raise AssertionError("Two-route function cannot hold without one path")
        snapshots.append({
            "time": t, "present_component_count": len(state.vertices),
            "present_edge_count": len(state.edges),
            "old_component_lost": lost not in state.vertices if t else False,
            "new_component_present": (6+lost) in state.vertices,
            "F1": f1a, "F2": f2a,
        })
    return {"loss": lost, "snapshots": snapshots}


def audit() -> dict:
    data = {
        "protocol": PROTOCOL,
        "preregistration_commit": PREREG,
        "first_run_id": os.environ.get("GITHUB_RUN_ID"),
        "original_code_commit": os.environ.get("GITHUB_SHA"),
        "verdict": "REGISTERED_TURNOVER_REPAIR_PREDICTION_FAILED",
        "scope": "fixed toy graph replacement and old-neighbor edge reattachment",
        "all_real_domain_observations": 0,
        "new_universal_law_claimed": False,
        "measurements_of_recovery_or_biological_growth": False,
        "forecast_or_physical_scalar_estimated": False,
        "result": {},
        "negative_controls": {},
        "errors": [],
    }
    try:
        for policy, repair in (("repair", True), ("no_repair", False)):
            data["result"][policy] = {}
            for graph in ("A", "B"):
                original = originals(graph)
                if len(original.vertices) != 6 or len(original.edges) != 7:
                    raise AssertionError("Source invariant rejected")
                paths = [single_history(graph, lost, repair) for lost in INTERNAL]
                f1 = tuple(sum(item["snapshots"][t]["F1"] for item in paths)
                           for t in HORIZON)
                f2 = tuple(sum(item["snapshots"][t]["F2"] for item in paths)
                           for t in HORIZON)
                uptime_f1 = sum(f1[1:])
                uptime_f2 = sum(f2[1:])
                if (f1 != REGISTERED_F1[policy][graph] or
                        f2 != REGISTERED_F2[policy][graph] or
                        uptime_f1 != REGISTERED_UPTIME_F1[policy][graph] or
                        uptime_f2 != REGISTERED_UPTIME_F2[policy][graph]):
                    raise AssertionError("Registered time-by-time function predictions failed")
                data["result"][policy][graph] = {
                    "per_time_F1_count_out_of_four": list(f1),
                    "per_time_F2_count_out_of_four": list(f2),
                    "uptime_F1_exact_count_out_of_20": uptime_f1,
                    "uptime_F2_exact_count_out_of_20": uptime_f2,
                    "original_single_failure_scenarios": paths,
                }
        b2 = next(case for case in data["result"]["repair"]["B"][
            "original_single_failure_scenarios"] if case["loss"] == 2)
        snaps = b2["snapshots"]
        if (snaps[0]["present_component_count"] != 6 or
                snaps[2]["present_component_count"] != 6 or
                snaps[4]["present_component_count"] != 6 or
                not snaps[0]["F1"] or snaps[2]["F1"] or not snaps[4]["F1"]):
            raise AssertionError("Equal-component-count counterexample rejected")
        data["negative_controls"] = {
            "B_bottleneck_F1_not_restored_by_new_node_alone": True,
            "no_repair_A_F1_equal_to_repair_A_F1": True,
            "B_F2_never_established_by_repair": True,
            "repair_and_no_repair_B_F1_gain_only_two_out_of_20": True,
            "repair_restores_A_F2_after_delay_not_instantly": True,
        }
        data["verdict"] = "FINITE_TURNOVER_REPAIR_CONTRAST_VERIFIED"
    except (ValueError, AssertionError) as exc:
        data["errors"].append({"reason": f"{type(exc).__name__}: {str(exc)[:300]}"})
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("First original RP-U002 audit exists; refusing overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = audit()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"], "errors": result["errors"],
        "F1_repair": {
            name: row["per_time_F1_count_out_of_four"] for name, row
            in result["result"].get("repair", {}).items()
        },
    }, sort_keys=True))
    if result["verdict"] != "FINITE_TURNOVER_REPAIR_CONTRAST_VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
