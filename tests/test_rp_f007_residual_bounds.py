"""Adversarial exact-rational checks for frozen RP-F007-A01.

Every row is SYNTHETIC. No E010/E011 heldout data, fitted coefficients,
empirical scheduler claims or hidden actual completion in public inputs.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json

import pytest

from experiments import rp_f007_residual_bounds as bounds


def test_registered_public_caps_age_and_full_population():
    assert bounds.CAP_BROAD == 500
    assert bounds.CAP_NARROW == 90
    assert bounds.RUNNING_AGE == 30
    assert bounds.CAP_BROAD - bounds.RUNNING_AGE == 470
    assert bounds.CAP_NARROW - bounds.RUNNING_AGE == 60


@pytest.mark.parametrize("cap,remaining", [
    (500, 1), (500, 60), (500, 100), (500, 470),
    (90, 1), (90, 30), (90, 60),
])
def test_registered_extreme_and_interior_fcfs_validity(cap, remaining):
    world = bounds.make_world(cap, remaining)
    evidence = bounds.checked_world(world, cap)
    assert evidence["actual_future_remaining_s"] == remaining
    assert evidence["running_runtime_s"] == 30 + remaining
    assert evidence["target_wait_s"] == remaining
    assert evidence["independent_dispatch_replayed"] is True
    assert evidence["three_queue_state_oracles_agreed"] is True
    assert bounds.public_observation(world, enforced=True)[
        "running_walltime_limit_is_enforced"
    ] is True


@pytest.mark.parametrize("cap,max_remaining", [(500, 470), (90, 60)])
def test_all_future_outcomes_have_same_public_pre_origin_inputs(cap, max_remaining):
    left = bounds.public_observation(bounds.make_world(cap, 1), enforced=True)
    right = bounds.public_observation(
        bounds.make_world(cap, max_remaining), enforced=True
    )
    middle = bounds.public_observation(
        bounds.make_world(cap, max_remaining // 2), enforced=True
    )
    assert left == middle == right
    assert left["q_minus_120"] == left["q_minus_60"] == left["q_pre_target"] == 0
    assert left["running_job_age_s"] == "30"
    assert left["all_public_requests"][1][1] == str(cap)
    assert "running_job_actual_end" not in left
    assert "future_remaining" not in left
    assert "target_wait" not in left


def test_broad_and_narrow_observations_are_not_falsely_called_equal():
    broad = bounds.public_observation(bounds.make_world(500, 1), enforced=True)
    narrow = bounds.public_observation(bounds.make_world(90, 1), enforced=True)
    assert broad != narrow
    assert broad["all_public_requests"][1][1] == "500"
    assert narrow["all_public_requests"][1][1] == "90"
    assert [record for record in broad["all_pre_origin_events"]] == (
        narrow["all_pre_origin_events"]
    )


def test_the_registered_broad_family_is_complete_not_only_two_endpoints():
    family = bounds.exhaustive_family(500)
    assert family["admissible_world_count"] == 470
    assert family["admissible_wait_min_seconds"] == 1
    assert family["admissible_wait_max_seconds"] == 470
    assert family["minimax_midpoint_prediction_s"] == "471/2"
    assert family["sharp_minimax_worst_case_error_s"] == "469/2"
    assert family["independent_analytic_error_bound_s"] == "469/2"
    assert family["zero_prediction_worst_case_error_s"] == "470"
    assert family["public_observations_identical_in_family"] is True


def test_registered_narrow_family_is_complete_not_only_endpoints():
    family = bounds.exhaustive_family(90)
    assert family["admissible_world_count"] == 60
    assert family["admissible_wait_min_seconds"] == 1
    assert family["admissible_wait_max_seconds"] == 60
    assert family["minimax_midpoint_prediction_s"] == "61/2"
    assert family["sharp_minimax_worst_case_error_s"] == "59/2"
    assert family["independent_analytic_error_bound_s"] == "59/2"
    assert family["zero_prediction_worst_case_error_s"] == "60"


@pytest.mark.parametrize("cap,high", [(500, 470), (90, 60)])
def test_independent_endpoint_calculation_matches_all_integer_worlds(cap, high):
    analytical = bounds.analytic_minimax(1, high)
    midpoint = bounds.exact_midpoint(1, high)
    errors = [abs(midpoint - Fraction(r)) for r in range(1, high + 1)]
    assert analytical == max(errors)
    assert errors[0] == errors[-1] == analytical
    assert max(errors) >= min(errors)
    assert cap == high + 30


def test_tightening_guaranteed_cap_changes_mathematical_minimax_not_field_mae():
    source = bounds.audit()
    assert source["decision"] == "BOUNDED_STATE_MINIMAX_VERIFIED"
    assert source["minimax_error_decrease_s"] == "205"
    assert source["narrow_over_broad_minimax_error_ratio"] == "59/469"
    assert source["public_cap_change_means_public_observation_changes"] is True
    assert source["no_external_prediction_data_used"] is True
    assert source["physical_law_or_scalar_C_claimed"] is False


def test_unsafe_advertised_only_walltime_overrun_is_not_a_hard_bound():
    extended = bounds.make_world(500, 471)
    assert extended.named("R").service == 501
    with pytest.raises(bounds.WitnessInvalid, match="Hard cap violated"):
        bounds.checked_world(extended, 500, enforced=True)
    report = bounds.checked_world(extended, 500, enforced=False)
    assert report["target_wait_s"] == 471
    assert (bounds.public_observation(extended, enforced=False)[
        "running_walltime_limit_is_enforced"
    ]) is False


@pytest.mark.parametrize("wrong_cap", [0, 89, 91, 499, 501])
def test_cap_not_in_frozen_study_fails_closed(wrong_cap):
    with pytest.raises(bounds.WitnessInvalid, match="two registered"):
        bounds.exhaustive_family(wrong_cap)


@pytest.mark.parametrize("cap,remaining", [(500, 0), (90, 0), (500, -1)])
def test_zero_and_negative_residual_job_not_declared_active(cap, remaining):
    with pytest.raises(bounds.WitnessInvalid):
        bounds.checked_world(bounds.make_world(cap, remaining), cap)


def test_hidden_arrival_and_changed_dispatch_must_fail():
    frozen = bounds.make_world(500, 1)
    forged = replace(frozen, jobs=frozen.jobs[:-1])
    with pytest.raises(bounds.WitnessInvalid, match="hidden arrival"):
        bounds.checked_world(forged, 500)
    changed = replace(frozen, jobs=(
        frozen.named("H"),
        replace(frozen.named("R"), start=Fraction(-29)),
        frozen.named("T"),
    ))
    with pytest.raises(bounds.WitnessInvalid):
        bounds.checked_world(changed, 500)


def test_hard_cap_does_not_allow_changed_running_age():
    frozen = bounds.make_world(500, 100)
    tampered = replace(frozen, jobs=(
        frozen.named("H"),
        replace(frozen.named("R"), start=Fraction(-20)),
        frozen.named("T"),
    ))
    with pytest.raises(bounds.WitnessInvalid, match="age/cap"):
        bounds.checked_world(tampered, 500)


def test_zero_forecast_has_exact_worst_case_for_each_cap():
    for cap in (500, 90):
        allowed = list(range(1, cap - 30 + 1))
        assert max(abs(Fraction(0) - Fraction(r)) for r in allowed) == cap - 30


def test_no_fitted_parameter_or_probability_assumption_enters_minimax_bound():
    result = bounds.audit()
    assert result["source"] == "SYNTHETIC_ONLY"
    assert result["novel_queuing_theorem_claimed"] is False
    assert result["no_original_rp_e010_or_rp_e011_result_changed"] is True
    assert all(result["registered_controls"].values())
    assert result["broad_family"]["public_observation"] != (
        result["narrow_family"]["public_observation"]
    )
    # The JSON is natively serializable and does not accidentally inject
    # tuples converted to lists or future predictions into public input.
    assert json.loads(json.dumps(result)) == result


def test_illicit_future_completion_oracle_is_not_a_causal_feature():
    near = bounds.make_world(500, 1)
    far = bounds.make_world(500, 470)
    assert bounds.public_observation(near, enforced=True) == (
        bounds.public_observation(far, enforced=True)
    )
    assert near.named("R").end != far.named("R").end
    assert near.named("R").end == near.named("T").wait
    assert far.named("R").end == far.named("T").wait


def test_full_report_can_not_be_overwritten_by_cli(tmp_path, monkeypatch):
    import sys
    target = tmp_path / "original.json"
    monkeypatch.setattr(sys, "argv", [
        "rp_f007_residual_bounds.py", "--output", str(target)
    ])
    bounds.main()
    prior = target.read_bytes()
    with pytest.raises(SystemExit, match="overwrite"):
        bounds.main()
    assert target.read_bytes() == prior
