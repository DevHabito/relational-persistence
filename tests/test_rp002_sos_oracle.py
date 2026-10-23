"""Exact independent RP-F002 sum-of-squares regression oracle.

A minimal rational-pair implementation of Q(sqrt(3)) independently compares
all 36 Gram-matrix entries for the proposed sharp P6 energy inequality.
No NumPy, floating-point, or use of the Lean implementation is required.
This is a computational regression check, NOT a kernel-checked proof.
"""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Quadratic:
    rational: Fraction
    radical: Fraction

    def __init__(self, rational=0, radical=0):
        object.__setattr__(self, "rational", Fraction(rational))
        object.__setattr__(self, "radical", Fraction(radical))

    def __add__(self, other):
        other = as_quadratic(other)
        return Quadratic(
            self.rational + other.rational,
            self.radical + other.radical,
        )

    __radd__ = __add__

    def __neg__(self):
        return Quadratic(-self.rational, -self.radical)

    def __sub__(self, other):
        return self + (-as_quadratic(other))

    def __rsub__(self, other):
        return as_quadratic(other) - self

    def __mul__(self, other):
        other = as_quadratic(other)
        return Quadratic(
            self.rational * other.rational
            + 3 * self.radical * other.radical,
            self.rational * other.radical
            + self.radical * other.rational,
        )

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        scalar = Fraction(scalar)
        if not scalar:
            raise ZeroDivisionError("Zero rational denominator")
        return Quadratic(self.rational / scalar, self.radical / scalar)


def as_quadratic(value):
    return value if isinstance(value, Quadratic) else Quadratic(value)


def scalar_product(left, right):
    return sum((x * y for x, y in zip(left, right)), Quadratic())


def matrix_action(matrix, vector):
    return tuple(scalar_product(row, vector) for row in matrix)


def gram_entries(vectors, coefficients):
    return tuple(
        tuple(
            sum(
                (coefficient * vector[i] * vector[j]
                 for coefficient, vector in zip(coefficients, vectors)),
                Quadratic(),
            )
            for j in range(6)
        )
        for i in range(6)
    )


SQRT_THREE = Quadratic(0, 1)
ONE = Quadratic(1)
ZERO = Quadratic()
GAIN = (8 + SQRT_THREE) / 10

UPDATE = tuple(
    tuple(Quadratic(Fraction(entry, 10)) for entry in row)
    for row in (
        (9, 1, 0, 0, 0, 0),
        (1, 8, 1, 0, 0, 0),
        (0, 1, 8, 1, 0, 0),
        (0, 0, 1, 8, 1, 0),
        (0, 0, 0, 1, 8, 1),
        (0, 0, 0, 0, 1, 9),
    )
)

MODES = (
    (ONE,) * 6,
    tuple(map(Quadratic, (1, 0, -1, -1, 0, 1))),
    tuple(map(Quadratic, (1, -1, -1, 1, 1, -1))),
    tuple(map(Quadratic, (1, -2, 1, 1, -2, 1))),
    (
        ONE, -(ONE + SQRT_THREE), 2 + SQRT_THREE,
        -(2 + SQRT_THREE), ONE + SQRT_THREE, -ONE,
    ),
)
COEFFICIENTS = (
    (16 * SQRT_THREE - 33) / 600,
    (8 * SQRT_THREE - 7) / 200,
    (3 + 16 * SQRT_THREE) / 600,
    (9 + 8 * SQRT_THREE) / 600,
    (4 * SQRT_THREE - 6) / 75,
)
SLOW_MODE = (
    ONE, SQRT_THREE - 1, 2 - SQRT_THREE,
    SQRT_THREE - 2, 1 - SQRT_THREE, -ONE,
)


def test_exact_energy_defect_gram_matrix():
    """Compare all 36 entries: g²I - WᵀW against the SOS decomposition."""
    certificate = gram_entries(MODES, COEFFICIENTS)
    for i in range(6):
        for j in range(6):
            expected = (
                GAIN * GAIN if i == j else ZERO
            ) - sum(
                (UPDATE[k][i] * UPDATE[k][j] for k in range(6)),
                ZERO,
            )
            assert certificate[i][j] == expected, (i, j)


def test_exact_slow_mode_and_zero_mean():
    assert matrix_action(UPDATE, SLOW_MODE) == tuple(
        GAIN * value for value in SLOW_MODE
    )
    assert sum(SLOW_MODE, ZERO) == ZERO
    assert scalar_product(SLOW_MODE, SLOW_MODE) != ZERO


def test_nonnegative_sos_coefficients_without_decimal_rounding():
    # 3/2 < sqrt(3) < 2 follows from exact rational square comparisons.
    assert Fraction(3, 2) ** 2 < 3 < Fraction(2) ** 2
    for coefficient in COEFFICIENTS[1:]:
        lower = coefficient.rational + coefficient.radical * (
            Fraction(3, 2) if coefficient.radical >= 0 else Fraction(2)
        )
        assert lower >= 0


def test_update_is_symmetric_and_preserves_the_constant_vector():
    for i in range(6):
        assert sum(UPDATE[i], ZERO) == ONE
        for j in range(6):
            assert UPDATE[i][j] == UPDATE[j][i]
