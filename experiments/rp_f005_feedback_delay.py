"""RP-F005-A01: exact comparison of zero-delay and one-step delayed feedback.

Declared mathematics only. No stochastic or physical latency measurements.
Protocol: docs/preregistration/RP-F005-A01.md.
"""

from __future__ import annotations

from fractions import Fraction
import json

PRIMARY_GAIN = Fraction(1)
CONTROL_GAINS = (Fraction(1, 2), Fraction(3, 2))
REGISTERED_GAINS = (PRIMARY_GAIN, *CONTROL_GAINS)
INITIAL_CURRENT = Fraction(1)
INITIAL_PREVIOUS = Fraction(1)
MAX_STEP = 24
THRESHOLD = Fraction(1, 2)

Matrix = tuple[tuple[Fraction, ...], ...]


def exact(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def validate(delay: int, gain: Fraction, current: Fraction, previous: Fraction) -> None:
    if type(delay) is not int or delay not in (0, 1):
        raise ValueError("Only integer delay 0 or 1 is registered")
    if type(gain) is not Fraction or gain not in REGISTERED_GAINS:
        raise ValueError("Feedback gain is not a registered exact fraction")
    if current != INITIAL_CURRENT or previous != INITIAL_PREVIOUS:
        raise ValueError("Preregistered current state and prehistory cannot change")


def direct_trajectory(delay: int, gain: Fraction,
                      current: Fraction = INITIAL_CURRENT,
                      previous: Fraction = INITIAL_PREVIOUS) -> tuple[Fraction, ...]:
    """Direct scalar recurrence with explicit x[-1] for delay 1."""
    validate(delay, gain, current, previous)
    if delay == 0:
        path = [current]
        for _ in range(MAX_STEP):
            path.append(path[-1] - gain * path[-1])
        return tuple(path)

    # This indexed sequence starts at x[-1] and x[0].
    history = [previous, current]
    for _ in range(MAX_STEP):
        history.append(history[-1] - gain * history[-2])
    return tuple(history[1:])


def multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("Invalid matrix dimensions")
    if any(len(row) != len(left[0]) for row in left):
        raise ValueError("Malformed left matrix")
    if any(len(row) != len(right[0]) for row in right):
        raise ValueError("Malformed right matrix")
    return tuple(
        tuple(sum((left[i][k] * right[k][j] for k in range(len(right))),
                  Fraction(0))
              for j in range(len(right[0])))
        for i in range(len(left))
    )


def power(base: Matrix, exponent: int) -> Matrix:
    if type(exponent) is not int or not 0 <= exponent <= MAX_STEP:
        raise ValueError("Matrix power outside the registered horizon")
    if len(base) != len(base[0]) or any(len(row) != len(base) for row in base):
        raise ValueError("Square matrix required")
    result: Matrix = tuple(
        tuple(Fraction(int(i == j)) for j in range(len(base)))
        for i in range(len(base))
    )
    while exponent:
        if exponent & 1:
            result = multiply(result, base)
        exponent >>= 1
        if exponent:
            base = multiply(base, base)
    return result


def transition(delay: int, gain: Fraction) -> Matrix:
    validate(delay, gain, INITIAL_CURRENT, INITIAL_PREVIOUS)
    if delay == 0:
        return ((Fraction(1) - gain,),)
    return ((Fraction(1), -gain), (Fraction(1), Fraction(0)))


def independent_matrix_trajectory(delay: int, gain: Fraction) -> tuple[Fraction, ...]:
    """Independent companion-matrix powers, without the scalar iterator."""
    matrix = transition(delay, gain)
    state = ((INITIAL_CURRENT,),) if delay == 0 else (
        (INITIAL_CURRENT,), (INITIAL_PREVIOUS,)
    )
    return tuple(multiply(power(matrix, t), state)[0][0] for t in range(MAX_STEP + 1))


def relabelled_delayed_trajectory(gain: Fraction) -> tuple[Fraction, ...]:
    """Swap coordinates and conjugate A to check state-label invariance."""
    a = transition(1, gain)
    swap: Matrix = ((Fraction(0), Fraction(1)),
                    (Fraction(1), Fraction(0)))
    conjugated = multiply(multiply(swap, a), swap)
    relabelled_state = ((INITIAL_PREVIOUS,), (INITIAL_CURRENT,))
    return tuple(
        multiply(power(conjugated, t), relabelled_state)[1][0]
        for t in range(MAX_STEP + 1)
    )


def audit() -> dict:
    records = []
    for gain in REGISTERED_GAINS:
        delayed = transition(1, gain)
        if delayed[0][0] * delayed[1][1] - delayed[0][1] * delayed[1][0] != gain:
            raise AssertionError("Companion determinant did not equal the gain")
        for delay in (0, 1):
            direct = direct_trajectory(delay, gain)
            matrix = independent_matrix_trajectory(delay, gain)
            if direct != matrix:
                raise AssertionError("Exact direct/matrix trajectory mismatch")
            if delay == 1 and matrix != relabelled_delayed_trajectory(gain):
                raise AssertionError("Coordinate relabeling changed the trajectory")
            records.append({
                "feedback_gain": exact(gain),
                "delay_steps": delay,
                "x_minus_1_if_delayed": exact(INITIAL_PREVIOUS) if delay else None,
                "states_x0_to_x24": [exact(v) for v in direct],
                "x6": exact(direct[6]),
                "x12": exact(direct[12]),
                "x24": exact(direct[24]),
                "squared_residual_t6": exact(direct[6] ** 2 / INITIAL_CURRENT ** 2),
                "determinant_of_companion_if_delayed": exact(gain) if delay else None,
            })
    primary_undelayed = direct_trajectory(0, PRIMARY_GAIN)
    primary_delayed = direct_trajectory(1, PRIMARY_GAIN)
    energy_undelayed = primary_undelayed[6] ** 2
    energy_delayed = primary_delayed[6] ** 2
    difference = energy_delayed - energy_undelayed

    a = transition(1, PRIMARY_GAIN)
    identity: Matrix = ((Fraction(1), Fraction(0)),
                        (Fraction(0), Fraction(1)))
    negative_identity: Matrix = ((Fraction(-1), Fraction(0)),
                                 (Fraction(0), Fraction(-1)))
    if (power(a, 3) != negative_identity or
            power(a, 6) != identity or
            power(a, 12) != identity or
            primary_delayed[6] != INITIAL_CURRENT or
            primary_undelayed[1] != 0):
        raise AssertionError("Registered gain-one control matrix identity failed")

    return {
        "protocol": "RP-F005-A01",
        "model": "x[t+1]=x[t]-k*x[t-d]",
        "arithmetic": "exact Python fractions; no floating-point decision",
        "primary_gain": exact(PRIMARY_GAIN),
        "primary_initial_current": exact(INITIAL_CURRENT),
        "primary_delayed_prehistory": exact(INITIAL_PREVIOUS),
        "evaluated_times": list(range(MAX_STEP + 1)),
        "secondary_gains_are_controls_only": [exact(x) for x in CONTROL_GAINS],
        "records": records,
        "primary_outcome": "x[6]^2/x[0]^2",
        "primary_zero_delay": exact(energy_undelayed),
        "primary_one_step_delay": exact(energy_delayed),
        "primary_difference": exact(difference),
        "registered_threshold": exact(THRESHOLD),
        "decision": "PASS_DELAY_CHANGES_RESPONSE"
        if difference >= THRESHOLD else "NO_REGISTERED_SEPARATION",
        "actual_feedback_delays_are_not_equal": True,
        "scalar_index_is_not_tested": True,
        "lean_scope": "real-valued six-step identity and finite algebra, not general stability theory",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
