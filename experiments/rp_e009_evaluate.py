"""RP-E009: independently replay original executable TCP service evidence.

Refuse incomplete/corrupt source, temporal leakage, reordered FIFO events,
and changed labels. The proposed trend is classical and has no fit.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

from experiments.rp_e004_p02 import (
    GAP_LIMIT_NS, RECOVERY_DWELL_NS, read_jsonlines, replay_monitor,
)
from experiments.rp_e005_idle_oracle import replay_idle_groups
from experiments.rp_e007_temporal_backlog import predict_from_source
from experiments.rp_e009_acquire import (
    ORIGINAL_FILES, PROTOCOL, digest, registered_trials,
)

EXPECTED_CALIBRATION = 60
THRESHOLD = .90


def obj(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Nonobject original record")
    return data


def integer(x: object, label: str, *, positive: bool = False) -> int:
    if type(x) is not int or x < (1 if positive else 0):
        raise ValueError(f"Bad integer {label}")
    return x


def check_events(events: list[dict], injection: dict, controller: dict,
                 calib: dict) -> list[dict]:
    if not events:
        raise ValueError("No actual service-side events")
    last = -1
    allowed = {"accept", "start", "complete", "reset", "accelerate"}
    for event in events:
        stamp = integer(event["time_ns"], "event time", positive=True)
        if stamp < last or event["event"] not in allowed:
            raise ValueError("Event times unordered or unknown event kind")
        last = stamp
    reset_events = [e for e in events if e["event"] == "reset"]
    speed_events = [e for e in events if e["event"] == "accelerate"]
    if len(reset_events) != 1 or len(speed_events) != 1:
        raise ValueError("Missing or repeated control/reset")
    reset = reset_events[0]
    action = speed_events[0]
    if (reset["phase"] != "calibration" or action["phase"] != "experiment"
            or reset["calibrated_tasks"] != EXPECTED_CALIBRATION
            or action.get("speed_factor") != 2
            or controller["actual_service_applied_ns"] != action["time_ns"]
            or controller["acknowledged_ns"] < action["time_ns"]):
        raise ValueError("Incorrect actual service-control provenance")
    calibration = [e for e in events
                   if e["phase"] == "calibration"
                   and e["event"] in ("accept", "start", "complete")]
    intervention = [e for e in events
                    if e["phase"] == "experiment"
                    and e["event"] in ("accept", "start", "complete")]
    if (len(calibration) != 3 * EXPECTED_CALIBRATION
            or not calibration
            or calibration[-1]["time_ns"] >= reset["time_ns"]
            or action["time_ns"] <= reset["time_ns"]
            or not intervention
            or intervention[0]["time_ns"] <= action["time_ns"]):
        raise ValueError("Calibration and intervention phases overlap")

    def inspect(rows: list[dict], n: int) -> dict:
        categorized = {
            event: [e for e in rows if e["event"] == event]
            for event in ("accept", "start", "complete")
        }
        if any(len(a) != n for a in categorized.values()):
            raise ValueError("Missing accepted/start/completed tasks")
        for event in categorized:
            jobs = [integer(e["job"], "job", positive=True)
                    for e in categorized[event]]
            if jobs != list(range(1, n + 1)):
                raise ValueError("Duplicate, missing or reordered FIFO task")
        by_id = {
            kind: {r["job"]: r for r in categorized[kind]}
            for kind in categorized
        }
        for j in range(1, n + 1):
            a = by_id["accept"][j]["time_ns"]
            start = by_id["start"][j]["time_ns"]
            finish = by_id["complete"][j]["time_ns"]
            if not a <= start < finish:
                raise ValueError("Service started before arrival or stopped out of order")
            if j > 1 and start < by_id["complete"][j - 1]["time_ns"]:
                raise ValueError("Overlapping workers")
            if by_id["accept"][j].get("nominal_prechange_ms") != (8, 12, 16)[(j - 1) % 3]:
                raise ValueError("Unexpected worker service pattern")
        return categorized

    inspect(calibration, EXPECTED_CALIBRATION)
    count = integer(injection["work_units"], "intervention units", positive=True)
    experiment = inspect(intervention, count)
    earliest_send = integer(injection["first_enqueue_sent_ns"], "injection start",
                            positive=True)
    end = integer(injection["end_ns"], "injection end", positive=True)
    if (calibration[0]["time_ns"] < calib["first_enqueue_sent_ns"]
            or calib["last_completed_observed_ns"] <= calibration[-1]["time_ns"]
            or calib["last_completed_observed_ns"] >= reset["time_ns"]
            or action["time_ns"] >= earliest_send):
        raise ValueError("Calibration timestamps conflict with service-side records")
    sends = injection["accepted_send_timestamps_ns"]
    acknowledgements = injection["acknowledged_timestamps_ns"]
    if len(sends) != count or len(acknowledgements) != count:
        raise ValueError("Missing original submission timestamps")
    if end != acknowledgements[-1]:
        raise ValueError("Incorrect original forecast origin")
    if any(not (sends[i] <= experiment["accept"][i]["time_ns"]
                <= acknowledgements[i] <= end)
           for i in range(count)):
        raise ValueError("Work accepted outside original client request interval")
    if any(sends[i] >= sends[i + 1] for i in range(count - 1)):
        raise ValueError("Nonmonotonic injection send times")
    return intervention


def check_monitor(samples: list[dict], events: list[dict],
                  end: int, accepted_n: int) -> dict:
    # Derive status from independently recorded service accept/start/complete
    # events, not from the original driver summary.
    experiment = [e for e in events if e["phase"] == "experiment"]
    first = -1
    last_received = -1
    for sample in samples:
        source = integer(sample["server_snapshot_ns"], "service status time",
                         positive=True)
        received = integer(sample["observed_ns"], "client probe time",
                           positive=True)
        if source <= first or received <= last_received or source > received:
            raise ValueError("Invalid monotonic probe ordering")
        first, last_received = source, received
        before = [e for e in experiment if e["time_ns"] <= source]
        count = Counter(e["event"] for e in before)
        n_accepted = count["accept"]
        n_started = count["start"]
        n_completed = count["complete"]
        if (sample["accepted"] != n_accepted
                or sample["completed"] != n_completed
                or sample["queued"] != n_accepted - n_started
                or sample["active"] != n_started - n_completed):
            raise ValueError("Reported status contradicts actual original service events")
        if sample["active"] not in (0, 1):
            raise ValueError("More than one worker reported active")
    last_after = [s for s in samples if s["observed_ns"] >= end]
    if not last_after or samples[-1]["accepted"] != accepted_n:
        raise ValueError("Incomplete monitor trace")
    first_replay = replay_monitor(
        samples, end, RECOVERY_DWELL_NS, GAP_LIMIT_NS
    )
    second_replay = replay_idle_groups(samples, end)
    if first_replay != second_replay or first_replay["confirmed_at_ns"] is None:
        raise ValueError("Unconfirmed oracles disagree on sampled recovery")
    return first_replay


def replay_trial(folder: Path, spec: dict, recorded: dict) -> dict:
    for name in ORIGINAL_FILES:
        path = folder / name
        if not path.is_file() or recorded.get("file_sha256", {}).get(name) != digest(path):
            raise ValueError(f"Missing or altered original event source: {name}")
    config = obj(folder / "configuration.json")
    if config != spec or recorded.get("trial_id") != spec["trial_id"]:
        raise ValueError("Wrong original trial identity")
    calibration = obj(folder / "calibration.json")
    controller = obj(folder / "controller.json")
    injection = obj(folder / "injector.json")
    feature = obj(folder / "feature-snapshot.json")
    events = read_jsonlines(folder / "service-events.jsonl")
    samples = read_jsonlines(folder / "monitor-samples.jsonl")
    if calibration["accepted"] != 60 or calibration["completed"] != 60:
        raise ValueError("Untrusted pre-intervention calibration")
    start = integer(calibration["first_enqueue_sent_ns"], "calibration begin",
                    positive=True)
    finish = integer(calibration["last_completed_observed_ns"], "calibration end",
                     positive=True)
    if not finish > start:
        raise ValueError("Nonpositive observed calibration interval")
    capacity = 60e9 / (finish - start)
    if not math.isfinite(capacity) or capacity <= 0 or (
        calibration["observed_B_work_per_second"] != capacity
    ):
        raise ValueError("Calibration capacity not independently reproducible")
    if controller.get("before_intervention") is not True or (
        controller.get("speed_factor") != 2
    ):
        raise ValueError("Wrong control condition")
    if (injection.get("work_units") != spec["work_units"]
            or injection.get("arrival_mode") != spec["arrival_mode"]
            or injection.get("accepted") != spec["work_units"]):
        raise ValueError("Wrong intervention identity or delivered workload")
    examined = check_events(events, injection, controller, calibration)
    end = injection["end_ns"]
    if (examined[-1]["event"] != "complete" or
            examined[-1]["time_ns"] > samples[-1]["server_snapshot_ns"]):
        raise ValueError("Observation ended before all job completions")
    replay = check_monitor(samples, events, end, spec["work_units"])
    from experiments.rp_e007_temporal_backlog import pre_end_pair
    prior, last = pre_end_pair(samples, end)
    expected_snapshot = {
        "previous_observed_ns": prior["observed_ns"],
        "latest_observed_ns": last["observed_ns"],
        "previous_queued_and_active": prior["queued"] + prior["active"],
        "latest_queued_and_active": last["queued"] + last["active"],
        "source": "two original TCP health responses prior to injector end",
    }
    if feature != expected_snapshot:
        raise ValueError("Pre-end features contradict raw observed state")
    forecast = predict_from_source(samples, end, capacity)
    outcome = (replay["recovered_at_ns"] - end) / 1e9
    if outcome < 0 or replay["confirmed_at_ns"] > samples[-1]["observed_ns"]:
        raise ValueError("Invalid independent sampled recovery")
    if (recorded["monitor_samples"] != len(samples) or
            recorded["observed_B_work_per_second"] != capacity or
            recorded["accepted_intervention_work"] != spec["work_units"]):
        raise ValueError("Original per-trial report contradicts source")
    return {
        "trial_id": spec["trial_id"], "work_units": spec["work_units"],
        "arrival_mode": spec["arrival_mode"],
        "observed_B_work_per_second": capacity,
        "actual_intervention_seconds": (end - injection["first_enqueue_sent_ns"]) / 1e9,
        "sampled_recovery_s": outcome,
        "raw_event_sha256": digest(folder / "service-events.jsonl"),
        "raw_monitor_sha256": digest(folder / "monitor-samples.jsonl"),
        **forecast,
    }


def replay_split(directory: Path, split: str, run_id: str,
                 source_sha: str, proto_sha: str) -> tuple[list[dict], dict]:
    evidence = obj(directory / "provenance.json")
    summary = obj(directory / "summary.json")
    expected = {
        "protocol": PROTOCOL, "split": split,
        "source_commit": source_sha, "workflow_run_id": run_id,
        "preregistration_sha256": proto_sha,
        "trial_order": registered_trials(split),
        "independent_physical_system": "NOT_ESTABLISHED",
        "predictive_scalar_C_test": "NOT_PERFORMED",
    }
    for record in (evidence, summary):
        for k, value in expected.items():
            if record.get(k) != value:
                raise ValueError(f"{split}: wrong source identity {k}")
        if not str(record.get("runtime", "")).startswith("3.12.") or (
            not str(record.get("platform", "")).startswith("Linux-")
        ):
            raise ValueError(f"{split}: wrong declared runtime")
    if summary.get("acquisition_gate") != "PASS_ALL_RECORDED":
        raise ValueError(f"{split}: original acquisition gate failed")
    claimed = summary.get("original_trials")
    if not isinstance(claimed, list) or len(claimed) != 9:
        raise ValueError(f"{split}: incomplete original trials")
    audited = []
    hashes = {}
    for spec, declared in zip(registered_trials(split), claimed):
        casefolder = directory / spec["trial_id"]
        measured = replay_trial(casefolder, spec, declared)
        audited.append(measured)
        hashes.update({
            f"{split}/{spec['trial_id']}/{name}": digest(casefolder / name)
            for name in ORIGINAL_FILES
        })
    return audited, hashes


def score(diagnostic: list[dict], heldout: list[dict]) -> dict:
    if len(diagnostic) != 9 or len(heldout) != 9:
        raise ValueError("Incomplete original diagnostic or held-out records")
    train_average = math.fsum(row["sampled_recovery_s"] for row in diagnostic) / 9
    predictions = []
    for row in heldout:
        actual = row["sampled_recovery_s"]
        estimates = {
            "static": row["prediction_static_s"],
            "trend": row["prediction_trend_s"],
            "diagnostic_mean": train_average,
        }
        errors = {key: abs(val - actual) for key, val in estimates.items()}
        predictions.append({
            **row, "predictions_s": estimates, "absolute_errors_s": errors,
        })
    maes = {
        model: math.fsum(p["absolute_errors_s"][model] for p in predictions) / 9
        for model in ("static", "trend", "diagnostic_mean")
    }
    static = maes["static"]
    if not all(math.isfinite(v) and v >= 0 for v in maes.values()):
        raise ValueError("Invalid heldout metric")
    passed = static > 0 and maes["trend"] <= THRESHOLD * static
    profiles = {}
    for profile in ("uniform", "early_burst", "late_burst"):
        cases = [p for p in predictions if p["arrival_mode"] == profile]
        profiles[profile] = {
            model: math.fsum(p["absolute_errors_s"][model] for p in cases) / 3
            for model in ("static", "trend")
        }
    wins = sum(p["absolute_errors_s"]["trend"] <
               p["absolute_errors_s"]["static"] for p in predictions)
    ties = sum(p["absolute_errors_s"]["trend"] ==
               p["absolute_errors_s"]["static"] for p in predictions)
    return {
        "decision": "PASS_EXECUTABLE_TRANSFER" if passed
        else "NO_REGISTERED_EXECUTABLE_GAIN",
        "registered_threshold": THRESHOLD,
        "mae_seconds": maes, "per_arrival_mode_mae_seconds": profiles,
        "trend_wins": wins, "ties": ties, "trend_losses": 9 - wins - ties,
        "diagnostic_only_mean_s": train_average,
        "heldout_cases": predictions,
    }


def evaluate(root: Path, project: Path, run_id: str, source_sha: str) -> dict:
    protocol_sha = digest(project / "docs/preregistration/RP-E009-P01.md")
    completed, all_hashes, failures = {}, {}, []
    for split in ("diagnostic", "holdout"):
        try:
            completed[split], hashes = replay_split(
                root / f"rp-e009-p01-{split}", split, run_id,
                source_sha, protocol_sha
            )
            all_hashes.update(hashes)
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
            failures.append({
                "block": split, "reason": f"{type(exc).__name__}: {exc}"
            })
    report = {
        "protocol": PROTOCOL, "source_commit": source_sha,
        "workflow_run_id": run_id, "preregistration_sha256": protocol_sha,
        "diagnostic_trials_replayed": len(completed.get("diagnostic", [])),
        "heldout_trials_replayed": len(completed.get("holdout", [])),
        "verified_original_source_file_count": len(all_hashes),
        "original_sha256": all_hashes,
        "errors": failures, "scoring": None,
        "decision": "STOP_TRANSFER_AUDIT",
        "physical_independence": "NOT_ESTABLISHED",
        "physical_law_test": "NOT_PERFORMED",
        "prior_RP_E007_observations_reused": False,
        "new_lean_theorem": False,
    }
    if failures:
        return report
    try:
        report["scoring"] = score(completed["diagnostic"], completed["holdout"])
        report["decision"] = report["scoring"]["decision"]
    except (ValueError, KeyError, TypeError) as exc:
        report["errors"] = [{
            "block": "score", "reason": f"{type(exc).__name__}: {exc}"
        }]
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--source-sha", required=True)
    args = p.parse_args()
    result = evaluate(
        args.input, Path(__file__).resolve().parents[1],
        args.run_id, args.source_sha
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "RP-E009-P01.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "decision": result["decision"],
        "source_files": result["verified_original_source_file_count"],
        "errors": result["errors"],
        "mae": result["scoring"]["mae_seconds"] if result["scoring"] else None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
