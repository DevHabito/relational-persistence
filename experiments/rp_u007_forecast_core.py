"""RP-U007: fixed, source-free comparison of informed queue forecasts.

Both predictors share all registered arrivals, time since enable, the same
per-regime capacity calibration and planned future work. Only one gets a
measured live outstanding-work sample. No outcome-dependent learning.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import median

PROTOCOL = "RP-U007-P01"
PROTOCOL_SHA = "0589da88d5df064d033e5a8b774d31c862bede27"
REGIMES = {
    "fast": (6, 9, 12),
    "standard": (8, 12, 16),
    "slow": (12, 18, 24),
}
CALIBRATION_ORDER = ("fast", "standard", "slow")
CALIBRATION_TASKS = 18
LANDMARK_NS = 100_000_000
LANDMARK_SECONDS = .100
LATEST_SNAPSHOT_AGE_NS = 30_000_000
FORECAST_DEADLINE_NS = 125_000_000
FUTURE_BATCH_OFFSET_NS = 160_000_000
FUTURE_BATCH_COUNT = 2
EXPECTED_EARLY_ADDED_JOBS = 4
LATENCY_ALLOWANCE_SECONDS = .024
FUTURE_MINIMUM_LEAD_SECONDS = .060
MAX_MONITOR_GAP_NS = 120_000_000
MIN_RECOVERY_PAIR_GAP_NS = 8_000_000
MIN_POST_RECOVERY_MONITOR_NS = 60_000_000
MIN_MAE_REDUCTION = .20
MIN_WINS = 9

@dataclass(frozen=True)
class Holdout:
    regime: str
    initial_jobs: int

HOLDOUTS = (
    Holdout("standard", 14),
    Holdout("slow", 10),
    Holdout("fast", 18),
    Holdout("slow", 22),
    Holdout("fast", 10),
    Holdout("standard", 22),
    Holdout("standard", 10),
    Holdout("fast", 22),
    Holdout("slow", 18),
    Holdout("standard", 18),
    Holdout("slow", 14),
    Holdout("fast", 14),
)

class InvalidEvidence(ValueError):
    """An original source or fixed measurement requirement failed."""


def calibrated_interval(events: list[dict]) -> float:
    """14 completion times from IDs 5..18 provide exactly 13 gaps."""
    completes = [
        (e.get("job"), e.get("server_time_ns"))
        for e in events if e.get("event") == "complete"
    ]
    if [r[0] for r in completes] != list(range(1, CALIBRATION_TASKS + 1)):
        raise InvalidEvidence("CALIBRATION_COMPLETION_SEQUENCE_CHANGED")
    if any(type(t) is not int or t <= 0 for _, t in completes):
        raise InvalidEvidence("INVALID_CALIBRATION_CLOCK")
    selected = [t for _, t in completes[4:]]
    diffs = [(y-x)/1e9 for x, y in zip(selected, selected[1:])]
    if len(diffs) != 13 or any(not math.isfinite(v) or v <= 0 for v in diffs):
        raise InvalidEvidence("THIRTEEN_POSITIVE_CALIBRATION_INTERVALS_REQUIRED")
    return float(median(diffs))


def validate_events(events: list[dict], *, initial: int,
                    calibration: bool) -> dict:
    """Reconstruct complete event/job identity using service-side source rows."""
    if (type(initial) is not int or initial < 0 or initial > 22
            or not isinstance(events, list) or not events):
        raise InvalidEvidence("INVALID_SOURCE_EVENT_CENSUS")
    total = initial if calibration else initial + 6
    if any(type(e.get("server_time_ns")) is not int for e in events):
        raise InvalidEvidence("MISSING_SERVER_EVENT_CLOCK")
    if any(b["server_time_ns"] < a["server_time_ns"]
           for a, b in zip(events, events[1:])):
        raise InvalidEvidence("NONMONOTONIC_SOURCE_EVENT_CLOCK")
    accepts = [e for e in events if e.get("event") == "accept"]
    starts = [e for e in events if e.get("event") == "start"]
    completes = [e for e in events if e.get("event") == "complete"]
    expected = list(range(1, total + 1))
    if any([e.get("job") for e in rows] != expected
           for rows in (accepts, starts, completes)):
        raise InvalidEvidence("SOURCE_JOB_IDENTITY_OR_FIFO_MISMATCH")
    enable = [e for e in events if e.get("event") == "enable"]
    shutdown = [e for e in events if e.get("event") == "shutdown"]
    if len(enable) != 1 or len(shutdown) != 1:
        raise InvalidEvidence("SOURCE_ENABLE_AND_SHUTDOWN_COUNT_MISMATCH")
    en = enable[0]["server_time_ns"]
    if calibration:
        if any(e["server_time_ns"] <= en for e in accepts):
            raise InvalidEvidence("CALIBRATION_ACCEPTED_BEFORE_ENABLE")
    else:
        if (any(e["server_time_ns"] >= en for e in accepts[:initial])
                or any(e["server_time_ns"] <= en for e in accepts[initial:])
                or any(e["server_time_ns"] <= en for e in completes)):
            raise InvalidEvidence("ORIGINAL_PRE_POST_ENABLE_BATCH_TIMELINE_INVALID")
    if starts and any(e["server_time_ns"] < en for e in starts):
        raise InvalidEvidence("SOURCE_WORKER_STARTED_BEFORE_ENABLE")
    if not calibration:
        first_early = accepts[initial:initial+2]
        second_early = accepts[initial+2:initial+4]
        final = accepts[initial+4:]
        if not (len(first_early) == len(second_early) == len(final) == 2):
            raise InvalidEvidence("INVALID_POST_ENABLE_BATCH_COMPOSITION")
    if (shutdown[0]["server_time_ns"] < completes[-1]["server_time_ns"]
            or shutdown[0].get("completed") != total):
        raise InvalidEvidence("EARLY_SHUTDOWN_OR_INCOMPLETE_SOURCE_WORK")
    return {
        "accepted_count": len(accepts), "completed_count": len(completes),
        "enable_ns": en,
        "first_two_post_batches_last_accept_ns": (
            accepts[initial+3]["server_time_ns"] if not calibration else None
        ),
        "last_batch_last_accept_ns": (
            accepts[-1]["server_time_ns"] if not calibration else None
        ),
    }


def validate_samples(samples: list[dict], *, total: int,
                     enable_ns: int) -> None:
    if not isinstance(samples, list) or len(samples) < 5:
        raise InvalidEvidence("MISSING_SOURCE_MONITOR_HISTORY")
    last = -1
    after = []
    for s in samples:
        t = s.get("observed_ns")
        server = s.get("server_snapshot_ns")
        if type(t) is not int or type(server) is not int:
            raise InvalidEvidence("MISSING_MONITOR_OR_SERVER_CLOCK")
        if not (t >= server and t > last):
            raise InvalidEvidence("MONITOR_CLOCK_ORDERING_INVALID")
        last = t
        values = [s.get(k) for k in ("accepted","completed","queued","active")]
        if any(type(x) is not int for x in values):
            raise InvalidEvidence("NONINTEGER_MONITOR_COUNTER")
        a,c,q,active = values
        if (a < 0 or a > total or c < 0 or c > a or
                min(q,active) < 0 or q + active != a - c):
            raise InvalidEvidence("MONITOR_WORK_CONSERVATION_VIOLATED")
        if type(s.get("available")) is not bool:
            raise InvalidEvidence("MONITOR_AVAILABILITY_UNDECLARED")
        if server > enable_ns:
            after.append(s)
    if len(after) < 4:
        raise InvalidEvidence("TOO_FEW_POST_ENABLE_SAMPLES")
    if any(b["observed_ns"]-a["observed_ns"] > MAX_MONITOR_GAP_NS
           for a,b in zip(after,after[1:])):
        raise InvalidEvidence("MISSING_POST_ENABLE_MONITOR_INTERVAL")


def select_landmark_sample(samples: list[dict], *,
                           enable_ns: int, expected_accepted: int) -> dict:
    """Exactly latest eligible-timestamp sample, never choose better backlog."""
    threshold = enable_ns + LANDMARK_NS
    prior = [s for s in samples if s["observed_ns"] <= threshold
             and s["server_snapshot_ns"] > enable_ns]
    if not prior:
        raise InvalidEvidence("NO_PRE_LANDMARK_LIVE_MONITOR_SAMPLE")
    sample = max(prior, key=lambda s: s["observed_ns"])
    if sample["observed_ns"] < threshold - LATEST_SNAPSHOT_AGE_NS:
        raise InvalidEvidence("STALE_LANDMARK_MONITOR_SAMPLE")
    if (sample["accepted"] != expected_accepted
            or sample["available"] is not True
            or sample["queued"] + sample["active"] !=
                sample["accepted"] - sample["completed"]):
        raise InvalidEvidence("PRE_LANDMARK_STATE_OR_ACCEPTED_COUNT_MISMATCH")
    return sample


def original_forecasts(interval_sec: float, *,
                       accepted_at_landmark: int,
                       observed_outstanding: int) -> dict:
    if (not math.isfinite(interval_sec) or interval_sec <= 0
            or type(accepted_at_landmark) is not int
            or type(observed_outstanding) is not int
            or accepted_at_landmark < EXPECTED_EARLY_ADDED_JOBS
            or observed_outstanding < 0
            or observed_outstanding > accepted_at_landmark):
        raise InvalidEvidence("NONFINITE_OR_INVALID_LANDMARK_FEATURE")
    expected_completed = math.floor(LANDMARK_SECONDS / interval_sec)
    input_only_backlog = max(0, accepted_at_landmark - expected_completed)
    def predict(backlog: int) -> float:
        return max((backlog + FUTURE_BATCH_COUNT)*interval_sec,
                   FUTURE_MINIMUM_LEAD_SECONDS) + LATENCY_ALLOWANCE_SECONDS
    before = predict(input_only_backlog)
    after = predict(observed_outstanding)
    if before != predict(input_only_backlog):
        raise InvalidEvidence("SOURCE_FREE_SHAM_PREDICTION_MISMATCH")
    return {
        "calibrated_interval_seconds": interval_sec,
        "accepted_by_landmark": accepted_at_landmark,
        "input_inferred_backlog": input_only_backlog,
        "observed_landmark_backlog": observed_outstanding,
        "future_registered_jobs": FUTURE_BATCH_COUNT,
        "input_capacity_prediction_seconds": before,
        "observed_state_prediction_seconds": after,
        "sham_replacing_measured_with_inferred_seconds": predict(input_only_backlog),
    }


def measured_recovery(samples: list[dict], *, landmark_ns: int,
                      final_batch_accept_ns: int) -> float:
    if type(landmark_ns) is not int or type(final_batch_accept_ns) is not int:
        raise InvalidEvidence("MISSING_RECOVERY_ANCHOR")
    if final_batch_accept_ns <= landmark_ns:
        raise InvalidEvidence("FINAL_BATCH_NOT_AFTER_LANDMARK")
    after = [s for s in samples if s["server_snapshot_ns"] >
             final_batch_accept_ns]
    if len(after) < 3:
        raise InvalidEvidence("INSUFFICIENT_POST_FINAL_BATCH_SAMPLES")
    for a,b in zip(after,after[1:]):
        gap = b["observed_ns"]-a["observed_ns"]
        if (a["accepted"] == b["accepted"]
                and a["queued"]+a["active"] == 0
                and b["queued"]+b["active"] == 0
                and MIN_RECOVERY_PAIR_GAP_NS <= gap <= MAX_MONITOR_GAP_NS):
            if samples[-1]["observed_ns"]-b["observed_ns"] < (
                    MIN_POST_RECOVERY_MONITOR_NS):
                raise InvalidEvidence("INSUFFICIENT_POST_RECOVERY_MONITOR_FOLLOWUP")
            return (b["observed_ns"]-landmark_ns)/1e9
    raise InvalidEvidence("RECOVERY_NOT_OBSERVED_IN_FROZEN_HORIZON")


def evaluate_original(source: dict) -> dict:
    if (source.get("original_sources_all_valid") is not True
            or source.get("status") != "RP_U007_SOURCE_READY_FOR_EVALUATION"):
        raise InvalidEvidence("UNVERIFIED_ORIGINAL_SOURCE_TRIAL_CENSUS")
    calibration = source.get("calibration")
    holdouts = source.get("holdouts")
    if not isinstance(calibration, list) or len(calibration) != 3:
        raise InvalidEvidence("THREE_PRE_HOLDOUT_CALIBRATIONS_REQUIRED")
    if not isinstance(holdouts, list) or len(holdouts) != 12:
        raise InvalidEvidence("TWELVE_HOLDOUTS_REQUIRED")
    if [r["regime"] for r in calibration] != list(CALIBRATION_ORDER):
        raise InvalidEvidence("CALIBRATION_REGIME_ORDER_CHANGED")
    if [(r.get("regime"),r.get("initial_jobs")) for r in holdouts] != [
        (p.regime,p.initial_jobs) for p in HOLDOUTS
    ]:
        raise InvalidEvidence("HOLDOUT_REGIME_ORDER_OR_LOAD_CHANGED")
    errors_i,errors_s,comparison=[],[],[]
    for row in holdouts:
        if row.get("valid_original_trial") is not True:
            raise InvalidEvidence("INVALID_INDIVIDUAL_HOLDOUT")
        actual=row.get("measured_recovery_from_landmark_seconds")
        pred=row.get("predictions")
        if type(actual) is not float or not math.isfinite(actual) or actual <= 0:
            raise InvalidEvidence("INVALID_HELDOUT_RECOVERY_TIME")
        if not isinstance(pred,dict):
            raise InvalidEvidence("MISSING_PRE_OUTCOME_FORECAST")
        input_value=pred.get("input_capacity_prediction_seconds")
        observed_value=pred.get("observed_state_prediction_seconds")
        if any(type(v) is not float or not math.isfinite(v) or v < 0
               for v in (input_value,observed_value)):
            raise InvalidEvidence("INVALID_HELDOUT_FORECAST_VALUE")
        if pred.get("sham_replacing_measured_with_inferred_seconds") != input_value:
            raise InvalidEvidence("ALGORITHMIC_NEGATIVE_CONTROL_FAILED")
        err_i=abs(input_value-actual)
        err_s=abs(observed_value-actual)
        errors_i.append(err_i)
        errors_s.append(err_s)
        comparison.append({
            "regime":row["regime"],"initial_jobs":row["initial_jobs"],
            "actual_remaining_seconds":actual,
            "input_capacity_absolute_error_seconds":err_i,
            "measured_state_absolute_error_seconds":err_s,
            "state_strictly_better":bool(err_s < err_i),
        })
    mae_i=sum(errors_i)/12
    mae_s=sum(errors_s)/12
    win_count=sum(p["state_strictly_better"] for p in comparison)
    gain=(mae_i-mae_s)/mae_i if mae_i > 0 else None
    support=bool(
        mae_i > 0 and mae_s <= (1-MIN_MAE_REDUCTION)*mae_i
        and win_count >= MIN_WINS
    )
    return {
        "status": (
            "RP_U007_INCREMENTAL_LIVE_STATE_GAIN_WITHIN_HOST" if support else
            "RP_U007_COMPLETE_NO_CONFIRMED_INCREMENT"
        ),
        "study":PROTOCOL,
        "input_capacity_MAE_seconds":mae_i,
        "observed_state_MAE_seconds":mae_s,
        "relative_MAE_reduction":gain,
        "strict_state_wins":win_count,
        "total_holdouts":12,
        "registered_increment_confirmed_within_host":support,
        "all_individual_comparisons":comparison,
        "no_population_p_value_claimed":True,
        "physical_network_repair_or_biological_recovery_measured":False,
    }
