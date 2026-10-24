"""Negative and positive adversarial gates for RP-E007 prospective protocol.

All prediction rows here are *synthetic* and are not held-out
observations. No RP-E006 original outcome is used for tuning.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.rp_e007_temporal_backlog import (
    GAP_LIMIT_NS, evaluate, pre_end_pair, predict_from_source, score,
)

END = 1_125_000_000


def sample(t: int, queued: int, *, active: int = 0) -> dict:
    return {
        "observed_ns": t, "server_snapshot_ns": t - 10,
        "queued": queued, "active": active, "completed": 5,
    }


def synthetic_rows(n: int, y: float, *,
                   static: float = 0.1, trend: float = 0.1125) -> list[dict]:
    return [
        {
            "trial_id": f"fixture-{i}",
            "prediction_static_s": static,
            "prediction_trend_s": trend,
            "observed_recovery_s": y,
        }
        for i in range(n)
    ]


def test_two_source_samples_produce_exact_registered_predictions():
    points = [
        sample(1_000_000_000, 10),
        sample(1_100_000_000, 20),
        sample(1_150_000_000, 9999),  # Future Y must never be a feature.
    ]
    computed = predict_from_source(points, END, 100.0)
    assert computed["previous_pre_end_ns"] == 1_000_000_000
    assert computed["latest_pre_end_ns"] == 1_100_000_000
    assert computed["latest_backlog"] == 20
    assert computed["observed_backlog_slope_units_per_second"] == 100.0
    assert computed["latest_sample_age_s"] == 0.025
    assert computed["extrapolated_backlog_at_origin"] == 22.5
    assert computed["prediction_static_s"] == 0.1
    assert computed["prediction_trend_s"] == 0.1125


def test_future_samples_can_never_affect_forecast():
    original = [sample(1_000_000_000, 10),
                sample(1_100_000_000, 20)]
    original_forecast = predict_from_source(original, END, 100)
    after = original + [
        sample(1_125_000_001, 1000000),
        sample(1_130_000_000, 0),
    ]
    assert predict_from_source(after, END, 100) == original_forecast


def test_negative_trend_does_not_force_pass():
    training = synthetic_rows(18, 0.1)
    testing = synthetic_rows(9, 0.1)
    result = score(training, testing)
    assert result["decision"] == "NO_REGISTERED_TREND_GAIN"
    assert result["heldout_mae_s"]["static"] == 0
    assert result["heldout_mae_s"]["two_sample_trend"] > 0


def test_positive_trend_gate_is_reachable_for_synthetic_case():
    training = synthetic_rows(18, 0.1)
    testing = synthetic_rows(9, 0.1125)
    result = score(training, testing)
    assert result["decision"] == "PASS_TREND_INCREMENT"
    assert result["heldout_mae_s"]["two_sample_trend"] == 0
    assert result["heldout_mae_s"]["static"] > 0
    assert result["heldout_mae_s"]["train_constant"] > 0


def test_heldout_labels_do_not_affect_frozen_predictions_or_train_mean():
    training = synthetic_rows(18, 0.1)
    testing = synthetic_rows(9, 0.1125)
    prior = score(training, testing)
    modified = deepcopy(testing)
    for row in modified:
        row["observed_recovery_s"] += 10.0
    rerun = score(training, modified)
    assert prior["train_constant_s"] == rerun["train_constant_s"]
    assert prior["heldout_trial_predictions"][0]["predictions_s"] == (
        rerun["heldout_trial_predictions"][0]["predictions_s"]
    )
    assert prior["heldout_mae_s"] != rerun["heldout_mae_s"]


@pytest.mark.parametrize("value", (0, -1, float("nan"), float("inf")))
def test_bad_capacity_cannot_be_used(value):
    with pytest.raises(ValueError):
        predict_from_source(
            [sample(1_000_000_000, 10), sample(1_100_000_000, 20)],
            END, value,
        )


def test_only_one_preend_sample_is_rejected():
    with pytest.raises(ValueError, match="Fewer than two"):
        pre_end_pair([sample(1_100_000_000, 20),
                      sample(1_150_000_000, 30)], END)


def test_preend_sample_age_over_gate_is_rejected():
    with pytest.raises(ValueError, match="gap/age"):
        pre_end_pair([
            sample(800_000_000, 10), sample(900_000_000, 20),
        ], END)


def test_preend_sample_gap_over_gate_is_rejected():
    with pytest.raises(ValueError, match="gap/age"):
        pre_end_pair([
            sample(900_000_000, 10), sample(1_100_000_000, 20),
        ], END)


def test_duplicate_time_is_rejected():
    with pytest.raises(ValueError, match="ordering"):
        pre_end_pair([
            sample(1_100_000_000, 10), sample(1_100_000_000, 20),
        ], END)


def test_future_data_only_cannot_be_used():
    with pytest.raises(ValueError, match="Fewer than two"):
        pre_end_pair([
            sample(1_125_000_001, 10), sample(1_126_000_000, 20),
        ], END)


@pytest.mark.parametrize("field,invalid", [
    ("queued", -1),
    ("active", True),
    ("completed", 3.5),
    ("server_snapshot_ns", -1),
])
def test_invalid_raw_sample_fields_stop(field, invalid):
    inputs = [
        sample(1_000_000_000, 10), sample(1_100_000_000, 20),
    ]
    inputs[1][field] = invalid
    with pytest.raises(ValueError):
        pre_end_pair(inputs, END)


def test_post_timestamp_cannot_precede_service_snapshot():
    inputs = [
        sample(1_000_000_000, 10), sample(1_100_000_000, 20),
    ]
    inputs[1]["server_snapshot_ns"] = 1_100_000_001
    with pytest.raises(ValueError):
        pre_end_pair(inputs, END)


def test_negative_queue_slope_clips_extrapolated_backlog_to_zero():
    inputs = [
        sample(1_000_000_000, 20), sample(1_100_000_000, 1),
    ]
    computed = predict_from_source(inputs, END, 100)
    assert computed["extrapolated_backlog_at_origin"] == 0
    assert computed["prediction_trend_s"] == 0


def test_missing_original_new_experiment_cannot_be_claimed_a_pass(tmp_path):
    project = __import__("pathlib").Path(__file__).resolve().parents[1]
    outcome = evaluate(tmp_path, project, "original-run", "source-sha")
    assert outcome["decision"] == "STOP_INSTRUMENTATION"
    assert len(outcome["errors"]) == 2
    assert outcome["original_training_trials_audited"] == 0
    assert outcome["original_heldout_trials_audited"] == 0
    assert outcome["physical_law_test"] == "NOT_PERFORMED"


def test_frozen_horizon_and_cutoff_are_unmodified():
    assert GAP_LIMIT_NS == 150_000_000
    assert len(synthetic_rows(18, 0.1)) == 18
    with pytest.raises(ValueError, match="18"):
        score(synthetic_rows(17, 0.1), synthetic_rows(9, 0.1))
    with pytest.raises(ValueError, match="9"):
        score(synthetic_rows(18, 0.1), synthetic_rows(8, 0.1))
