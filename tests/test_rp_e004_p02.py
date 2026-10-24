"""Synthetic adversarial tests for P02; no empirical claim is made here."""

import copy
import json

import pytest

from experiments.rp_e004_p02 import (
    CALIBRATION_RATE_VARIATION,
    GAP_LIMIT_NS,
    RECOVERY_DWELL_NS,
    SEED,
    TRIAL_NAMES,
    audit_calibration,
    decide,
    read_jsonlines,
    replay_monitor,
)


def sample(t: int, queued=0, active=0, completed=10):
    return {"observed_ns": t, "server_snapshot_ns": t - 100,
            "queued": queued, "active": active, "completed": completed}


def calibration():
    start = 1_000_000_000
    windows = []
    for k in range(3):
        a = start + 250_000_000 * k
        b = a + 250_000_000
        windows.append({
            "start_ns": a, "end_ns": b, "completed_delta": 20,
            "queued_start": 100 - 20*k, "queued_end": 80 - 20*k,
            "active_start": 1, "active_end": 1,
            "start_service_snapshot_ns": a-50,
            "end_service_snapshot_ns": b-50,
        })
    return {"windows": windows, "sparse_probe": {
        "completed": 12, "start_ns": 100, "end_ns": 200,
    }}


def test_recovery_requires_replayable_dwell_and_reports_first_sample():
    t = 1_000_000_000
    samples = [
        sample(t, queued=10), sample(t + 25_000_000, queued=5),
    ] + [sample(t + 50_000_000 + k*25_000_000)
         for k in range(21)]
    result = replay_monitor(samples, t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    assert result["recovered_at_ns"] == t + 50_000_000
    assert result["confirmed_at_ns"] == t + 550_000_000
    assert result["sample_count"] == len(samples)


def test_nonidle_sample_restarts_window():
    t = 1_000_000_000
    samples = [
        sample(t), sample(t + 25_000_000), sample(t + 50_000_000, active=1),
    ] + [sample(t + 75_000_000 + k*25_000_000) for k in range(21)]
    assert replay_monitor(samples, t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)[
        "recovered_at_ns"
    ] == t + 75_000_000


def test_missing_samples_and_out_of_order_stamps_fail_closed():
    t = 1_000_000_000
    with pytest.raises(ValueError, match="gap"):
        replay_monitor([sample(t), sample(t + GAP_LIMIT_NS + 1)],
                       t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    with pytest.raises(ValueError, match="Nonmonotonic"):
        replay_monitor([sample(t), sample(t)], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    with pytest.raises(ValueError, match="Nonmonotonic"):
        replay_monitor([sample(t), sample(t-1)], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)


def test_invalid_sample_status_and_future_service_timestamp_fail():
    t = 1_000_000_000
    with pytest.raises(ValueError, match="Invalid"):
        replay_monitor([sample(t, queued=-1)], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    bad = sample(t)
    bad["server_snapshot_ns"] = t + 1
    with pytest.raises(ValueError, match="Invalid"):
        replay_monitor([bad], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    wrong = sample(t)
    wrong["active"] = True
    with pytest.raises(ValueError, match="Non-integer"):
        replay_monitor([wrong], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)


def test_empty_trace_or_no_after_intervention_sample_fails():
    t = 1_000_000_000
    with pytest.raises(ValueError, match="Empty"):
        replay_monitor([], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    with pytest.raises(ValueError, match="No health"):
        replay_monitor([sample(t-200)], t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)


def test_trace_with_no_recovery_is_right_censored_not_discarded():
    t = 1_000_000_000
    s = [sample(t + k*25_000_000, queued=2) for k in range(35)]
    x = replay_monitor(s, t, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    assert x["recovered_at_ns"] is None
    assert x["confirmed_at_ns"] is None


def test_calibration_three_saturated_windows_and_sparse_contrast():
    r = audit_calibration(calibration())
    assert r["window_count"] == 3
    assert r["sparse_completed"] == 12
    assert r["calibrated_local_B"] == 80
    assert r["rate_windows_per_second"] == [80, 80, 80]


def test_calibration_nonempty_queue_is_required_for_all_windows():
    x = calibration()
    x["windows"][1]["queued_end"] = 0
    with pytest.raises(ValueError, match="saturation"):
        audit_calibration(x)


def test_calibration_rate_variation_stop():
    x = calibration()
    x["windows"][1]["completed_delta"] = 50
    with pytest.raises(ValueError, match="variation"):
        audit_calibration(x)


def test_calibration_sparse_probe_must_precede_three_windows():
    x = calibration()
    x["sparse_probe"]["end_ns"] = x["windows"][0]["start_ns"]
    with pytest.raises(ValueError, match="Sparse"):
        audit_calibration(x)


def test_calibration_wrong_number_of_windows():
    x = calibration()
    x["windows"].pop()
    with pytest.raises(ValueError, match="exactly three"):
        audit_calibration(x)


def test_decision_requires_all_four_fixed_trials():
    proper = [
        {"trial_id": TRIAL_NAMES[0], "verdict": "AUDITABLE_CONTROLLED_POSITIVE"},
        {"trial_id": TRIAL_NAMES[1], "verdict": "AUDITABLE_CONTROLLED_POSITIVE"},
        {"trial_id": TRIAL_NAMES[2], "verdict": "DISABLED_CONTROL_RECOVERY_REPLAYED"},
        {"trial_id": TRIAL_NAMES[3], "verdict": "SHAM_UNDEFINED_INDEX"},
    ]
    assert decide(proper) == "PASS_AUDITABLE_INSTRUMENTATION"
    assert decide(proper[:-1]) == "STOP_INSTRUMENTATION_UNRELIABLE"
    bad = copy.deepcopy(proper)
    bad[0]["verdict"] = "STOP_TRIAL_AUDIT"
    assert decide(bad) == "STOP_INSTRUMENTATION_UNRELIABLE"


def test_frozen_order_is_deterministic_and_contains_all_groups():
    import random
    one, two = list(TRIAL_NAMES), list(TRIAL_NAMES)
    random.Random(SEED).shuffle(one)
    random.Random(SEED).shuffle(two)
    assert one == two
    assert len(set(one)) == 4
    assert one.count("sham-01") == 1
