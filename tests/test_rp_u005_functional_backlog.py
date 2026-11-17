"""RP-U005 synthetic adversarial checks before the first frozen source computation."""
from __future__ import annotations

from copy import deepcopy

import pytest

from experiments import rp_u005_functional_backlog as f


def test_original_source_and_edge_failure_repair_schedule_are_exact():
    assert f.EDGES == frozenset({(0, 1), (1, 3), (0, 2), (2, 3)})
    assert f.FAILED_EDGE == (1, 3)
    assert f.RESTORE_TICK == 3
    assert f.TICKS == tuple(range(12))
    assert f.WORLDS == tuple(f.World(pre, post)
                            for pre in (0, 2) for post in (0, 1, 2, 3))
    for tick in f.TICKS:
        state = f.structural_snapshot(tick)
        assert state["F1"] == 1
        assert state["F2"] == (0 if tick < 3 else 1)
        assert state["capacity"] == (1 if tick < 3 else 2)


def test_two_independent_route_oracles_for_all_fixed_graph_states():
    for tick in f.TICKS:
        edges = f.source_graph(tick)
        paths = f.paths_dfs(edges)
        assert f.reachable_bfs(edges) == bool(paths)
        assert f.two_routes_from_paths(paths) == f.two_routes_from_cut_test(edges)


def test_independent_queue_oracles_agree_on_complete_eight_world_grid():
    for world in f.WORLDS:
        first = f.scalar_recurrence(world)
        second = f.fifo_event_oracle(world)
        assert first == second
        f.verify_history(world, first)
        assert len(first) == 12
        assert sum(x["arrived"] for x in first) == (
            sum(x["delivered"] for x in first) + first[-1]["backlog"]
        )


def test_primary_counterexample_has_identical_public_graph_and_post_demand():
    healthy = f.World(0, 1)
    stressed = f.World(2, 1)
    a = f.scalar_recurrence(healthy)
    b = f.scalar_recurrence(stressed)
    assert [(x["F1"], x["F2"], x["capacity"]) for x in a] == [
        (x["F1"], x["F2"], x["capacity"]) for x in b
    ]
    assert [x["arrived"] for x in a[3:]] == [x["arrived"] for x in b[3:]]
    assert f.first_two_empty_end_ticks(a) == 4
    assert f.first_two_empty_end_ticks(b) == 6
    assert b[2]["backlog"] == 3
    assert a[2]["backlog"] == 0


def test_balanced_capacity_cannot_drain_a_preexisting_backlog():
    balanced = f.scalar_recurrence(f.World(2, 2))
    assert all(x["F2"] == 1 for x in balanced[3:])
    assert all(x["backlog"] == 3 for x in balanced[3:])
    assert f.first_two_empty_end_ticks(balanced) is None
    no_load_before = f.scalar_recurrence(f.World(0, 2))
    assert all(x["backlog"] == 0 for x in no_load_before)
    assert f.first_two_empty_end_ticks(no_load_before) == 4


def test_expected_negative_controls_not_selected_after_results():
    recovering = f.scalar_recurrence(f.World(2, 0))
    assert recovering[3]["backlog"] == 1
    assert recovering[4]["backlog"] == 0
    assert f.first_two_empty_end_ticks(recovering) == 5
    newly_overloaded = f.scalar_recurrence(f.World(0, 3))
    assert newly_overloaded[3]["backlog"] == 1
    assert newly_overloaded[-1]["backlog"] > 0
    with_history = f.scalar_recurrence(f.World(2, 3))
    assert with_history[-1]["backlog"] > with_history[2]["backlog"]


def test_missing_or_reordered_time_or_modified_arrivals_fail_closed():
    world = f.World(2, 1)
    original = f.scalar_recurrence(world)
    missing = deepcopy(original[:-1])
    with pytest.raises(f.ScopeViolation, match="INCOMPLETE"):
        f.verify_history(world, missing)
    wrong_arrival = deepcopy(original)
    wrong_arrival[4]["arrived"] = 2
    with pytest.raises(f.ScopeViolation, match="SOURCE_INPUT"):
        f.verify_history(world, wrong_arrival)
    reordered = deepcopy(original)
    reordered[5], reordered[6] = reordered[6], reordered[5]
    with pytest.raises(f.ScopeViolation, match="TIME_WAS_CHANGED"):
        f.verify_history(world, reordered)


def test_invalid_backlog_and_false_completion_fail_conservation_audit():
    world = f.World(2, 1)
    original = f.scalar_recurrence(world)
    for field, value, error in (
        ("backlog", -1, "NEGATIVE"),
        ("delivered", 3, "NEGATIVE"),
        ("backlog", 0, "CONSERVATION"),
    ):
        changed = deepcopy(original)
        changed[1][field] = value
        with pytest.raises(f.ScopeViolation, match=error):
            f.verify_history(world, changed)


def test_unregistered_world_edge_and_graph_tamper_rejected():
    with pytest.raises(f.ScopeViolation, match="UNREGISTERED_WORLD"):
        f.scalar_recurrence(f.World(1, 1))
    with pytest.raises(f.ScopeViolation, match="UNREGISTERED_TICK"):
        f.source_graph(100)
    with pytest.raises(f.ScopeViolation, match="UNREGISTERED_EDGE"):
        f.paths_dfs(frozenset({(0, 3)}))


def test_recovery_metric_rejects_short_or_reordered_monitor_trace():
    trace = f.scalar_recurrence(f.World(0, 1))
    with pytest.raises(f.ScopeViolation, match="FULL_MONITOR"):
        f.first_two_empty_end_ticks(trace[:-1])
    altered = deepcopy(trace)
    altered[0]["t"] = 1
    with pytest.raises(f.ScopeViolation, match="GRID"):
        f.first_two_empty_end_ticks(altered)


def test_structural_oracle_mismatch_must_abort_not_be_interpreted(monkeypatch):
    monkeypatch.setattr(f, "two_routes_from_cut_test", lambda edges: False)
    with pytest.raises(f.ScopeViolation, match="INDEPENDENT_F2"):
        f.structural_snapshot(3)
