"""RP-E009 preregistered design, adverse controls, and a disposable TCP smoke.

Smoke bytes are *not* the registered hosted first-run dataset, and may
never be substituted for failed first-run scientific observations.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path
import json

import pytest

from experiments.rp_e009_acquire import (
    ORIGINAL_FILES, digest, planned_spacing_ms, registered_trials,
    trial, acquire,
)
from experiments.rp_e009_evaluate import (
    replay_trial, score, check_events, check_monitor,
)
from experiments.rp_e009_tcp_service import MeasuredQueue


def synthetic_row(ident: str, target: float, baseline: float,
                  trend: float, mode="uniform") -> dict:
    return {
        "trial_id": ident,
        "sampled_recovery_s": target,
        "prediction_static_s": baseline,
        "prediction_trend_s": trend,
        "arrival_mode": mode,
    }


def test_registered_cells_and_sequential_split_are_frozen():
    a = registered_trials("diagnostic")
    b = registered_trials("holdout")
    assert len(a) == len(b) == 9
    assert len({r["trial_id"] for r in a + b}) == 18
    assert {r["arrival_mode"] for r in a} == {
        "uniform", "early_burst", "late_burst"
    }
    assert {r["work_units"] for r in b} == {40, 70, 100}
    assert a == registered_trials("diagnostic")
    assert b == registered_trials("holdout")
    assert set(ORIGINAL_FILES) == {
        "calibration.json", "controller.json", "injector.json",
        "monitor-samples.jsonl", "service-events.jsonl",
        "feature-snapshot.json", "configuration.json",
    }


@pytest.mark.parametrize("mode,first,second", [
    ("uniform", 3, 3), ("early_burst", 1, 5), ("late_burst", 5, 1),
])
def test_nominal_arrival_patterns_are_not_actual_measurement_inputs(
    mode, first, second
):
    assert planned_spacing_ms(mode, 0, 40) == first
    assert planned_spacing_ms(mode, 25, 40) == second


def test_synthetic_good_heldout_presses_positive_gate():
    diagnostics = [synthetic_row(str(i), .10, .20, .15) for i in range(9)]
    holdout = [
        synthetic_row(str(i), .10, .20, .105, ("uniform", "early_burst",
                                              "late_burst")[i % 3])
        for i in range(9)
    ]
    outcome = score(diagnostics, holdout)
    assert outcome["decision"] == "PASS_EXECUTABLE_TRANSFER"
    assert outcome["trend_wins"] == 9
    assert outcome["registered_threshold"] == .90


def test_synthetic_negative_gate_remains_possible():
    diagnostics = [synthetic_row(str(i), .10, .20, .15) for i in range(9)]
    heldout = [
        synthetic_row(str(i), .10, .20, .30, ("uniform", "early_burst",
                                              "late_burst")[i % 3])
        for i in range(9)
    ]
    outcome = score(diagnostics, heldout)
    assert outcome["decision"] == "NO_REGISTERED_EXECUTABLE_GAIN"
    assert outcome["trend_wins"] == 0


def test_zero_error_static_forbids_claimed_positive_gain():
    rows = [
        synthetic_row(str(i), .10, .10, .10,
                      ("uniform", "early_burst", "late_burst")[i % 3])
        for i in range(9)
    ]
    assert score(rows, rows)["decision"] == "NO_REGISTERED_EXECUTABLE_GAIN"


def test_heldout_labels_cannot_change_frozen_predictions():
    train = [synthetic_row(str(i), .05, .05, .05) for i in range(9)]
    test = [synthetic_row(str(i), .1, .12, .10) for i in range(9)]
    initial = score(train, test)
    modified = deepcopy(test)
    for item in modified:
        item["sampled_recovery_s"] += 10
    changed = score(train, modified)
    assert initial["heldout_cases"][0]["predictions_s"] == (
        changed["heldout_cases"][0]["predictions_s"]
    )
    assert initial["mae_seconds"] != changed["mae_seconds"]
    assert initial["diagnostic_only_mean_s"] == changed["diagnostic_only_mean_s"]


def test_unregistered_or_partial_scenarios_stop():
    with pytest.raises(ValueError):
        registered_trials("new-seed")
    with pytest.raises(ValueError):
        planned_spacing_ms("surprise", 0, 40)
    with pytest.raises(ValueError):
        score([synthetic_row(str(i), .1, .2, .1) for i in range(8)],
              [synthetic_row(str(i), .1, .2, .1) for i in range(9)])


def test_missing_github_identity_cannot_be_assumed(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.delenv("GITHUB_RUN_ID", raising=False)
    with pytest.raises(ValueError, match="source commit"):
        acquire("diagnostic", tmp_path / "first-run")


def test_service_double_control_and_nonidle_reset_are_rejected(tmp_path):
    async def check():
        state = MeasuredQueue(tmp_path / "scratch-event.jsonl")
        response = await state.respond({"op": "enqueue"})
        assert response["accepted"] is True
        with pytest.raises(ValueError, match="nonidle"):
            await state.respond({"op": "reset"})
    asyncio.run(check())


def test_disposable_fresh_executable_and_source_byte_audit(tmp_path):
    """An end-to-end process smoke on localhost, not original new evidence."""
    spec = {
        "trial_id": "smoke-040-uniform",
        "work_units": 40,
        "arrival_mode": "uniform",
    }
    location = tmp_path / "disposable" / spec["trial_id"]
    result = asyncio.run(trial(location, spec))
    hashes = {name: digest(location / name) for name in ORIGINAL_FILES}
    reported = {**result, "file_sha256": hashes}
    outcome = replay_trial(location, spec, reported)
    assert outcome["trial_id"] == spec["trial_id"]
    assert outcome["sampled_recovery_s"] >= 0
    assert outcome["prediction_static_s"] >= 0
    assert outcome["prediction_trend_s"] >= 0
    assert outcome["previous_pre_end_ns"] < outcome["latest_pre_end_ns"]
    assert outcome["latest_pre_end_ns"] <= outcome["injector_end_ns"]

    # Adversarial byte mutation must invalidate stored source hash.
    source = location / "monitor-samples.jsonl"
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="altered original"):
        replay_trial(location, spec, reported)


def test_bad_calibration_and_controller_source_never_trusted(tmp_path):
    """No fabricated positive report from incomplete evidence."""
    with pytest.raises(ValueError, match="Missing or altered"):
        replay_trial(tmp_path, {"trial_id": "missing"}, {})
