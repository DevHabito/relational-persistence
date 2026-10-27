"""RP-U003-A01 synthetic adversarial regression tests (BEFORE first run).

No novel graph law, no field datasets. Full exhaustive benchmark runs
only after exact reviewed Python 3.11/3.12 and Lean 4 CI success.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import pytest

from experiments import rp_u003_equal_budget as u
from experiments.rp_u001_functional_continuity import GRAPH_EDGES


def example(name):
    return tuple(sorted(tuple(sorted(e)) for e in GRAPH_EDGES[name]))


def test_frozen_protocol_source_and_time_policy_criteria():
    assert u.PREREG == "5cb8d3af473aa95848ab22d5ecc591c5a1567a00"
    assert len(u.PAIRS) == 14 and (0, 5) not in u.PAIRS
    assert len(set(u.PAIRS)) == 14
    assert u.TIMES == tuple(range(7))
    assert u.INTERNAL == (1, 2, 3, 4)
    assert u.POLICIES == ("ASC", "DEGREE", "GREEDY1", "LOOKAHEAD2")


def test_two_independent_accepted_labeled_graph_enumerators_agree():
    family = u.all_registered_graphs()
    assert family
    assert len(family) == len(set(family))
    assert tuple(sorted(family)) == family
    for graph in family:
        assert len(graph) == 7
        assert u.source_valid(graph)
        assert u.independent_source_valid(graph)
        degrees = u.original_degrees(graph)
        assert degrees[0] == degrees[5] == 2
        assert all(degrees[v] >= 1 for v in range(6))
        assert (0, 5) not in graph


def test_no_cherry_picked_prior_graph_paired_selection():
    # These old networks need not satisfy the newly frozen exact family;
    # every eligible 7-edge network is included by predicate alone.
    for name in ("A", "B"):
        graph = example(name)
        assert len(graph) == 7
        assert (0, 5) not in graph
        assert u.source_valid(graph)
        assert graph in set(u.all_registered_graphs())


def test_source_enumeration_disagreement_is_fatal(monkeypatch):
    monkeypatch.setattr(u, "independent_source_valid", lambda edges: False)
    with pytest.raises(AssertionError, match="independent graph enumerations"):
        u.all_registered_graphs()


def test_original_simple_graph_incorrect_terminal_degree_is_excluded():
    graph = ((0, 1), (0, 2), (0, 3), (1, 4), (2, 3), (3, 5), (4, 5))
    assert not u.source_valid(graph)
    assert not u.independent_source_valid(graph)
    assert (0, 5) not in graph


def test_direct_terminal_connection_cannot_enter_family():
    network = tuple(sorted(((0, 1), (0, 5), (1, 2), (2, 5),
                            (0, 3), (3, 4), (4, 5))))
    assert not u.source_valid(network)
    assert not u.independent_source_valid(network)


def test_original_pre_loss_degrees_and_neighbors_are_fixed():
    B = example("B")
    assert u.old_neighbors(B, 2) == (1, 3, 4, 5)
    degrees = u.original_degrees(B)
    assert degrees[2] == 4
    assert degrees[0] == degrees[5] == 2
    assert u.policy_order(B, 2, "ASC")[0] == (1, 3, 4, 5)
    assert sorted(u.policy_order(B, 2, "DEGREE")[0]) == [1, 3, 4, 5]


@pytest.mark.parametrize("graph", ["A", "B"])
@pytest.mark.parametrize("lost", [1, 2, 3, 4])
def test_registered_equal_budget_across_every_policy_toy_example(graph, lost):
    base = example(graph)
    traces = {p: u.trace_for_policy(base, lost, p) for p in u.POLICIES}
    costs = []
    for p, record in traces.items():
        assert record["order"] and len(record["order"]) == len(u.old_neighbors(base, lost))
        assert len(set(record["order"])) == len(record["order"])
        assert record["post_failure_F1"] == sum(s["F1"] for s in record["snapshots"][1:])
        assert record["post_failure_F2"] == sum(s["F2"] for s in record["snapshots"][1:])
        assert all(s["F2"] <= s["F1"] for s in record["snapshots"])
        costs.append([
            (s["node_count"], s["edge_count"], s["cumulative_repaired_edges"])
            for s in record["snapshots"]
        ])
    assert all(x == costs[0] for x in costs)
    assert costs[0][0] == (6, 7, 0)
    assert costs[0][1][0] == 5
    assert costs[0][2][0] == 6


def test_step_count_and_new_identity_remains_distinct_from_failed():
    base = example("B")
    old = u.old_neighbors(base, 2)
    for p in u.POLICIES:
        record = u.trace_for_policy(base, 2, p)
        for s in record["snapshots"][2:]:
            expected_budget = min(s["t"] - 1, len(old))
            assert s["cumulative_repaired_edges"] == expected_budget
            assert s["node_count"] == 6


def test_one_and_two_step_task_rules_do_not_have_future_empirical_labels():
    base = example("B")
    for p in ("GREEDY1", "LOOKAHEAD2"):
        order, ops = u.policy_order(base, 2, p)
        assert set(order) == set(u.old_neighbors(base, 2))
        assert ops > 0
    assert u.policy_order(base, 2, "ASC")[1] == 0
    assert u.policy_order(base, 2, "DEGREE")[1] == 0


def test_offline_envelope_is_per_function_per_time_bound_not_deployable_rule():
    for graph in ("A", "B"):
        base = example(graph)
        for lost in u.INTERNAL:
            upper = u.offline_envelope(base, lost)
            assert len(upper) == 7
            for policy in u.POLICIES:
                trace = u.trace_for_policy(base, lost, policy)
                for actual, limit in zip(trace["snapshots"], upper):
                    assert actual["F1"] <= limit["F1"]
                    assert actual["F2"] <= limit["F2"]


def test_disconnected_graph_then_function_checks_consistent():
    edges = frozenset({(0, 1), (3, 5)})
    nodes = frozenset({0, 1, 3, 5})
    assert u.functions(edges, nodes) == (0, 0)


def test_two_paths_means_two_disjoint_internal_node_routes():
    edges = frozenset({
        (0, 1), (1, 5), (0, 2), (2, 5), (1, 2),
    })
    nodes = frozenset({0, 1, 2, 5})
    assert u.functions(edges, nodes) == (1, 1)
    assert u.functions(edges - {(2, 5)}, nodes) == (1, 0)


def test_f1_second_oracle_disagreement_rejects_research(monkeypatch):
    monkeypatch.setattr(u, "all_simple_paths", lambda *args, **kwargs: ())
    with pytest.raises(AssertionError, match="BFS and simple DFS"):
        u.functions(frozenset(example("A")), frozenset(range(6)))


def test_f2_independent_oracles_mismatch_fails_closed(monkeypatch):
    monkeypatch.setattr(u, "connected_bfs", lambda *args, **kwargs: True)
    edges = frozenset({(0, 1), (1, 5)})
    nodes = frozenset({0, 1, 5})
    with pytest.raises(AssertionError):
        u.functions(edges, nodes)


def test_invalid_forced_repair_edge_not_from_failed_vertex_neighborhood():
    base = example("B")
    with pytest.raises(AssertionError, match="Unregistered"):
        u.direct_snapshot(base, 2, (0,))
    with pytest.raises(AssertionError, match="duplicate"):
        u.direct_snapshot(base, 2, (1, 1))


def test_fake_original_vertex_return_or_wrong_repair_edge_is_caught(monkeypatch):
    base = example("B")
    natural = u.build_by_events
    def bad(base, lost, seq):
        steps = natural(base, lost, seq)
        edges, nodes = steps[3]
        steps[3] = (edges, nodes | {lost})
        return steps
    monkeypatch.setattr(u, "build_by_events", bad)
    with pytest.raises(AssertionError, match="snapshot disagree|budget|returned"):
        u.trace_for_policy(base, 2, "ASC")


def test_deliberately_wrong_policy_order_is_rejected(monkeypatch):
    base = example("B")
    monkeypatch.setattr(u, "policy_order", lambda *args: ((1, 1, 3, 4), 0))
    with pytest.raises(AssertionError, match="precisely original"):
        u.trace_for_policy(base, 2, "ASC")


def test_unknown_policy_and_unregistered_missing_component_rejected():
    base = example("B")
    with pytest.raises(AssertionError):
        u.policy_order(base, 2, "posthoc_custom")
    with pytest.raises(AssertionError):
        u.old_neighbors(base, 0)
    with pytest.raises(AssertionError):
        u.old_neighbors(base, 5)


def test_static_degree_baseline_does_not_claim_equal_policy_CPU_time():
    base = example("B")
    simple = u.policy_order(base, 2, "DEGREE")[1]
    aware = u.policy_order(base, 2, "LOOKAHEAD2")[1]
    assert simple == 0 and aware > 0


def test_time_reference_budget_prevents_unequal_policy_comparisons():
    base = example("B")
    records = u.trace_for_policy(base, 2, "ASC")["snapshots"]
    assert records[0]["edge_count"] == 7
    assert records[1]["edge_count"] == 3
    assert [r["edge_count"] for r in records[2:]] == [4, 5, 6, 7, 7]
