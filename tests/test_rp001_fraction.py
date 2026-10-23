"""An independent exact-fraction regression oracle for RP-001.

The implementation uses a signed edge-incidence update and the Python
standard library only, rather than NumPy eigendecomposition, NetworkX,
or the coordinate update definitions in Lean. Agreement is regression
evidence, not proof of a universal law or empirical validation.
"""

from fractions import Fraction

VERTICES = tuple(range(6))
GAIN = Fraction(1, 10)
PATH_EDGES = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5))
STAR_EDGES = tuple((0, vertex) for vertex in VERTICES[1:])
START = tuple(map(Fraction, (1, 1, 1, -1, -1, -1)))


def step(edges, state):
    """Perform x -> (Id - alpha L) x by accumulating signed edge flux."""
    if len(state) != 6:
        raise ValueError("The frozen RP-001 experiment has six vertices")
    change = [Fraction(0) for _ in VERTICES]
    for left, right in edges:
        delta = GAIN * (state[left] - state[right])
        change[left] += delta
        change[right] -= delta
    return tuple(state[index] - change[index] for index in VERTICES)


def evolve(edges, state, horizon=20):
    for _ in range(horizon):
        state = step(edges, state)
    return state


def energy(state):
    return sum((coordinate**2 for coordinate in state), Fraction(0))


def test_same_vertex_and_edge_counts():
    assert len(VERTICES) == 6
    assert len(PATH_EDGES) == len(STAR_EDGES) == 5


def test_path_witness_exceeds_exact_lower_threshold():
    result = evolve(PATH_EDGES, START)
    assert energy(result) > Fraction(1, 5) ** 2 * energy(START)
    assert result[0] == Fraction(
        17969771336684377939, 25000000000000000000
    )


def test_star_witness_respects_uniform_bound():
    result = evolve(STAR_EDGES, START)
    assert energy(result) <= Fraction(3, 20) ** 2 * energy(START)


def test_step_preserves_total_for_both_graphs():
    samples = [
        START,
        tuple(Fraction(v, 7) for v in (3, 4, -5, -9, 7, 2)),
    ]
    for edges in (PATH_EDGES, STAR_EDGES):
        for initial in samples:
            assert sum(step(edges, initial)) == sum(initial)


def test_graph_relabeling_equivariance():
    permutation = (5, 3, 1, 4, 2, 0)
    for edges in (PATH_EDGES, STAR_EDGES):
        renamed_edges = tuple(
            (permutation[left], permutation[right])
            for left, right in edges
        )
        renamed_state = [Fraction(0)] * 6
        for old, new in enumerate(permutation):
            renamed_state[new] = START[old]
        reference = evolve(edges, START)
        renamed = evolve(renamed_edges, tuple(renamed_state))
        for old, new in enumerate(permutation):
            assert reference[old] == renamed[new]
