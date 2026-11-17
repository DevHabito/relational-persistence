"""RP-U006 source-independent fixed recovery/forecast evaluation.

Use one training median, one pretrial calibration, and eight future holdout
forecasts. All decisions were registered before any hosted measurements.
"""
from __future__ import annotations

from statistics import median
import math

PROTOCOL = "RP-U006-P01"
PROTOCOL_ONLY_SHA = "b99e505d99d25bed57e2308029947407b2668777"
CALIBRATION_CORRECTION_SHA = "376eb4de39990d22112f80606a2fbe1d765e1163"
CALIBRATION_TASKS = 12
DIAGNOSTIC_LOADS = (8, 16, 24, 8, 16, 24)
HOLDOUT_LOADS = (7, 11, 15, 19, 23, 9, 21, 13)
POLL_SECONDS = 0.020
DURATION_SECONDS = 0.012
MONITOR_LATENCY_ALLOWANCE_SECONDS = 0.040
MIN_PAIR_GAP_NS = 15_000_000
MAX_PAIR_GAP_NS = 120_000_000
HOLDOUT_WIN_MIN = 6
MIN_MAE_REDUCTION = 0.25


class InvalidObservation(ValueError):
    pass


def calibration_interval(events: list[dict]) -> float:
    """Jobs 3..12 inclusive give exactly nine consecutive intervals."""
    completes = [
        (e.get("job"), e.get("server_time_ns"))
        for e in events if e.get("event") == "complete"
    ]
    if [p[0] for p in completes] != list(range(1, 13)):
        raise InvalidObservation("CALIBRATION_INCOMPLETE_OR_REORDERED")
    if any(type(p[1]) is not int or p[1] <= 0 for p in completes):
        raise InvalidObservation("INVALID_CALIBRATION_TIMESTAMP")
    stamps = [p[1] for p in completes[2:]]
    intervals = [(b - a) / 1e9 for a, b in zip(stamps, stamps[1:], strict=False)]
    if len(intervals) != 9 or any(x <= 0 for x in intervals):
        raise InvalidObservation("NINE_POSITIVE_SERVICE_INTERVALS_REQUIRED")
    return float(median(intervals))


def validate_service_events(events: list[dict], batch: int,
                            *, calibration: bool) -> dict:
    """Independent job-identity conservation based only on original server log."""
    if type(batch) is not int or not 0 <= batch <= 24:
        raise InvalidObservation("UNREGISTERED_SOURCE_BATCH")
    accepted = [x.get("job") for x in events if x.get("event") == "accept"]
    started = [x.get("job") for x in events if x.get("event") == "start"]
    finished = [x.get("job") for x in events if x.get("event") == "complete"]
    expected = list(range(1, batch + 1))
    if accepted != expected or started != expected or finished != expected:
        raise InvalidObservation("ORIGINAL_JOB_IDENTITY_OR_FIFO_AUDIT_FAILED")
    enabled = [x for x in events if x.get("event") == "enable"]
    if len(enabled) != 1:
        raise InvalidObservation("EXACTLY_ONE_ENABLE_REQUIRED")
    en_stamp = enabled[0].get("server_time_ns")
    if type(en_stamp) is not int:
        raise InvalidObservation("INVALID_SERVICE_ENABLE_STAMP")
    if any(type(x.get("server_time_ns")) is not int for x in events):
        raise InvalidObservation("MISSING_MONOTONIC_SERVER_TIME")
    if any(b["server_time_ns"] < a["server_time_ns"]
           for a, b in zip(events, events[1:])):
        raise InvalidObservation("NONMONOTONIC_SERVICE_EVENT_CLOCK")
    accepts = [x["server_time_ns"] for x in events if x.get("event") == "accept"]
    first_completions = [x["server_time_ns"] for x in events
                         if x.get("event") == "complete"]
    if (not calibration and (any(t >= en_stamp for t in accepts)
                             or any(t <= en_stamp for t in first_completions))):
        raise InvalidObservation("TASKS_STARTED_BEFORE_RESTORE_OR_LATE_ARRIVALS")
    if calibration and any(t <= en_stamp for t in first_completions):
        raise InvalidObservation("CALIBRATION_COMPLETION_BEFORE_ENABLE")
    return {"accepted": len(accepted), "completed": len(finished),
            "server_enable_ns": en_stamp}


def recovery_elapsed(samples: list[dict], enable_ns: int,
                     expected_jobs: int) -> float:
    """First pair of qualifying zero-health probes after restore; fail closed."""
    if len(samples) < 5:
        raise InvalidObservation("INSUFFICIENT_INDEPENDENT_MONITOR_SAMPLES")
    if type(enable_ns) is not int:
        raise InvalidObservation("BAD_ENABLE_TIME")
    last_receipt = -1
    valid = []
    for x in samples:
        receipt = x.get("observed_ns")
        server = x.get("server_snapshot_ns")
        if type(receipt) is not int or type(server) is not int:
            raise InvalidObservation("MISSING_SEPARATE_MONITOR_TIMESTAMPS")
        if receipt < server or receipt <= last_receipt:
            raise InvalidObservation("MONITOR_AND_SERVER_CLOCK_INCONSISTENCY")
        last_receipt = receipt
        accepted = x.get("accepted")
        completed = x.get("completed")
        queued = x.get("queued")
        active = x.get("active")
        if any(type(v) is not int for v in (accepted, completed, queued, active)):
            raise InvalidObservation("NONINTEGER_SERVICE_HEALTH_COUNTER")
        if (min(accepted, completed, queued, active) < 0
                or accepted > expected_jobs or completed > accepted
                or queued + active != accepted - completed):
            raise InvalidObservation("MONITOR_QUEUE_CONSERVATION_FAILED")
        if server > enable_ns:
            valid.append(x)
    if len(valid) < 3:
        raise InvalidObservation("MISSING_POST_RESTORE_PROBES")
    for earlier, later in zip(valid, valid[1:]):
        gap = later["observed_ns"] - earlier["observed_ns"]
        if gap > MAX_PAIR_GAP_NS:
            raise InvalidObservation("UNBOUNDED_POST_RESTORE_MONITOR_GAP")
        if (earlier["queued"] + earlier["active"] == 0
                and later["queued"] + later["active"] == 0
                and MIN_PAIR_GAP_NS <= gap <= MAX_PAIR_GAP_NS):
            return (later["observed_ns"] - enable_ns) / 1e9
    raise InvalidObservation("RECOVERY_NOT_OBSERVED_WITHIN_SOURCE_WINDOW")


def frozen_forecasts(training_recovery: list[float], calibration_sec: float,
                     holdout_outstanding: int) -> dict:
    if len(training_recovery) != len(DIAGNOSTIC_LOADS):
        raise InvalidObservation("DIAGNOSTIC_FIT_REQUIRES_SIX_PREVIOUS_TARGETS")
    if any(not math.isfinite(x) or x <= 0 for x in training_recovery):
        raise InvalidObservation("INVALID_DIAGNOSTIC_RECOVERY_DURATION")
    if not math.isfinite(calibration_sec) or calibration_sec <= 0:
        raise InvalidObservation("INVALID_MEASURED_CALIBRATION")
    if type(holdout_outstanding) is not int or holdout_outstanding < 0:
        raise InvalidObservation("NEGATIVE_OR_NONINTEGER_FEATURE")
    return {
        "availability_only_seconds": float(median(training_recovery)),
        "outstanding_aware_seconds": (
            holdout_outstanding * calibration_sec
            + MONITOR_LATENCY_ALLOWANCE_SECONDS
        ),
    }


def evaluate_original(original: dict) -> dict:
    """Data-independent, immutable decision on all eight heldout outcomes."""
    if original.get("original_trials_valid") is not True:
        raise InvalidObservation("SOME_FIRST_SOURCE_TRIALS_INVALID")
    trials = original.get("heldout")
    if not isinstance(trials, list) or len(trials) != len(HOLDOUT_LOADS):
        raise InvalidObservation("NOT_ALL_EIGHT_PRESELECTED_HOLDOUTS")
    baseline_errors = []
    aware_errors = []
    results = []
    for declared, trial in zip(HOLDOUT_LOADS, trials, strict=True):
        if trial.get("requested_jobs") != declared:
            raise InvalidObservation("HOLDOUT_ORDER_OR_LOAD_CHANGED")
        target = trial.get("recovery_seconds")
        pred = trial.get("predictions")
        if not isinstance(pred, dict):
            raise InvalidObservation("MISSING_FROZEN_HOLDOUT_FORECAST")
        baseline = pred.get("availability_only_seconds")
        aware = pred.get("outstanding_aware_seconds")
        if any(type(v) not in (float, int) or not math.isfinite(v) or v < 0
               for v in (target, baseline, aware)):
            raise InvalidObservation("NONFINITE_OR_INVALID_PREDICTION")
        be, ae = abs(target - baseline), abs(target - aware)
        baseline_errors.append(be)
        aware_errors.append(ae)
        results.append({
            "requested_jobs": declared,
            "recovery_seconds": target,
            "availability_only_absolute_error": be,
            "outstanding_aware_absolute_error": ae,
            "state_forecast_strictly_better": bool(ae < be),
        })
    mae_b = sum(baseline_errors) / len(baseline_errors)
    mae_s = sum(aware_errors) / len(aware_errors)
    wins = sum(x["state_forecast_strictly_better"] for x in results)
    supported = mae_s <= (1 - MIN_MAE_REDUCTION) * mae_b and wins >= HOLDOUT_WIN_MIN
    return {
        "status": (
            "RP_U006_EXECUTABLE_STATE_FORECAST_GAIN_WITHIN_HOST"
            if supported else "RP_U006_COMPLETE_NO_REGISTERED_GAIN"
        ),
        "holdout": results,
        "availability_only_MAE_seconds": mae_b,
        "outstanding_aware_MAE_seconds": mae_s,
        "state_forecast_strict_wins_of_eight": wins,
        "relative_MAE_reduction": (
            (mae_b - mae_s) / mae_b if mae_b > 0 else None
        ),
        "registered_gain_supported": supported,
        "heldout_trial_count": 8,
        "physical_network_repair_measured": False,
        "independent_hardware_sensors": False,
        "new_physical_or_biological_law_proven": False,
    }
