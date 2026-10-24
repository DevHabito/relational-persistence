"""Acquire the frozen RP-E006-P01 training/test software interventions.

This is an instrumented local FIFO *software* benchmark. It does not
test a universal physical law. Frozen protocol: docs/preregistration/RP-E006-P01.md.
Original RP-E004/E005 archives and service source are not modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import random
import time
from itertools import product
from pathlib import Path

from experiments.rp_e004_p02 import (
    GAP_LIMIT_NS, RECOVERY_DWELL_NS, audit_calibration, calibrate_p02,
    log_jsonline, probe_p02, read_jsonlines, serve_p02,
)
from experiments.rp_e004_pilot import (
    await_empty, await_service, join_role, pick_local_port, request,
    write_log,
)
from experiments.rp_e005_idle_oracle import replay_idle_groups
from experiments.rp_e004_p02 import replay_monitor

PROTOCOL = "RP-E006-P01"
LOADS = (60, 100, 140)
SCHEDULED_LAGS_MS = (15, 70, 120)
SPLIT_REPETITIONS = {"train": 2, "test": 1}
SPLIT_SEEDS = {"train": 20261026, "test": 20261027}
EXPECTED_PYTHON_PREFIX = "3.12."
INJECT_SPACING = 0.003
ROLE_FILENAMES = (
    "calibration.json", "controller.json", "injector.json",
    "monitor.json", "monitor-samples.jsonl", "service-actions.jsonl",
    "injector-onset.json", "forecast-snapshot.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases_for_split(split: str) -> list[dict]:
    if split not in SPLIT_REPETITIONS:
        raise ValueError("Only frozen train/test blocks are registered")
    cases = [
        {"trial_id": f"{split}-{n:03d}-{delay_ms:03d}-r{rep}",
         "work_units": n, "lag_ms": delay_ms, "repeat": rep}
        for rep in range(SPLIT_REPETITIONS[split])
        for n, delay_ms in product(LOADS, SCHEDULED_LAGS_MS)
    ]
    random.Random(SPLIT_SEEDS[split]).shuffle(cases)
    return cases


def inject(port: int, onset_file: Path, report_file: Path, work_units: int) -> None:
    # The onset file is written before any traffic; response timers
    # observe its timestamp, not injection-end or outcome labels.
    onset = time.monotonic_ns()
    write_log(onset_file, {"onset_ns": onset, "pid": os.getpid()})
    delivered = 0
    for _ in range(work_units):
        if request(port, "/work", "POST").get("accepted") is not True:
            raise RuntimeError("Server rejected registered intervention work")
        delivered += 1
        time.sleep(INJECT_SPACING)
    finish = time.monotonic_ns()
    write_log(report_file, {
        "role": "injector", "pid": os.getpid(),
        "logger_id": f"e006-injector-{os.getpid()}",
        "onset_ns": onset, "end_ns": finish,
        "delivered": delivered, "attempted": work_units,
        "nominal_spacing_seconds": INJECT_SPACING,
    })


def control(port: int, onset_file: Path, report_file: Path, lag_ms: int) -> None:
    deadline = time.monotonic() + 5
    start_ns = None
    while time.monotonic() < deadline:
        if onset_file.is_file():
            start_ns = json.loads(onset_file.read_text())["onset_ns"]
            break
        time.sleep(0.001)
    if type(start_ns) is not int:
        raise RuntimeError("No valid external onset marker")
    action_time_ns = start_ns + lag_ms * 1_000_000
    while time.monotonic_ns() < action_time_ns:
        remaining = action_time_ns - time.monotonic_ns()
        time.sleep(min(remaining / 1e9, 0.002))
    sent = time.monotonic_ns()
    result = request(port, "/action", "POST")
    ack = time.monotonic_ns()
    if result.get("changed") is not True:
        raise RuntimeError("Controller action was rejected")
    write_log(report_file, {
        "role": "controller", "pid": os.getpid(),
        "logger_id": f"e006-controller-{os.getpid()}",
        "enabled": True, "scheduled_lag_ms": lag_ms,
        "request_sent_ns": sent,
        "server_applied_ns": result["server_applied_ns"],
        "acknowledged_ns": ack,
    })


def audit_trial(folder: Path, spec: dict, *, preserve_snapshot: bool = True) -> dict:
    calibration = json.loads((folder / "calibration.json").read_text())
    injector = json.loads((folder / "injector.json").read_text())
    onset = json.loads((folder / "injector-onset.json").read_text())
    controller = json.loads((folder / "controller.json").read_text())
    monitor = json.loads((folder / "monitor.json").read_text())
    actions = read_jsonlines(folder / "service-actions.jsonl")
    samples = read_jsonlines(folder / "monitor-samples.jsonl")
    measured_calibration = audit_calibration(calibration)
    if len({calibration["pid"], injector["pid"], controller["pid"], monitor["pid"]}) != 4:
        raise ValueError("Distinct logging processes required")
    if injector["delivered"] != spec["work_units"] or injector["attempted"] != spec["work_units"]:
        raise ValueError("Incomplete positive intervention")
    if onset["onset_ns"] != injector["onset_ns"] or onset["pid"] != injector["pid"]:
        raise ValueError("Onset marker disagrees with injector log")
    start, end = injector["onset_ns"], injector["end_ns"]
    if type(start) is not int or type(end) is not int or end <= start:
        raise ValueError("Invalid monotonic injection interval")
    if calibration["windows"][-1]["end_ns"] >= start:
        raise ValueError("Capacity estimated after injection began")
    if len(actions) != 1 or controller["enabled"] is not True:
        raise ValueError("Expected exactly one live controller action")
    send, applied, ack = (
        controller["request_sent_ns"], controller["server_applied_ns"],
        controller["acknowledged_ns"],
    )
    if (not all(type(t) is int for t in (send, applied, ack))
            or not start < send <= applied <= ack or applied >= end
            or ack - send > GAP_LIMIT_NS
            or actions[0]["server_applied_ns"] != applied
            or controller["scheduled_lag_ms"] != spec["lag_ms"]):
        raise ValueError("Controller action or actual tau invalid")

    replay = replay_monitor(samples, end, RECOVERY_DWELL_NS, GAP_LIMIT_NS)
    other = replay_idle_groups(samples, end)
    if replay != other:
        raise ValueError("Independent recovery oracles disagree")
    if (replay["recovered_at_ns"] is None
            or replay["confirmed_at_ns"] is None
            or monitor["recovered_at_ns"] != replay["recovered_at_ns"]
            or monitor["confirmed_at_ns"] != replay["confirmed_at_ns"]
            or monitor["sample_count"] != len(samples)
            or monitor["logged_injector_end_ns"] != end
            or monitor["observation_end_ns"] < replay["confirmed_at_ns"]
            or monitor["observation_end_ns"] - end > 8_000_000_000 + GAP_LIMIT_NS):
        raise ValueError("Unrecovered, censored or incorrectly sampled trial")
    pre_end = [row for row in samples if row["observed_ns"] <= end]
    if not pre_end:
        raise ValueError("No valid pre-end forecast-origin observation")
    last = pre_end[-1]
    if end - last["observed_ns"] > GAP_LIMIT_NS:
        raise ValueError("Stale pre-end forecast-origin queue sample")
    if last["observed_ns"] < start:
        raise ValueError("Queue snapshot predates intervention onset")

    first_post = next((row for row in samples if row["observed_ns"] > end), None)
    if first_post is None:
        raise ValueError("No post-end health status")
    if (last["observed_ns"] >= first_post["observed_ns"]
            or last["observed_ns"] > end):
        raise ValueError("Forecast features use future samples")

    feature_snapshot = {
        "original_monitor_observed_ns": last["observed_ns"],
        "queued": last["queued"],
        "active": last["active"],
        "completed": last["completed"],
        "source": "last monitor observation at or before injector end",
    }
    if preserve_snapshot:
        write_log(folder / "forecast-snapshot.json", feature_snapshot)
    else:
        if json.loads((folder / "forecast-snapshot.json").read_text()) != feature_snapshot:
            raise ValueError("Frozen pre-end feature snapshot contradicts original monitor")
    b = measured_calibration["calibrated_local_B"]
    i = injector["delivered"] * 1e9 / (end - start)
    tau = (applied - start) / 1e9
    y = (replay["recovered_at_ns"] - end) / 1e9
    if not (b > 0 and i > 0 and tau > 0 and y >= 0):
        raise ValueError("Undefined positive-domain scalar or recovery")
    return {
        "trial_id": spec["trial_id"],
        "work_units": spec["work_units"],
        "scheduled_lag_ms": spec["lag_ms"],
        "calibrated_B_work_per_s": b,
        "measured_I_work_per_s": i,
        "measured_tau_s": tau,
        "sampled_recovery_Y_s": y,
        "candidate_C_inverse_s": b / (i * tau),
        "last_pre_end_backlog": last["queued"] + last["active"],
        "last_pre_end_observed_ns": last["observed_ns"],
        "injection_end_ns": end,
        "first_post_end_observed_ns": first_post["observed_ns"],
        "replay": replay,
        "measurement_scope": "hosted software FIFO; NOT physical-law validation",
        "file_sha256": {name: sha256(folder / name) for name in ROLE_FILENAMES},
    }


def run_trial(ctx: mp.context.BaseContext, root: Path, spec: dict) -> dict:
    folder = root / spec["trial_id"]
    if folder.exists():
        raise ValueError("No preexisting trial directory may be overwritten")
    folder.mkdir(parents=True, exist_ok=False)
    port = pick_local_port()
    server = ctx.Process(target=serve_p02, args=(port, folder / "service-actions.jsonl"))
    server.start()
    try:
        await_service(port, server)
        calib = ctx.Process(target=calibrate_p02, args=(port, folder / "calibration.json"))
        calib.start()
        join_role(calib, 12, "pretrial capacity calibration")
        await_empty(port, 8)
        monitor = ctx.Process(
            target=probe_p02,
            args=(port, folder / "injector.json", folder / "monitor.json",
                  folder / "monitor-samples.jsonl"),
        )
        controller = ctx.Process(
            target=control,
            args=(port, folder / "injector-onset.json",
                  folder / "controller.json", spec["lag_ms"]),
        )
        injector = ctx.Process(
            target=inject,
            args=(port, folder / "injector-onset.json", folder / "injector.json",
                  spec["work_units"]),
        )
        monitor.start()
        controller.start()
        time.sleep(0.09)
        injector.start()
        join_role(injector, 9, "variable-load injector")
        join_role(controller, 9, "scheduled-action controller")
        join_role(monitor, 13, "sampled independent health observer")
        return audit_trial(folder, spec)
    finally:
        if server.is_alive():
            server.terminate()
        server.join(timeout=4)


def acquire(split: str, root: Path) -> dict:
    if root.exists() and any(root.iterdir()):
        raise ValueError("Existing observations may not be overwritten")
    root.mkdir(parents=True, exist_ok=True)
    sha = os.getenv("GITHUB_SHA")
    workflow = os.getenv("GITHUB_RUN_ID")
    if not sha or not workflow:
        raise ValueError("GitHub source commit and run identity required")
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "docs/preregistration/RP-E006-P01.md"
    metadata = {
        "protocol": PROTOCOL,
        "split": split,
        "source_commit": sha,
        "workflow_run_id": workflow,
        "protocol_sha256": sha256(source),
        "trial_seed": SPLIT_SEEDS[split],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hardware_independence": "NOT_ESTABLISHED",
        "physical_law_test": "NOT_PERFORMED",
        "scheduled_trials": cases_for_split(split),
    }
    write_log(root / "provenance.json", metadata)
    completed = []
    ctx = mp.get_context("spawn")
    for spec in metadata["scheduled_trials"]:
        try:
            completed.append(run_trial(ctx, root, spec))
        except (ValueError, RuntimeError, OSError, KeyError, TypeError, AssertionError) as error:
            completed.append({
                "trial_id": spec["trial_id"], "failure":
                f"{type(error).__name__}: {error}",
            })
    result = {
        **metadata, "observations": completed,
        "run_quality": "PASS_ALL_RECORDED" if len(completed) ==
        len(metadata["scheduled_trials"]) and
        all("failure" not in row for row in completed)
        else "STOP_INSTRUMENTATION",
    }
    write_log(root / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=("train", "test"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    outcome = acquire(args.split, args.output)
    print(json.dumps({
        "split": args.split, "decision": outcome["run_quality"],
        "observations": len(outcome["observations"]),
        "failures": [x for x in outcome["observations"] if "failure" in x],
    }, sort_keys=True))
    if outcome["run_quality"] != "PASS_ALL_RECORDED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
