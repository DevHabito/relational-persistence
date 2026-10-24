"""Adversarial exact checks for frozen RP-F005-A01."""

import json
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.rp_f005_feedback_delay import (
    CONTROL_GAINS,
    INITIAL_CURRENT,
    MAX_STEP,
    PRIMARY_GAIN,
    THRESHOLD,
    audit,
    direct_trajectory,
    independent_matrix_trajectory,
    multiply,
    power,
    relabelled_delayed_trajectory,
    transition,
    validate,
)


@pytest.mark.parametrize("gain", (PRIMARY_GAIN, *CONTROL_GAINS))
@pytest.mark.parametrize("delay", (0, 1))
def test_all_25_steps_agree_with_independent_matrix_oracle(delay, gain):
    assert direct_trajectory(delay, gain) == independent_matrix_trajectory(delay, gain)
    assert len(direct_trajectory(delay, gain)) == MAX_STEP + 1


def test_primary_delay_contrast_is_exact_and_exceeds_registered_threshold():
    undelayed = direct_trajectory(0, PRIMARY_GAIN)
    delayed = direct_trajectory(1, PRIMARY_GAIN)
    assert undelayed[0] == delayed[0] == 1
    assert undelayed[1:] == (Fraction(0),) * MAX_STEP
    assert delayed[:7] == tuple(map(Fraction, (1, 0, -1, -1, 0, 1, 1)))
    assert delayed[6] ** 2 - undelayed[6] ** 2 == 1
    assert Fraction(1) >= THRESHOLD
    assert delayed[12] == delayed[24] == 1


def test_exact_companion_power_boundaries():
    matrix = transition(1, PRIMARY_GAIN)
    assert power(matrix, 3) == (
        (Fraction(-1), Fraction(0)), (Fraction(0), Fraction(-1))
    )
    assert power(matrix, 6) == (
        (Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))
    )
    assert power(matrix, 12) == power(matrix, 6)


@pytest.mark.parametrize("gain", (PRIMARY_GAIN, *CONTROL_GAINS))
def test_secondary_gains_have_correct_determinant_and_relabeling(gain):
    a = transition(1, gain)
    determinant = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    assert determinant == gain
    assert relabelled_delayed_trajectory(gain) == direct_trajectory(1, gain)


def test_prespecified_contrast_controls_not_substituted_for_primary():
    assert direct_trajectory(0, Fraction(1, 2))[6] == Fraction(1, 64)
    assert direct_trajectory(1, Fraction(1, 2))[6] == 0
    assert direct_trajectory(0, Fraction(3, 2))[6] == Fraction(1, 64)
    assert direct_trajectory(1, Fraction(3, 2))[6] == 1


@pytest.mark.parametrize("invalid", (-1, 2, Fraction(1, 2), 0.5, True))
def test_invalid_delay_rejected(invalid):
    with pytest.raises(ValueError):
        validate(invalid, PRIMARY_GAIN, Fraction(1), Fraction(1))


@pytest.mark.parametrize("invalid", (Fraction(2), Fraction(3, 4), 1, 1.0))
def test_nontarget_gain_rejected(invalid):
    with pytest.raises(ValueError):
        validate(1, invalid, Fraction(1), Fraction(1))


@pytest.mark.parametrize("current,previous", (
    (Fraction(0), Fraction(1)),
    (Fraction(2), Fraction(1)),
    (Fraction(1), Fraction(0)),
    (Fraction(1), Fraction(2)),
))
def test_changed_current_or_prehistory_rejected(current, previous):
    with pytest.raises(ValueError):
        validate(1, PRIMARY_GAIN, current, previous)


@pytest.mark.parametrize("n", (-1, 25, Fraction(6), True))
def test_invalid_matrix_horizon_rejected(n):
    with pytest.raises(ValueError):
        power(transition(1, PRIMARY_GAIN), n)


def test_matrix_corruption_is_detected():
    corrupted = ((Fraction(1), Fraction(-2)), (Fraction(1), Fraction(0)))
    assert multiply(power(corrupted, 6),
                    ((Fraction(1),), (Fraction(1),)))[0][0] != 1
    with pytest.raises(ValueError):
        multiply(((Fraction(1), Fraction(2)),), ((Fraction(1),),))


def test_frozen_result_json_matches_independent_runtime():
    path = Path(__file__).resolve().parents[1] / "docs" / "results" / "RP-F005-A01.json"
    archived = json.loads(path.read_text(encoding="utf-8"))
    assert archived == audit()
    assert archived["decision"] == "PASS_DELAY_CHANGES_RESPONSE"
    assert archived["primary_difference"] == "1/1"
    assert archived["actual_feedback_delays_are_not_equal"]
    assert archived["scalar_index_is_not_tested"]
    assert len(archived["records"]) == 6


def test_no_hidden_empirical_interpretation_in_output_schema():
    report = audit()
    assert report["arithmetic"].startswith("exact")
    assert report["primary_outcome"] == "x[6]^2/x[0]^2"
    assert report["registered_threshold"] == "1/2"
