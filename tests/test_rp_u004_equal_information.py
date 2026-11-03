"""Adversarial and structural checks for the prospectively frozen RP-U004.

These checks intentionally do NOT execute the main selected-family benchmark
or assert a result for H1/H2. First outcome belongs to the archived hosted run.
"""

from __future__ import annotations

from itertools import combinations

import pytest

from experiments import rp_u004_equal_information as u


FIXTURE = (
    (0, 1), (0, 2), (1, 3), (1, 6),
    (2, 4), (2, 6), (3, 4), (4, 5),
)


def test_fixed_source_model_and_original_protocol_anchor():
    assert u.PREREG == "186d6fc5d8cc6451fca63abb5f6ef4f2029a3d7b"
    assert len(u.PAIRS) == 20
    assert len(u.INNER_PAIRS) == 10
    assert (0, 6) not in u.PAIRS
    assert u.TIMES == (1, 2, 3, 4, 5, 6)
    assert u.INTERNAL == (1, 2, 3, 4, 5)
    assert u.POLICIES == (
        "ASC", "DEGREE", "GREEDY_F1", "GREEDY_F2",
        "LOOKAHEAD2_F1", "LOOKAHEAD2_F2",
    )


def test_dual_structural_enumerators_and_degree_pair_selection_agree():
    # No policy scores or candidate selection by observed outcome.
    graphs = u.all_source_graphs()
    assert graphs
    assert graphs == tuple(sorted(graphs))
    assert len(graphs) == len(set(graphs))
    for graph in graphs:
        assert len(graph) == 8
        assert u.source_valid(graph)
        assert u.independent_source_valid(graph)
        assert u.degrees(graph)[0] == u.degrees(graph)[6] == 2
    pairs, singletons = u.matched_degree_pairs(graphs)
    assert pairs and singletons >= 0
    selected = []
    for degree_key, first, last in pairs:
        assert first < last
        assert u.degrees(first) == degree_key == u.degrees(last)
        selected.extend((first, last))
    assert len(selected) == len(set(selected))


def test_source_pair_enumerator_disagreement_is_fatal(monkeypatch):
    monkeypatch.setattr(u, "independent_source_valid", lambda _graph: False)
    with pytest.raises(AssertionError, match="enumerators disagree"):
        u.all_source_graphs()


def test_source_rejects_direct_terminal_edge_invalid_count_and_disconnection():
    assert not u.source_valid(FIXTURE + ((0, 6),))
    assert not u.independent_source_valid(FIXTURE + ((0, 6),))
    assert not u.source_valid(FIXTURE[:-1])
    assert not u.independent_source_valid(FIXTURE[:-1])
    disconnected = (
        (0, 1), (0, 2), (1, 2), (1, 3),
        (4, 5), (4, 6), (5, 6), (3, 2),
    )
    assert not u.source_valid(disconnected)


def test_independent_oracles_and_two_route_negative_control():
    edges, nodes = frozenset(FIXTURE), u.VERTICES
    assert u.functions(edges, nodes) == (1, 1)
    assert u.functions(edges - {(2, 6)}, nodes) == (1, 0)
    assert u.functions(frozenset({(0, 1), (3, 6)}), nodes) == (0, 0)


def test_f1_oracle_disagreement_is_a_stopping_error(monkeypatch):
    monkeypatch.setattr(u, "all_simple_paths", lambda *_args: ())
    with pytest.raises(AssertionError, match="F1 BFS and DFS"):
        u.functions(frozenset(FIXTURE), u.VERTICES)


def test_f2_oracle_disagreement_is_a_stopping_error(monkeypatch):
    monkeypatch.setattr(u, "reachable_bfs", lambda *_args, **_kw: True)
    with pytest.raises(AssertionError, match="F2 disjoint-path and cut"):
        u.functions(frozenset({(0, 1), (1, 6)}), u.VERTICES)


def test_replacement_identity_time_and_edge_budget():
    assert u.source_valid(FIXTURE)
    neighbors = u.old_neighbors(FIXTURE, 3)
    assert neighbors == (1, 4)
    first_edges, first_nodes = u.snapshot(FIXTURE, 3, (), 1)
    assert 3 not in first_nodes and len(first_nodes) == 6
    assert len(first_edges) == 6
    second_edges, second_nodes = u.snapshot(FIXTURE, 3, (1,), 2)
    assert second_nodes == frozenset({0, 1, 2, 4, 5, 6, 10})
    assert (1, 10) in second_edges
    assert len(second_edges) == 7
    with pytest.raises(AssertionError):
        u.snapshot(FIXTURE, 3, (0,), 2)
    with pytest.raises(AssertionError):
        u.snapshot(FIXTURE, 3, (1, 1), 3)


@pytest.mark.parametrize("lost", u.INTERNAL)
def test_same_information_cost_and_offline_bounds_on_fixed_fixture(lost):
    table = u.truth_table(FIXTURE, lost)
    neighbors = u.old_neighbors(FIXTURE, lost)
    assert len(table) == 2 ** len(neighbors)
    offline = u.offline_optimum(FIXTURE, lost, table)
    assert offline["permutations"] >= 1
    policies = [u.policy_trace(FIXTURE, lost, policy, table)
                for policy in u.POLICIES]
    cost_trace = None
    for record in policies:
        current = [
            (row["node_count"], row["edge_count"], row["repaired_edges"])
            for row in record["snapshots"]
        ]
        if cost_trace is None:
            cost_trace = current
        else:
            assert current == cost_trace
        assert record["F1_uptime"] <= offline["F1"]
        assert record["F2_uptime"] <= offline["F2"]
        assert all(s["F2"] <= s["F1"] for s in record["snapshots"])
        assert len(record["order"]) == len(neighbors)
        assert set(record["order"]) == set(neighbors)


def test_adversarial_replay_mismatch_is_rejected(monkeypatch):
    base = u.event_replay
    def corrupt(graph, lost, order):
        states = list(base(graph, lost, order))
        old_edges, old_nodes = states[1]
        states[1] = (old_edges, old_nodes | {lost})
        return states
    monkeypatch.setattr(u, "event_replay", corrupt)
    with pytest.raises(AssertionError, match="replay disagrees"):
        u.policy_trace(FIXTURE, 3, "ASC", u.truth_table(FIXTURE, 3))


def test_relabeled_graph_retains_its_structural_rules():
    for lost in u.INTERNAL:
        relabeled, relost = u.cyclic_relabel(FIXTURE, lost)
        assert u.independent_source_valid(relabeled)
        assert relost in u.INTERNAL
        assert len(u.old_neighbors(relabeled, relost)) == len(
            u.old_neighbors(FIXTURE, lost)
        )


def test_no_hidden_policy_or_outcome_target_posthoc():
    assert "adaptive_learned" not in u.POLICIES
    assert not hasattr(u, "preferred_graphs_from_results")
    assert u.canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert len(u.hash_sequence([list(FIXTURE)])) == 64


def test_original_f2_is_measured_before_failure_not_assumed_from_degrees():
    assert u.source_valid(FIXTURE)
    assert u.functions(frozenset(FIXTURE), u.VERTICES)[1] == 1
    # Removing a single terminal edge retains F1 but destroys two-route F2.
    damaged = frozenset(FIXTURE) - {(2, 6)}
    assert u.functions(damaged, u.VERTICES) == (1, 0)


def test_precomputed_subset_table_is_complete_and_not_policy_specific():
    table = u.truth_table(FIXTURE, 3)
    neighbors = u.old_neighbors(FIXTURE, 3)
    expected = {
        frozenset(subset)
        for n in range(len(neighbors) + 1)
        for subset in combinations(neighbors, n)
    }
    assert set(table) == expected
    for policy in u.POLICIES:
        assert set(u.policy_trace(FIXTURE, 3, policy, table)["order"]) == set(neighbors)


def test_offline_optimum_repair_orders_are_actual_argmax():
    """Each claimed optimum must be attained by its reported repair order."""
    graph, lost = FIXTURE, 3
    table = u.truth_table(graph, lost)
    optimum = u.offline_optimum(graph, lost, table)
    eligible = u.old_neighbors(graph, lost)
    for metric in ("F1", "F2"):
        order = tuple(optimum[f"{metric}_optimal_order_first_lex"])
        assert tuple(sorted(order)) == eligible
        assert 1 <= optimum[f"{metric}_optimal_order_count"] <= optimum["permutations"]
        original_edges, original_nodes = u.snapshot(graph, lost, (), 1)
        original_score = u.functions(original_edges, original_nodes)[0 if metric == "F1" else 1]
        trace_score = sum(
            table[frozenset(order[:min(tick - 1, len(order))])][0 if metric == "F1" else 1]
            for tick in range(2, 7)
        )
        assert original_score + trace_score == optimum[metric]


def test_degree_stratum_census_accounts_for_all_accepted_sources():
    from collections import Counter

    accepted = u.all_source_graphs()
    degree_counts = Counter(u.degrees(graph) for graph in accepted)
    pairs, singleton_count = u.matched_degree_pairs(accepted)
    assert sum(degree_counts.values()) == len(accepted)
    assert singleton_count == sum(count == 1 for count in degree_counts.values())
    assert len(pairs) == sum(count >= 2 for count in degree_counts.values())
