"""Exact characteristic-polynomial regression certificates for RP-F002.

Independent of NumPy's eigensolver, NetworkX, and the Lean coordinate
recurrence: compute det(tI-L) from the Leibniz formula with Fraction
arithmetic. These tests are computational checks, not formal proofs.
"""

from fractions import Fraction
from itertools import permutations

PATH_EDGES = tuple((i, i + 1) for i in range(5))
STAR_EDGES = tuple((0, i) for i in range(1, 6))


def graph_laplacian(edges, n=6):
    matrix = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for i, j in edges:
        if not (0 <= i < n and 0 <= j < n) or i == j:
            raise ValueError("Expected distinct in-range vertices")
        matrix[i][i] += 1
        matrix[j][j] += 1
        matrix[i][j] -= 1
        matrix[j][i] -= 1
    return matrix


def multiply_polynomials(a, b):
    result = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y
    return result


def factored_polynomial(*factors):
    result = [Fraction(1)]
    for factor in factors:
        result = multiply_polynomials(result, [Fraction(c) for c in factor])
    return result


def characteristic_polynomial(laplacian):
    """Return det(tI-L), coefficients ordered from low to high degree."""
    n = len(laplacian)
    coefficients = [Fraction(0)] * (n + 1)
    for perm in permutations(range(n)):
        inversion_count = sum(
            perm[i] > perm[j]
            for i in range(n)
            for j in range(i + 1, n)
        )
        polynomial = [Fraction(1)]
        for i, j in enumerate(perm):
            polynomial = multiply_polynomials(
                polynomial, [-laplacian[i][j], Fraction(i == j)]
            )
        sign = (-1) ** inversion_count
        for k, coefficient in enumerate(polynomial):
            coefficients[k] += sign * coefficient
    return coefficients


def test_path_laplacian_characteristic_polynomial():
    actual = characteristic_polynomial(graph_laplacian(PATH_EDGES))
    expected = factored_polynomial(
        (0, 1), (-1, 1), (-2, 1), (-3, 1), (1, -4, 1)
    )
    assert actual == expected
    assert actual[-1] == 1


def test_star_laplacian_characteristic_polynomial():
    actual = characteristic_polynomial(graph_laplacian(STAR_EDGES))
    expected = factored_polynomial(
        (0, 1), (-6, 1), *([(-1, 1)] * 4)
    )
    assert actual == expected
    assert actual[-1] == 1


def test_vertex_relabeling_preserves_polynomial():
    permutation = (5, 2, 4, 0, 3, 1)
    for edges in (PATH_EDGES, STAR_EDGES):
        renamed_edges = tuple(
            (permutation[i], permutation[j]) for i, j in edges
        )
        assert characteristic_polynomial(graph_laplacian(renamed_edges)) == (
            characteristic_polynomial(graph_laplacian(edges))
        )


def test_trace_coefficient_identity():
    for edges in (PATH_EDGES, STAR_EDGES):
        laplacian = graph_laplacian(edges)
        coefficients = characteristic_polynomial(laplacian)
        assert coefficients[-2] == -sum(
            laplacian[i][i] for i in range(6)
        ) == -10
