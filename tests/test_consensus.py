"""Regression, adversarial, and boundary tests for the declared baseline."""

import networkx as nx
import pytest

from relational_persistence.consensus import (
    ar1_variance_state,
    evaluate_consensus,
    matrix_power_residual,
    scalar_capacity_noise_latency_index,
)


@pytest.mark.parametrize("graph", [nx.path_graph(6), nx.star_graph(5)])
def test_spectral_and_matrix_power_agree(graph: nx.Graph) -> None:
    result = evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.01)
    direct = matrix_power_residual(graph, alpha=0.1, horizon=20)
    assert result.residual_at_horizon == pytest.approx(direct, abs=1e-10)


def test_preregistered_graph_pair_has_identical_scalar_index_but_distinct_outcome() -> None:
    a = evaluate_consensus(nx.path_graph(6), alpha=0.1, horizon=20, noise_variance=0.01)
    b = evaluate_consensus(nx.star_graph(5), alpha=0.1, horizon=20, noise_variance=0.01)
    assert (a.nodes, a.edges) == (b.nodes, b.edges) == (6, 5)
    assert scalar_capacity_noise_latency_index(1.0, 0.01, 1.0) == 100.0
    assert a.residual_at_horizon - b.residual_at_horizon >= 0.05


def test_relabeling_does_not_change_results() -> None:
    base = nx.path_graph(6)
    relabeled = nx.relabel_nodes(base, {i: f"node-{5-i}" for i in range(6)})
    a = evaluate_consensus(base, alpha=0.1, horizon=20, noise_variance=0.01)
    b = evaluate_consensus(relabeled, alpha=0.1, horizon=20, noise_variance=0.01)
    assert a.residual_at_horizon == pytest.approx(b.residual_at_horizon, abs=1e-12)
    assert a.stationary_total_disagreement == pytest.approx(b.stationary_total_disagreement, abs=1e-12)


def test_self_comparison_is_zero() -> None:
    graph = nx.path_graph(6)
    a = evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.01)
    b = evaluate_consensus(graph.copy(), alpha=0.1, horizon=20, noise_variance=0.01)
    assert a.residual_at_horizon - b.residual_at_horizon == pytest.approx(0)


def test_noise_scaling_and_deterministic_independence() -> None:
    graph = nx.path_graph(6)
    a = evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.01)
    b = evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.02)
    assert b.stationary_total_disagreement == pytest.approx(2 * a.stationary_total_disagreement)
    assert b.residual_at_horizon == a.residual_at_horizon


def test_contraction_when_alpha_is_valid() -> None:
    for graph in (nx.path_graph(6), nx.star_graph(5)):
        result = evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.01)
        assert 0 <= result.residual_at_horizon < 1
        assert result.algebraic_connectivity > 0


@pytest.mark.parametrize("graph", [nx.empty_graph(6), nx.DiGraph([(0, 1)]), nx.Graph([(0, 0), (0, 1)])])
def test_invalid_graphs_fail_closed(graph: nx.Graph) -> None:
    with pytest.raises(ValueError):
        evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=0.01)


@pytest.mark.parametrize("alpha", [-0.2, 0.0, 1.0, float("nan")])
def test_invalid_or_unstable_alpha_is_rejected(alpha: float) -> None:
    with pytest.raises(ValueError):
        evaluate_consensus(nx.star_graph(5), alpha=alpha, horizon=20, noise_variance=0.01)


def test_negative_or_zero_noise_is_rejected() -> None:
    with pytest.raises(ValueError):
        evaluate_consensus(nx.path_graph(6), alpha=0.1, horizon=20, noise_variance=0)
    with pytest.raises(ValueError):
        scalar_capacity_noise_latency_index(1.0, 0, 1.0)


def test_ar1_counterexample() -> None:
    assert ar1_variance_state(coefficient=0.5, noise_variance=0.01) == "finite"
    assert ar1_variance_state(coefficient=1.1, noise_variance=0.01) == "unbounded"
    assert ar1_variance_state(coefficient=1.0, noise_variance=0.01) == "unbounded"


def test_exhaustive_connected_four_vertex_graphs_agree_across_implementations() -> None:
    """Exhaustive finite check over all 2^6 labeled four-node simple graphs."""
    import itertools

    edges = list(itertools.combinations(range(4), 2))
    connected_count = 0
    for mask in range(1 << len(edges)):
        graph = nx.Graph()
        graph.add_nodes_from(range(4))
        graph.add_edges_from(edge for j, edge in enumerate(edges) if (mask >> j) & 1)
        if not nx.is_connected(graph):
            continue
        connected_count += 1
        alpha = 0.5 / max(dict(graph.degree()).values())
        evaluation = evaluate_consensus(graph, alpha=alpha, horizon=12, noise_variance=0.02)
        power = matrix_power_residual(graph, alpha=alpha, horizon=12)
        assert evaluation.residual_at_horizon == pytest.approx(power, abs=1e-10)
    assert connected_count == 38  # Standard exhaustive count of labeled connected n=4 graphs.


def test_directed_and_nan_noise_fail_closed() -> None:
    graph = nx.path_graph(6)
    with pytest.raises(ValueError):
        evaluate_consensus(graph, alpha=0.1, horizon=20, noise_variance=float("nan"))
    with pytest.raises(ValueError):
        evaluate_consensus(graph, alpha=0.1, horizon=0, noise_variance=0.01)
    with pytest.raises(ValueError):
        ar1_variance_state(coefficient=float("nan"), noise_variance=0.01)
