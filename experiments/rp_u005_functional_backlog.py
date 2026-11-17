"""RP-U005-P01: finite structural restoration versus queue-service recovery.

The registered experiment is a deterministic four-vertex toy service network.
All inputs were fixed before this module was written. A graph's structural
F1/F2 metrics are checked independently from the synthetic queue backlog and
delivered work. Nothing here is a measured brain, ecological, medical or
Internet service, and no general physical law is claimed.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

PROTOCOL = "RP-U005-P01"
PREREG = "ef5c45a815bbd1fd496b481cc0cfee5c1f368402"
EDGES = frozenset({(0, 1), (1, 3), (0, 2), (2, 3)})
FAILED_EDGE = (1, 3)
SOURCE = 0
TARGET = 3
INTERNAL = (1, 2)
TICKS = tuple(range(12))
RESTORE_TICK = 3
PRE_LOADS = (0, 2)
POST_LOADS = (0, 1, 2, 3)
FIRST_RESULT = Path("docs/results/RP-U005-P01-first-run/audit.json")


class ScopeViolation(ValueError):
    """The frozen experiment or its independent verification has been violated."""


@dataclass(frozen=True, order=True)
class World:
    pre: int
    post: int


WORLDS = tuple(World(pre, post) for pre in PRE_LOADS for post in POST_LOADS)


def source_graph(tick: int) -> frozenset[tuple[int, int]]:
    if tick not in TICKS:
        raise ScopeViolation("UNREGISTERED_TICK")
    return EDGES - {FAILED_EDGE} if tick < RESTORE_TICK else EDGES


def neighbors(edges: frozenset[tuple[int, int]]) -> dict[int, set[int]]:
    """BFS oracle adjacency; the path enumerator builds its own adjacency."""
    adjacency = {n: set() for n in range(4)}
    if not edges <= EDGES:
        raise ScopeViolation("UNREGISTERED_EDGE_OR_VERTEX")
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    return adjacency


def reachable_bfs(edges: frozenset[tuple[int, int]],
                  forbidden: frozenset[int] = frozenset()) -> bool:
    if SOURCE in forbidden or TARGET in forbidden:
        return False
    adjacency = neighbors(edges)
    reached = {SOURCE}
    pending = deque([SOURCE])
    while pending:
        vertex = pending.popleft()
        if vertex == TARGET:
            return True
        for neighbor in sorted(adjacency[vertex]):
            if neighbor not in forbidden and neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    return False


def paths_dfs(edges: frozenset[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    """Independently enumerate all simple 0-to-3 paths without BFS calls."""
    if not edges <= EDGES:
        raise ScopeViolation("UNREGISTERED_EDGE_OR_VERTEX")
    found = []
    def visit(path: tuple[int, ...]) -> None:
        last = path[-1]
        if last == TARGET:
            found.append(path)
            return
        for a, b in sorted(edges):
            neighbor = b if a == last else a if b == last else None
            if neighbor is not None and neighbor not in path:
                visit(path + (neighbor,))
    visit((SOURCE,))
    return tuple(sorted(found))


def two_routes_from_paths(paths: tuple[tuple[int, ...], ...]) -> bool:
    return any(
        frozenset(path[1:-1]).isdisjoint(other[1:-1])
        for path, other in combinations(paths, 2)
    )


def two_routes_from_cut_test(edges: frozenset[tuple[int, int]]) -> bool:
    """Independent cut oracle for the exact four-vertex model."""
    return all(reachable_bfs(edges, frozenset({v})) for v in INTERNAL)


def structural_snapshot(tick: int) -> dict:
    edges = source_graph(tick)
    actual_paths = paths_dfs(edges)
    reachable = reachable_bfs(edges)
    if reachable != bool(actual_paths):
        raise ScopeViolation("INDEPENDENT_F1_ORACLES_DISAGREE")
    f2_paths = two_routes_from_paths(actual_paths)
    f2_cut = two_routes_from_cut_test(edges)
    if f2_paths != f2_cut or (f2_paths and not reachable):
        raise ScopeViolation("INDEPENDENT_F2_ORACLES_DISAGREE")
    if not reachable:
        raise ScopeViolation("REGISTERED_GRAPH_LOST_ALL_PATHS")
    expected_f2 = tick >= RESTORE_TICK
    if f2_paths != expected_f2:
        raise ScopeViolation("STRUCTURAL_REPAIR_TIMELINE_CHANGED")
    return {
        "t": tick,
        "present_edges": [list(e) for e in sorted(edges)],
        "F1": int(reachable),
        "F2": int(f2_paths),
        "capacity": 1 + int(f2_paths),
    }


def require_world(world: World) -> None:
    if world not in WORLDS:
        raise ScopeViolation("UNREGISTERED_WORLD")


def arrivals(world: World, tick: int) -> int:
    require_world(world)
    if tick not in TICKS:
        raise ScopeViolation("UNREGISTERED_TICK")
    return world.pre if tick < RESTORE_TICK else world.post


def scalar_recurrence(world: World) -> list[dict]:
    """Integer capacity recurrence; no individual job objects are used."""
    require_world(world)
    backlog = 0
    output = []
    for t in TICKS:
        graph = structural_snapshot(t)
        demand = arrivals(world, t)
        available = backlog + demand
        completed = min(available, graph["capacity"])
        backlog = available - completed
        output.append({
            "t": t,
            "arrived": demand,
            "delivered": completed,
            "backlog": backlog,
            "capacity": graph["capacity"],
            "F1": graph["F1"],
            "F2": graph["F2"],
        })
    return output


def fifo_event_oracle(world: World) -> list[dict]:
    """Separate unit-job FIFO engine; never uses scalar_recurrence's update."""
    require_world(world)
    jobs: deque[tuple[int, int]] = deque()
    completed_ids = set()
    output = []
    for t in TICKS:
        # The graph cut test is independent of the path-pair oracle used by
        # structural_snapshot; the two implementations must still agree.
        active = source_graph(t)
        capacity = 1 + int(two_routes_from_cut_test(active))
        for index in range(arrivals(world, t)):
            key = (t, index)
            if key in completed_ids or key in jobs:
                raise ScopeViolation("REPLAYED_JOB_IDENTITY")
            jobs.append(key)
        finished = 0
        for _ in range(capacity):
            if not jobs:
                break
            key = jobs.popleft()
            if key in completed_ids:
                raise ScopeViolation("DUPLICATE_JOB_COMPLETION")
            completed_ids.add(key)
            finished += 1
        output.append({
            "t": t,
            "arrived": arrivals(world, t),
            "delivered": finished,
            "backlog": len(jobs),
            "capacity": capacity,
            "F1": int(bool(paths_dfs(active))),
            "F2": int(two_routes_from_cut_test(active)),
        })
    return output


def verify_history(world: World, trace: list[dict]) -> None:
    """Prefix conservation and frozen intervention are independently checked."""
    require_world(world)
    if len(trace) != len(TICKS):
        raise ScopeViolation("INCOMPLETE_TWELVE_TICK_HISTORY")
    total_input = 0
    total_delivered = 0
    for t, row in zip(TICKS, trace, strict=True):
        if row["t"] != t or row["arrived"] != arrivals(world, t):
            raise ScopeViolation("SOURCE_INPUT_OR_TIME_WAS_CHANGED")
        expected = structural_snapshot(t)
        if any(row[field] != expected[field] for field in ("F1", "F2", "capacity")):
            raise ScopeViolation("STRUCTURAL_STATE_OR_CAPACITY_INCONSISTENT")
        if (type(row["backlog"]) is not int or row["backlog"] < 0
                or type(row["delivered"]) is not int
                or not 0 <= row["delivered"] <= expected["capacity"]):
            raise ScopeViolation("NEGATIVE_OR_INVALID_COMPLETION_COUNT")
        total_input += row["arrived"]
        total_delivered += row["delivered"]
        if total_input != total_delivered + row["backlog"]:
            raise ScopeViolation("JOB_CONSERVATION_FAILED")


def first_two_empty_end_ticks(trace: list[dict]) -> int | None:
    if len(trace) != len(TICKS):
        raise ScopeViolation("RECOVERY_REQUIRES_FULL_MONITOR_TRACE")
    if [row.get("t") for row in trace] != list(TICKS):
        raise ScopeViolation("MONITOR_TIME_GRID_INVALID")
    for t in range(RESTORE_TICK + 1, len(TICKS)):
        if trace[t]["backlog"] == 0 and trace[t - 1]["backlog"] == 0:
            return t
    return None


def evaluate_world(world: World) -> dict:
    by_equation = scalar_recurrence(world)
    by_jobs = fifo_event_oracle(world)
    verify_history(world, by_equation)
    verify_history(world, by_jobs)
    if by_equation != by_jobs:
        raise ScopeViolation("INDEPENDENT_SERVICE_ORACLES_DISAGREE")
    return {
        "pre_arrivals_each_failed_tick": world.pre,
        "post_arrivals_each_restored_tick": world.post,
        "graph_repaired_at_tick": RESTORE_TICK,
        "structural_F2_after_repair": [int(x["F2"]) for x in by_equation[RESTORE_TICK:]],
        "queue_at_beginning_of_repair_tick": by_equation[RESTORE_TICK-1]["backlog"],
        "first_two_sample_zero_backlog_completion_tick": first_two_empty_end_ticks(by_equation),
        "cumulative_arrivals": sum(x["arrived"] for x in by_equation),
        "cumulative_delivered": sum(x["delivered"] for x in by_equation),
        "end_backlog": by_equation[-1]["backlog"],
        "twelve_complete_observations": by_equation,
        "independent_FIFO_and_recurrence_oracles_agree": True,
    }


def audit() -> dict:
    if len(WORLDS) != 8 or len(set(WORLDS)) != 8:
        raise ScopeViolation("FROZEN_EIGHT_WORLD_GRID_CHANGED")
    results = [evaluate_world(world) for world in WORLDS]
    by_case = {(r["pre_arrivals_each_failed_tick"],
                r["post_arrivals_each_restored_tick"]): r for r in results}
    healthy = by_case[(0, 1)]
    stressed = by_case[(2, 1)]
    good_tick = healthy["first_two_sample_zero_backlog_completion_tick"]
    bad_tick = stressed["first_two_sample_zero_backlog_completion_tick"]
    h1 = (isinstance(good_tick, int) and isinstance(bad_tick, int)
          and bad_tick - good_tick >= 2
          and healthy["structural_F2_after_repair"]
              == stressed["structural_F2_after_repair"])
    stressed_balanced = by_case[(2, 2)]
    h2 = (stressed_balanced["queue_at_beginning_of_repair_tick"] > 0
          and stressed_balanced["first_two_sample_zero_backlog_completion_tick"] is None
          and all(stressed_balanced["structural_F2_after_repair"]))
    controls = {
        "clean_balanced_service_no_backlog": (
            by_case[(0, 2)]["end_backlog"] == 0
            and by_case[(0, 2)]["first_two_sample_zero_backlog_completion_tick"] is not None
        ),
        "stressed_zero_demand_drains": (
            by_case[(2, 0)]["end_backlog"] == 0
            and by_case[(2, 0)]["first_two_sample_zero_backlog_completion_tick"] is not None
        ),
        "overcapacity_arrivals_generate_backlog": (
            by_case[(0, 3)]["end_backlog"] > 0
            and by_case[(0, 3)]["first_two_sample_zero_backlog_completion_tick"] is None
        ),
        "stressed_overcapacity_arrivals_increase_backlog": (
            by_case[(2, 3)]["end_backlog"]
            > by_case[(2, 3)]["queue_at_beginning_of_repair_tick"]
        ),
    }
    if not all(controls.values()) or not h2:
        raise ScopeViolation("REGISTERED_NEGATIVE_CONTROLS_OR_SECONDARY_FAIL")
    result = {
        "protocol": PROTOCOL,
        "protocol_only_commit": PREREG,
        "synthetic_data_only": True,
        "observed_human_or_field_records": 0,
        "registered_cases": 8,
        "ticks_per_case": len(TICKS),
        "first_full_repair_tick": RESTORE_TICK,
        "independent_graph_and_service_oracles_agree": True,
        "registered_H1_supported": h1,
        "registered_H1_recovery_tick_clean": good_tick,
        "registered_H1_recovery_tick_stressed": bad_tick,
        "registered_H1_difference": (
            bad_tick - good_tick if h1 else None
        ),
        "registered_H2_balanced_backlog_persists": h2,
        "negative_controls": controls,
        "status": (
            "FINITE_TOPOLOGY_INSUFFICIENT_FOR_RECOVERY_TIME" if h1 else
            "FINITE_REGISTERED_SEPARATION_NOT_OBSERVED"
        ),
        "worlds": results,
        "new_physical_or_biological_law_proven": False,
    }
    return result


def main() -> None:
    if FIRST_RESULT.exists():
        raise SystemExit("FIRST_ARCHIVE_EXISTS_DO_NOT_OVERWRITE")
    report = audit()
    FIRST_RESULT.parent.mkdir(parents=True, exist_ok=True)
    FIRST_RESULT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
