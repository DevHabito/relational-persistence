"""Spectral calculations for a declared linear consensus model.

These are applications of classical matrix analysis, not new physical laws.
"""

from dataclasses import asdict, dataclass
from math import isfinite

import networkx as nx
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ConsensusResult:
    nodes: int
    edges: int
    alpha: float
    horizon: int
    noise_variance: float
    algebraic_connectivity: float
    largest_laplacian_eigenvalue: float
    contraction_factor: float
    residual_at_horizon: float
    stationary_total_disagreement: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def scalar_capacity_noise_latency_index(
    updates_per_step: float, noise_variance: float, latency_steps: float
) -> float:
    """An operational index, *not* an externally validated persistence measure."""
    parameters = (updates_per_step, noise_variance, latency_steps)
    if not all(isfinite(value) and value > 0 for value in parameters):
        raise ValueError("All operational proxy values must be finite and positive")
    return updates_per_step / (noise_variance * latency_steps)


def _validate_graph(graph: nx.Graph) -> None:
    if graph.is_directed() or graph.is_multigraph():
        raise ValueError("The protocol assumes a simple undirected graph")
    if graph.number_of_nodes() < 2 or not nx.is_connected(graph):
        raise ValueError("The protocol assumes a connected graph with at least 2 nodes")
    if nx.number_of_selfloops(graph) != 0:
        raise ValueError("Self-loops are excluded by the declared unweighted model")


def _laplacian(graph: nx.Graph) -> NDArray[np.float64]:
    # Ignore the empirical graph's edge-weight attributes in this experiment.
    adjacency = nx.to_numpy_array(graph, weight=None, dtype=np.float64)
    degree = np.diag(adjacency.sum(axis=1))
    return degree - adjacency


def evaluate_consensus(
    graph: nx.Graph, *, alpha: float, horizon: int, noise_variance: float
) -> ConsensusResult:
    """Compute exact-model spectral outcomes with finite-precision numerics.

    x[t+1] = (Identity - alpha * Laplacian) x[t] + xi[t].
    xi has independent centered entries, each of variance noise_variance.
    Disagreement removes the all-ones (consensus) mode. No simulation needed.
    """
    _validate_graph(graph)
    if not isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be finite and positive")
    if not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be an integer >= 1")
    if not isfinite(noise_variance) or noise_variance <= 0:
        raise ValueError("noise_variance must be finite and positive")

    eigenvalues = np.linalg.eigvalsh(_laplacian(graph))
    non_consensus = eigenvalues[1:]
    if not np.isclose(eigenvalues[0], 0.0, atol=1e-10):
        raise ValueError("Consensus eigenvalue must be zero")
    if non_consensus[0] <= 1e-10:
        raise ValueError("Expected a connected graph with positive algebraic connectivity")

    multipliers = 1.0 - alpha * non_consensus
    if np.any(np.abs(multipliers) >= 1.0):
        raise ValueError("Non-consensus modes must contract to define stationary energy")

    contraction = float(np.max(np.abs(multipliers)))
    energy = float(np.sum(noise_variance / (1.0 - np.square(multipliers))))

    return ConsensusResult(
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        alpha=alpha,
        horizon=horizon,
        noise_variance=noise_variance,
        algebraic_connectivity=float(non_consensus[0]),
        largest_laplacian_eigenvalue=float(non_consensus[-1]),
        contraction_factor=contraction,
        residual_at_horizon=float(contraction**horizon),
        stationary_total_disagreement=energy,
    )


def matrix_power_residual(graph: nx.Graph, *, alpha: float, horizon: int) -> float:
    """Independent matrix-power check of the worst-case disagreement residual."""
    _validate_graph(graph)
    count = graph.number_of_nodes()
    laplacian = _laplacian(graph)
    projection = np.eye(count) - np.ones((count, count)) / count
    transition = np.eye(count) - alpha * laplacian
    return float(np.linalg.norm(projection @ np.linalg.matrix_power(transition, horizon) @ projection, ord=2))


def ar1_variance_state(*, coefficient: float, noise_variance: float) -> str:
    """Classify asymptotic AR(1) variance under independent nonzero-variance noise."""
    if not isfinite(coefficient) or not isfinite(noise_variance) or noise_variance <= 0:
        raise ValueError("Parameters must be finite and noise variance positive")
    return "finite" if abs(coefficient) < 1 else "unbounded"
