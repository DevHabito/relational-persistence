"""Synthetic and adversarial *software* checks for frozen RP-E006-P01.

None of these fixtures are RP-E006 measured evidence. Hosted
intervention measurements are created only after main-branch merge.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from experiments.rp_e006_acquire import (
    LOADS, ROLE_FILENAMES, SCHEDULED_LAGS_MS, SPLIT_REPETITIONS,
    acquire, cases_for_split,
)
from experiments.rp_e006_evaluate import (
    evaluate, fit_linear, fit_models, predict, score, validate_split,
)

REPO = Path(__file__).resolve().parents[1]


def synthetic_row(trial: str, n: int, lag: int, response: float) -> dict:
    """A deliberately constructed fixture, not collected data."""
    tau = lag / 1000
    rate = 250.0
    capacity = 83.0
    return {
        "trial_id": trial,
        "work_units": n,
        "scheduled_lag_ms": lag,
        "calibrated_B_work_per_s": capacity,
        "measured_I_work_per_s": rate,
        "measured_tau_s": tau,
        "sampled_recovery_Y_s": response,
        "candidate_C_inverse_s": capacity / (rate * tau),
        "last_pre_end_backlog": n // 5,
        "last_pre_end_observed_ns": 100,
        "injection_end_ns": 101,
        "first_post_end_observed_ns": 102,
    }


def synthetic_train() -> list[dict]:
    return [
        synthetic_row(f"train-{n}-{lag}-{rep}", n, lag,
                      0.001 * n + 0.5 * lag / 1000)
        for rep in (0, 1)
        for n in LOADS
        for lag in SCHEDULED_LAGS_MS
    ]


def synthetic_test() -> list[dict]:
    return [
        synthetic_row(f"test-{n}-{lag}", n, lag, 0.001 * n + 0.5 * lag / 1000)
        for n in LOADS
        for lag in SCHEDULED_LAGS_MS
    ]


def test_registered_design_is_balanced_and_forward_split():
    train = cases_for_split("train")
    test = cases_for_split("test")
    assert len(train) == 18
    assert len(test) == 9
    assert {x["trial_id"] for x in train}.isdisjoint({x["trial_id"] for x in test})
    for n in LOADS:
        for lag in SCHEDULED_LAGS_MS:
            assert sum(x["work_units"] == n and x["lag_ms"] == lag
                       for x in train) == SPLIT_REPETITIONS["train"]
            assert sum(x["work_units"] == n and x["lag_ms"] == lag
                       for x in test) == SPLIT_REPETITIONS["test"]


def test_split_order_is_frozen_independently_of_observations():
    assert cases_for_split("train") == cases_for_split("train")
    assert cases_for_split("test") == cases_for_split("test")
    assert cases_for_split("train") != cases_for_split("test")


def test_no_source_filename_drops_original_sampled_stream():
    assert len(ROLE_FILENAMES) == 8
    assert "monitor-samples.jsonl" in ROLE_FILENAMES
    assert "service-actions.jsonl" in ROLE_FILENAMES
    assert "forecast-snapshot.json" in ROLE_FILENAMES


def test_predictors_fit_only_training_labels():
    train = synthetic_train()
    test = synthetic_test()
    model = fit_models(train)
    first = score(test, model)
    changed = copy.deepcopy(test)
    for row in changed:
        row["sampled_recovery_Y_s"] += 10
    second = score(changed, model)
    assert model == fit_models(train)
    assert first["test_mae_seconds"] != second["test_mae_seconds"]
    assert first["heldout_predictions"][0]["predictions_s"] == (
        second["heldout_predictions"][0]["predictions_s"]
    )


def test_index_ols_uses_reciprocal_C_in_seconds_not_C():
    train = synthetic_train()
    models = fit_models(train)
    expected = predict(models, train[0])["index_only"]
    z = 1 / train[0]["candidate_C_inverse_s"]
    fit = models["index_only"]
    assert fit["feature"] == "reciprocal_C"
    assert expected == max(0, fit["intercept"] + fit["slope"] * z)


def test_positive_predictions_are_clipped_only_after_fitting():
    rows = synthetic_train()
    models = fit_models(rows)
    models["index_only"] = {"feature": "reciprocal_C",
                            "intercept": -100, "slope": 0}
    assert predict(models, rows[0])["index_only"] == 0.0


def test_frozen_primary_gate_can_return_negative():
    train = synthetic_train()
    heldout = synthetic_test()
    scores = score(heldout, fit_models(train))
    assert scores["decision"] == "NO_REGISTERED_PREDICTIVE_GAIN"
    assert len(scores["heldout_predictions"]) == 9
    assert all(math.isfinite(value)
               for value in scores["test_mae_seconds"].values())


def test_registered_primary_gate_can_return_positive_on_synthetic_control():
    train = synthetic_train()
    # Deliberately engineered one-feature prediction. Not observations.
    for row in train:
        row["sampled_recovery_Y_s"] = (
            0.02 + 0.8 / row["candidate_C_inverse_s"]
        )
    test = synthetic_test()
    for row in test:
        row["sampled_recovery_Y_s"] = (
            0.02 + 0.8 / row["candidate_C_inverse_s"]
        )
    scores = score(test, fit_models(train))
    assert scores["decision"] == "PASS_PREDICTIVE_GAIN"
    assert scores["test_mae_seconds"]["index_only"] < 1e-10


def test_insufficient_or_degenerate_training_data_stops():
    with pytest.raises(ValueError, match="18"):
        fit_models(synthetic_train()[:-1])
    const = synthetic_train()
    for row in const:
        row["candidate_C_inverse_s"] = 100
    with pytest.raises(ValueError, match="Degenerate"):
        fit_linear(const, "reciprocal_C")


@pytest.mark.parametrize("feature", ("reciprocal_C", "tau", "N"))
def test_nonfinite_frozen_features_rejected(feature):
    rows = synthetic_train()
    name = {"reciprocal_C": "candidate_C_inverse_s",
            "tau": "measured_tau_s", "N": "work_units"}[feature]
    rows[0][name] = float("nan")
    with pytest.raises(ValueError, match="nonfinite"):
        fit_linear(rows, feature)


@pytest.mark.parametrize("split", ("train", "test"))
def test_missing_original_run_terminates_with_explicit_stop(tmp_path, split):
    outcome = evaluate(tmp_path, REPO, "not-a-real-run", "not-a-real-sha")
    assert outcome["decision"] == "STOP_INSTRUMENTATION"
    assert len(outcome["errors"]) == 2
    assert all(entry["split"] in ("train", "test") for entry in outcome["errors"])


def test_missing_run_identity_cannot_be_accepted(tmp_path):
    with pytest.raises(ValueError, match="GitHub"):
        acquire("train", tmp_path / "new_run")


def test_no_unregistered_split_is_accepted():
    with pytest.raises(ValueError):
        cases_for_split("exploratory")


def test_training_rows_must_not_be_used_as_a_heldout_block():
    with pytest.raises(ValueError, match="nine"):
        score(synthetic_train(), fit_models(synthetic_train()))


def test_unreadable_source_archive_cannot_be_treated_as_negative_evidence(tmp_path):
    with pytest.raises(OSError):
        validate_split(
            tmp_path / "missing-original", "train",
            "run", "sha", "protocol",
        )


def test_unregistered_identity_is_not_silently_accepted(tmp_path):
    archived = tmp_path / "rp-e006-p01-train"
    archived.mkdir()
    (archived / "provenance.json").write_text("{}")
    (archived / "summary.json").write_text("{}")
    with pytest.raises(ValueError, match="metadata mismatch"):
        validate_split(archived, "train", "123", "sha", "protocol")
