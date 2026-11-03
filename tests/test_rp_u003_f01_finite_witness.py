"""Frozen, previously inspected RP-U003-F01 finite-policy witness regression.

This is a regression for an already known synthetic scenario, not
out-of-sample evidence or a Lean/Python soundness equivalence proof.
"""
from experiments import rp_u003_equal_budget as u

WITNESS_GRAPH = (
    (0, 1), (0, 2), (1, 3), (1, 4), (1, 5), (2, 3), (3, 5),
)
FAILED_VERTEX = 3


def test_known_witness_is_in_the_registered_graph_family():
    assert u.source_valid(WITNESS_GRAPH)
    assert WITNESS_GRAPH in u.all_registered_graphs()
    assert u.old_neighbors(WITNESS_GRAPH, FAILED_VERTEX) == (1, 2, 5)


def test_frozen_policy_orders_and_equal_t3_cost():
    greedy_order, greedy_work = u.policy_order(
        WITNESS_GRAPH, FAILED_VERTEX, "GREEDY1"
    )
    lookahead_order, lookahead_work = u.policy_order(
        WITNESS_GRAPH, FAILED_VERTEX, "LOOKAHEAD2"
    )
    assert greedy_order == (1, 2, 5)
    assert lookahead_order == (2, 5, 1)
    assert greedy_work < lookahead_work
    greedy_trace = u.trace_for_policy(WITNESS_GRAPH, FAILED_VERTEX, "GREEDY1")
    lookahead_trace = u.trace_for_policy(WITNESS_GRAPH, FAILED_VERTEX, "LOOKAHEAD2")
    gs = greedy_trace["snapshots"][3]
    ls = lookahead_trace["snapshots"][3]
    assert (
        gs["node_count"], gs["edge_count"], gs["cumulative_repaired_edges"]
    ) == (6, 6, 2)
    assert (
        ls["node_count"], ls["edge_count"], ls["cumulative_repaired_edges"]
    ) == (6, 6, 2)
    assert (gs["F1"], gs["F2"]) == (1, 0)
    assert (ls["F1"], ls["F2"]) == (1, 1)


def test_exact_t3_graph_edges_two_oracles_and_cut_control():
    greedy, nodes = u.snapshot(WITNESS_GRAPH, FAILED_VERTEX, (1, 2), t=3)
    lookahead, nodes2 = u.snapshot(WITNESS_GRAPH, FAILED_VERTEX, (2, 5), t=3)
    assert nodes == nodes2 == frozenset({0, 1, 2, 4, 5, 9})
    assert greedy == frozenset({
        (0, 1), (0, 2), (1, 4), (1, 5), (1, 9), (2, 9),
    })
    assert lookahead == frozenset({
        (0, 1), (0, 2), (1, 4), (1, 5), (2, 9), (5, 9),
    })
    assert u.functions(greedy, nodes) == (1, 0)
    assert u.functions(lookahead, nodes2) == (1, 1)
    assert not u.connected_bfs(greedy, nodes, 0, 5, excluded=1)
    assert u.connected_bfs(lookahead, nodes2, 0, 5, excluded=1)
    paths = u.all_simple_paths(lookahead, nodes2)
    assert (0, 1, 5) in paths
    assert (0, 2, 9, 5) in paths
    assert set((0, 1, 5)[1:-1]).isdisjoint((0, 2, 9, 5)[1:-1])
