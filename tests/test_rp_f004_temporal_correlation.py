"""Independent and adversarial checks for frozen RP-F004-A01."""

from fractions import Fraction

import pytest

from experiments.rp_f004_temporal_correlation import (
    AMPLITUDE,
    GAIN,
    HORIZON,
    NOISE_VARIANCE,
    SECOND_HORIZON,
    THRESHOLD,
    Moments,
    evaluate,
    exact_path_variance,
    moment_at,
    moment_step,
    stationary_moments,
    validate_model,
)


@pytest.mark.parametrize("probability", [Fraction(1, 2), Fraction(3, 4)])
def test_full_path_oracle_matches_recursion_exactly(probability):
    variance, total_weight, count = exact_path_variance(probability)
    assert count == 4096
    assert total_weight == 1
    assert variance == moment_at(probability, HORIZON).variance


def test_registered_stationary_values_and_separation():
    white = stationary_moments(Fraction(1, 2))
    persistent = stationary_moments(Fraction(3, 4))
    assert white == Moments(Fraction(1, 75), Fraction(0))
    assert persistent == Moments(Fraction(1, 45), Fraction(1, 150))
    assert persistent.variance - white.variance == Fraction(2, 225)
    assert persistent.variance - white.variance >= THRESHOLD
    assert white.variance == NOISE_VARIANCE / (1 - GAIN**2)


@pytest.mark.parametrize("probability", [Fraction(1, 2), Fraction(3, 4)])
def test_stationary_fixed_point_is_exact(probability):
    fixed = stationary_moments(probability)
    assert moment_step(fixed, probability) == fixed
    changed = Moments(fixed.variance + Fraction(1, 10_000), fixed.cross_covariance)
    assert moment_step(changed, probability) != changed


@pytest.mark.parametrize(
    "probability,expected",
    [
        (Fraction(1, 2), Fraction(1118481, 83886080)),
        (Fraction(3, 4), Fraction(9320667, 419430400)),
    ],
)
def test_explicit_twelve_step_independent_expected(probability, expected):
    assert exact_path_variance(probability)[0] == expected


@pytest.mark.parametrize(
    "probability,expected",
    [
        (Fraction(1, 2), Fraction(16119010928195055662749, 1208925819614629174706176)),
        (Fraction(3, 4), Fraction(134325091068292130522903, 6044629098073145873530880)),
    ],
)
def test_exact_forty_step_moment_trace(probability, expected):
    assert moment_at(probability, SECOND_HORIZON).variance == expected


def test_same_fixed_noise_marginal_for_both_processes():
    assert (AMPLITUDE + (-AMPLITUDE)) / 2 == 0
    assert (AMPLITUDE**2 + (-AMPLITUDE)**2) / 2 == NOISE_VARIANCE
    assert NOISE_VARIANCE == Fraction(1, 100)


@pytest.mark.parametrize("invalid", [Fraction(-1, 4), Fraction(5, 4), Fraction(2, 3)])
def test_nonregistered_or_invalid_stay_probability_is_rejected(invalid):
    with pytest.raises(ValueError):
        validate_model(invalid)


def test_float_probability_does_not_sneak_into_exact_protocol():
    with pytest.raises(TypeError):
        validate_model(0.5)


@pytest.mark.parametrize(
    "override",
    [
        {"positive_noise": Fraction(2, 10)},
        {"negative_noise": Fraction(-2, 10)},
        {"first_sign_probability": Fraction(2, 3)},
        {"probability_flip": Fraction(1, 10)},
    ],
)
def test_distribution_and_transition_mutations_rejected(override):
    with pytest.raises(ValueError):
        validate_model(Fraction(3, 4), **override)


@pytest.mark.parametrize("invalid_horizon", [11, 13, 0])
def test_enumerator_horizon_cannot_be_changed(invalid_horizon):
    with pytest.raises(ValueError):
        exact_path_variance(Fraction(1, 2), invalid_horizon)


@pytest.mark.parametrize("invalid_horizon", [-1, SECOND_HORIZON + 1, 1.5])
def test_moment_horizon_is_bounded(invalid_horizon):
    with pytest.raises(ValueError):
        moment_at(Fraction(1, 2), invalid_horizon)


def test_frozen_output_and_nonempirical_scope():
    record = evaluate()
    assert record["decision"] == "PASS_CORRELATION_MATTERS"
    assert record["stationary_variance_difference"] == "2/225"
    assert record["scalar_inputs"]["C"] == "100/1"
    assert record["source_kind"].startswith("exact mathematical")
    assert record["cases"][0]["noise_variance"] == record["cases"][1]["noise_variance"]


def test_calibration_is_not_an_observed_noise_measure():
    """The protocol fixes a dimensionless proxy; no data-driven fit occurs."""
    assert NOISE_VARIANCE == Fraction(1, 100)
    assert stationary_moments(Fraction(3, 4)).variance != NOISE_VARIANCE


def test_committed_record_matches_recomputed_exact_output():
    """Archived fractions are not hand-updated or independently refitted."""
    import json
    from pathlib import Path

    archived_path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "results" / "RP-F004-A01.json"
    )
    record = json.loads(archived_path.read_text(encoding="utf-8"))
    assert record == evaluate()
