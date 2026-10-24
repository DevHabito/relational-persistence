"""RP-F004-A01: exact two-state correlated-noise stress test.

This model is entirely specified mathematics, not observational data.
See docs/preregistration/RP-F004-A01.md (committed before this code).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json

GAIN = Fraction(1, 2)
AMPLITUDE = Fraction(1, 10)
NOISE_VARIANCE = AMPLITUDE ** 2
HORIZON = 12
SECOND_HORIZON = 40
REGISTERED_PROBABILITIES = (Fraction(1, 2), Fraction(3, 4))
THRESHOLD = Fraction(1, 200)


@dataclass(frozen=True)
class Moments:
    variance: Fraction
    cross_covariance: Fraction


def validate_model(
    probability_stay: Fraction,
    *,
    positive_noise: Fraction = AMPLITUDE,
    negative_noise: Fraction = -AMPLITUDE,
    first_sign_probability: Fraction = Fraction(1, 2),
    probability_flip: Fraction | None = None,
) -> None:
    """Reject deviations from the preregistered noise distribution."""
    if not isinstance(probability_stay, Fraction):
        raise TypeError("Use exact Fraction for stay probability")
    if not Fraction(0) <= probability_stay <= Fraction(1):
        raise ValueError("Invalid Markov transition probability")
    if probability_stay not in REGISTERED_PROBABILITIES:
        raise ValueError("Noise transition is outside the frozen protocol")
    if (
        positive_noise != AMPLITUDE
        or negative_noise != -AMPLITUDE
        or first_sign_probability != Fraction(1, 2)
    ):
        raise ValueError("The symmetric noise marginal has been changed")
    if probability_flip is not None and probability_stay + probability_flip != 1:
        raise ValueError("Markov transition row does not sum to one")


def moment_step(moment: Moments, probability_stay: Fraction) -> Moments:
    """Propagate second moments for the specified joint Markov process.

    E[eta_next | eta] = (2p-1)*eta, eta^2 = 1/100.
    """
    validate_model(probability_stay)
    correlation = 2 * probability_stay - 1
    return Moments(
        variance=GAIN**2 * moment.variance
        + 2 * GAIN * moment.cross_covariance
        + NOISE_VARIANCE,
        cross_covariance=correlation * (
            GAIN * moment.cross_covariance + NOISE_VARIANCE
        ),
    )


def moment_at(probability_stay: Fraction, step: int) -> Moments:
    validate_model(probability_stay)
    if not isinstance(step, int) or not 0 <= step <= SECOND_HORIZON:
        raise ValueError("Only bounded preregistered moment horizons are supported")
    moment = Moments(Fraction(0), Fraction(0))
    for _ in range(step):
        moment = moment_step(moment, probability_stay)
    return moment


def stationary_moments(probability_stay: Fraction) -> Moments:
    """Solve the two exact fixed-point equations, without simulation."""
    validate_model(probability_stay)
    correlation = 2 * probability_stay - 1
    cross = correlation * NOISE_VARIANCE / (1 - correlation * GAIN)
    variance = (NOISE_VARIANCE + 2 * GAIN * cross) / (1 - GAIN**2)
    moment = Moments(variance, cross)
    if moment_step(moment, probability_stay) != moment:
        raise AssertionError("Stationary equations were not satisfied")
    return moment


def exact_path_variance(probability_stay: Fraction, horizon: int = HORIZON) -> tuple[Fraction, Fraction, int]:
    """Enumerate every sign history directly, independently of moment_step."""
    validate_model(probability_stay)
    if horizon != HORIZON:
        raise ValueError("The independent enumeration horizon is frozen at 12")
    total_weight = Fraction(0)
    second_moment = Fraction(0)
    paths = 0
    for signs in product((-1, 1), repeat=horizon):
        weight = Fraction(1, 2)
        for previous, current in zip(signs, signs[1:]):
            weight *= probability_stay if previous == current else 1 - probability_stay
        x = Fraction(0)
        for sign in signs:
            x = GAIN * x + sign * AMPLITUDE
        second_moment += weight * x * x
        total_weight += weight
        paths += 1
    return second_moment, total_weight, paths


def encode_fraction(number: Fraction) -> str:
    return f"{number.numerator}/{number.denominator}"


def evaluate() -> dict:
    cases = []
    for probability in REGISTERED_PROBABILITIES:
        stationary = stationary_moments(probability)
        first = moment_at(probability, HORIZON)
        second = moment_at(probability, SECOND_HORIZON)
        direct, weight, paths = exact_path_variance(probability)
        if (direct, weight, paths) != (first.variance, Fraction(1), 2**HORIZON):
            raise AssertionError("Full-path oracle disagrees with second-moment recursion")
        cases.append(
            {
                "stay_probability": encode_fraction(probability),
                "lag_one_correlation": encode_fraction(2 * probability - 1),
                "noise_mean": "0/1",
                "noise_variance": encode_fraction(NOISE_VARIANCE),
                "paths_enumerated": paths,
                "path_total_weight": encode_fraction(weight),
                "variance_at_12": encode_fraction(first.variance),
                "path_oracle_variance_at_12": encode_fraction(direct),
                "cross_covariance_at_12": encode_fraction(first.cross_covariance),
                "variance_at_40": encode_fraction(second.variance),
                "stationary_variance": encode_fraction(stationary.variance),
                "stationary_cross_covariance": encode_fraction(stationary.cross_covariance),
                "stationary_variance_approximation": float(stationary.variance),
            }
        )
    white, persistent = (
        stationary_moments(probability).variance
        for probability in REGISTERED_PROBABILITIES
    )
    if white != NOISE_VARIANCE / (1 - GAIN**2):
        raise AssertionError("Incorrect independent-noise control")
    separation = persistent - white
    decision = (
        "PASS_CORRELATION_MATTERS"
        if separation >= THRESHOLD
        else "NO_REGISTERED_SEPARATION"
    )
    return {
        "protocol": "RP-F004-A01",
        "model": "x[t+1]=x[t]/2+eta[t]",
        "dimensionless": True,
        "initial_state": "0/1",
        "scalar_inputs": {"B": "1/1", "I": "1/100", "tau": "1/1", "C": "100/1"},
        "noise_distribution": {"+1/10": "1/2", "-1/10": "1/2"},
        "primary_output": "stationary state variance",
        "cases": cases,
        "stationary_variance_difference": encode_fraction(separation),
        "stationary_variance_difference_approximation": float(separation),
        "registered_threshold": encode_fraction(THRESHOLD),
        "decision": decision,
        "source_kind": "exact mathematical Markov model; no observed trajectories",
        "lean_scope": "rational moment fixed points and uniqueness only",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, ensure_ascii=True))
