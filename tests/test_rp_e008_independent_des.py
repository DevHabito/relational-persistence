"""RP-E008 exact-code regressions, adversarial audits and synthetic decisions.

These assertions are unit tests of a constructed model, NEVER independent
field observations. Preregistered outcome is not asserted as PASS.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction

import pytest

from experiments.rp_e008_independent_des import (
    DWELL_MS, HELDOUT_REPETITIONS, ORIGIN_MS,
    PREVIOUS_SAMPLE_MS, LATEST_SAMPLE_MS, SAMPLE_STEP_MS,
    TRAIN_REPETITIONS, completion_recursion, design, duration_sources,
    event_calendar, evaluate_case, fraction_text, mean_fraction, predict,
    sampled_recovery, source_for, summarize, source_digest,
)


def test_registered_design_contains_all_72_unsubstituted_cases():
    cases = design()
    assert len(cases) == len({c["trial_id"] for c in cases}) == 72
    assert sum(c["split"] == "train" for c in cases) == 36
    assert sum(c["split"] == "heldout" for c in cases) == 36
    assert TRAIN_REPETITIONS == (0, 1, 2, 3)
    assert HELDOUT_REPETITIONS == (4, 5, 6, 7)


@pytest.mark.parametrize("spec", (design()[0], design()[30], design()[-1]))
def test_independent_fcfs_recursion_and_event_calendar_match_exactly(spec):
    source = source_for(spec)
    first_finish, first_status = completion_recursion(source)
    other_finish, other_status, trace = event_calendar(source)
    assert first_finish == other_finish
    assert first_status == other_status
    assert len(trace) == 2 * len(source["arrival_ms"])
    assert len(first_finish) == len(source["arrival_ms"])
    assert sampled_recovery(first_status) == sampled_recovery(other_status)
    assert all(row["backlog"] >= 0 for row in first_status)


def test_all_samples_and_service_inputs_remain_integral():
    spec = design()[0]
    source = source_for(spec)
    assert all(isinstance(v, int) and 0 <= v < ORIGIN_MS
               for v in source["arrival_ms"])
    assert all(d > 0 for d in source["postchange_service_ms"])
    assert len(source["prechange_calibration_ms"]) == 120
    assert sum(source["prechange_calibration_ms"]) == 120 * 18
    _, status = completion_recursion(source)
    assert all(row["time_ms"] % SAMPLE_STEP_MS == 0 for row in status)


def test_preend_features_cannot_read_any_future_status():
    source = source_for(design()[3])
    _, statuses = completion_recursion(source)
    original = predict(statuses, source["prechange_calibration_ms"])
    edited = deepcopy(statuses)
    for row in edited:
        if row["time_ms"] > ORIGIN_MS:
            row["backlog"] += 1000000
    assert predict(edited, source["prechange_calibration_ms"]) == original
    assert original["sample_prev_ms"] == PREVIOUS_SAMPLE_MS
    assert original["sample_last_ms"] == LATEST_SAMPLE_MS
    assert original["forecast_origin_ms"] == ORIGIN_MS


def test_manual_nonzero_two_sample_slope_is_exact_rational():
    samples = [
        {"time_ms": PREVIOUS_SAMPLE_MS, "backlog": 10},
        {"time_ms": LATEST_SAMPLE_MS, "backlog": 14},
    ]
    formula = predict(samples, [18] * 120)
    assert formula["prediction_static_seconds"] == "63/500"
    assert formula["predicted_backlog_at_origin"] == "16/1"
    assert formula["prediction_trend_seconds"] == "18/125"


def test_manual_negative_trend_is_clipped_to_zero():
    samples = [
        {"time_ms": PREVIOUS_SAMPLE_MS, "backlog": 10},
        {"time_ms": LATEST_SAMPLE_MS, "backlog": 2},
    ]
    result = predict(samples, [18] * 120)
    assert result["predicted_backlog_at_origin"] == "0/1"
    assert result["prediction_trend_seconds"] == "0/1"


def test_simultaneous_arrivals_remain_fcfs_even_under_service_variability():
    source = {
        "arrival_ms": [0, 0, 0, 4],
        "postchange_service_ms": [3, 9, 6, 4],
    }
    first_finish, first_samples = completion_recursion(source)
    second_finish, second_samples, trace = event_calendar(source)
    assert first_finish == second_finish == [3, 12, 18, 22]
    assert first_samples == second_samples
    assert len(trace) == 8
    assert [e["job"] for e in trace if e["kind"] == "completion"] == [0, 1, 2, 3]


def test_software_idle_periods_are_handled_not_padded_with_fake_work():
    source = {
        "arrival_ms": [0, 100, 400],
        "postchange_service_ms": [3, 9, 6],
    }
    a_finish, a_samples = completion_recursion(source)
    b_finish, b_samples, _ = event_calendar(source)
    assert a_finish == b_finish == [3, 109, 406]
    assert a_samples == b_samples
    assert a_samples[1]["backlog"] == 0


@pytest.mark.parametrize("invalid", [
    {"arrival_ms": [0, 1000], "postchange_service_ms": [5, 5]},
    {"arrival_ms": [-1], "postchange_service_ms": [5]},
    {"arrival_ms": [0], "postchange_service_ms": [0]},
    {"arrival_ms": [0, 1], "postchange_service_ms": [5]},
])
def test_invalid_job_inputs_stop_instead_of_producing_claims(invalid):
    with pytest.raises(ValueError):
        completion_recursion(invalid)


def test_missing_recovery_confirmation_is_not_interpreted_as_success():
    insufficient = [
        {"time_ms": ORIGIN_MS + i * SAMPLE_STEP_MS, "backlog": 0}
        for i in range(1, 5)
    ]
    with pytest.raises(ValueError, match="confirmation"):
        sampled_recovery(insufficient)


def test_missing_or_corrupted_calibration_does_not_pass():
    _, statuses = completion_recursion(source_for(design()[0]))
    with pytest.raises(ValueError):
        predict(statuses, [18] * 119)
    with pytest.raises(ValueError):
        predict(statuses, [12] * 120)


def test_exact_fraction_serialization_and_source_digest_are_reproducible():
    assert fraction_text(Fraction(2, 6)) == "1/3"
    one = source_for(design()[0])
    assert source_digest(one) == source_digest(source_for(design()[0]))
    mutated = deepcopy(one)
    mutated["arrival_ms"][0] = 33
    assert source_digest(mutated) != source_digest(one)


def synthetic_case(idx: int, split: str, static: Fraction,
                   trend: Fraction) -> dict:
    return {
        "trial_id": design()[idx]["trial_id"],
        "split": split,
        "arrival_profile": design()[idx]["arrival_profile"],
        "service_variant": design()[idx]["service_variant"],
        "absolute_errors_seconds": {
            "static": fraction_text(static),
            "trend": fraction_text(trend),
        },
    }


def synthetic_grid(static: Fraction, trend: Fraction) -> list[dict]:
    return [
        synthetic_case(k, spec["split"], static, trend)
        for k, spec in enumerate(design())
    ]


def test_synthetic_primary_gate_accepts_both_success_and_failure():
    good = summarize(synthetic_grid(Fraction(1, 10), Fraction(1, 20)))
    assert good["decision"] == "PASS_SIMULATED_TRANSFER"
    assert good["heldout_trials"] == 36
    bad = summarize(synthetic_grid(Fraction(1, 10), Fraction(1, 10)))
    assert bad["decision"] == "NO_REGISTERED_SIMULATED_TRANSFER"
    zero = summarize(synthetic_grid(Fraction(0), Fraction(0)))
    assert zero["decision"] == "NO_REGISTERED_SIMULATED_TRANSFER"


def test_missing_sample_or_case_causes_stop_not_a_selected_subset():
    with pytest.raises(ValueError):
        summarize(synthetic_grid(Fraction(1, 10), Fraction(1, 20))[:-1])


def test_exact_recovery_is_not_substituted_for_sampled_recovery():
    case = evaluate_case(source_for(design()[0]))
    true_ms = case["true_drain_after_origin_ms"]
    sampled_ms = case["first_sampled_idle_after_origin_ms"]
    assert 0 <= sampled_ms - true_ms < SAMPLE_STEP_MS
    assert DWELL_MS == 500
    assert case["observed_recovery_seconds"] == fraction_text(Fraction(sampled_ms, 1000))


def test_exact_rational_average_no_float_decision():
    assert mean_fraction([Fraction(1, 3), Fraction(2, 3)]) == Fraction(1, 2)
