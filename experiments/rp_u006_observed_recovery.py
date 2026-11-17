"""RP-U006: first prospective, single-host executable recovery measurements.

Exactly 1 calibration, 6 diagnostic and 8 fixed holdout TCP service trials.
The service, monitor and injector/controller have separate source records;
the service and monitor run in separate OS processes. A worker-gate reset
is NOT a physical network edge restoration or independent hardware sensing.
"""
from __future__ import annotations

import argparse
import asyncio
from hashlib import sha256
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import socket
from statistics import median
import time

from experiments import rp_u006_forecast_core as core
from experiments.rp_u006_gated_tcp_service import run_service

PROTOCOL_PATH = Path("docs/preregistration/RP-U006-P01.md")
ADDENDUM_PATH = Path(
    "docs/preregistration/RP-U006-P01-D01-PRE-SOURCE-CALIBRATION-CORRECTION.md"
)
OUTPUT = Path("docs/results/RP-U006-P01-first-run")
SOURCE_COMMIT = "PENDING_FIRST_ORIGINAL_SOURCE_COMMIT"
REQUEST_TIMEOUT_SECONDS = 2.0
STARTUP_DEADLINE_SECONDS = 5.0
DRAIN_DEADLINE_SECONDS = 6.0
FOLLOWUP_SECONDS = 0.15
PRESUBMISSION_MONITOR_SECONDS = 0.06
POST_BATCH_MONITOR_SECONDS = 0.065
ROLE_JOIN_SECONDS = 4.0


def write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise core.InvalidObservation("ORIGINAL_SOURCE_FILE_MUST_NOT_BE_REPLACED")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read_jsonlines(path: Path) -> list[dict]:
    if not path.is_file():
        raise core.InvalidObservation("MISSING_ORIGINAL_ROLE_EVENT_FILE")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows or any(not isinstance(x, dict) for x in rows):
        raise core.InvalidObservation("EMPTY_OR_INVALID_ORIGINAL_ROLE_LOG")
    return rows


def port_available() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


async def rpc(port: int, op: str, *, count: int | None = None) -> tuple[dict, int]:
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1", port),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        request = {"op": op}
        if count is not None:
            request["count"] = count
        writer.write((json.dumps(request) + "\n").encode("utf-8"))
        await asyncio.wait_for(writer.drain(), timeout=REQUEST_TIMEOUT_SECONDS)
        raw = await asyncio.wait_for(reader.readline(), timeout=REQUEST_TIMEOUT_SECONDS)
        receipt = time.monotonic_ns()
        response = json.loads(raw)
        if not isinstance(response, dict) or "error" in response:
            raise core.InvalidObservation(f"ORIGINAL_SERVICE_RPC_REJECTED_{op}")
        return response, receipt
    finally:
        writer.close()
        await writer.wait_closed()


def monitor_rpc(port: int) -> tuple[dict, int]:
    with socket.create_connection(("127.0.0.1", port), timeout=REQUEST_TIMEOUT_SECONDS) as s:
        s.settimeout(REQUEST_TIMEOUT_SECONDS)
        s.sendall(b'{"op":"health"}\n')
        with s.makefile("rb") as file:
            line = file.readline()
        receipt = time.monotonic_ns()
    message = json.loads(line)
    if not isinstance(message, dict) or "error" in message:
        raise core.InvalidObservation("MONITOR_SERVICE_HEALTH_REJECTED")
    return message, receipt


def monitor_process(port: int, path_string: str, stop: mp.synchronize.Event) -> None:
    """Source monitor on its own OS process. Never sends mutating commands."""
    path = Path(path_string)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as out:
            while not stop.is_set():
                state, observed = monitor_rpc(port)
                row = {
                    "observed_ns": observed,
                    "server_snapshot_ns": state["server_snapshot_ns"],
                    "queued": state["queued"],
                    "active": state["active"],
                    "accepted": state["accepted"],
                    "completed": state["completed"],
                    "available": state["available"],
                }
                out.write(json.dumps(row, sort_keys=True) + "\n")
                out.flush()
                time.sleep(core.POLL_SECONDS)
    except Exception as exc:
        # This is diagnostic failure evidence, not an eligible source.
        with (path.parent / "monitor-error.json").open("x", encoding="utf-8") as err:
            err.write(json.dumps({
                "error_type": type(exc).__name__,
                "error_text": str(exc)[:250],
            }, sort_keys=True) + "\n")
        raise


async def ready(port: int) -> None:
    deadline = time.monotonic() + STARTUP_DEADLINE_SECONDS
    while time.monotonic() < deadline:
        try:
            response, _ = await rpc(port, "ping")
            if response == {"ready": True}:
                return
        except (OSError, ConnectionError, asyncio.TimeoutError,
                core.InvalidObservation):
            await asyncio.sleep(.02)
    raise core.InvalidObservation("FRESH_SERVICE_PROCESS_NOT_READY")


def process_cleanup(process: mp.Process) -> None:
    if process.is_alive():
        process.terminate()
    process.join(timeout=ROLE_JOIN_SECONDS)
    if process.is_alive():
        process.kill()
        process.join(timeout=ROLE_JOIN_SECONDS)


async def one_trial(folder: Path, *, block: str, ordinal: int, batch: int,
                    cal_seconds: float | None = None,
                    trained_baseline: float | None = None) -> dict:
    if folder.exists():
        raise core.InvalidObservation("ORIGINAL_TRIAL_DIRECTORY_ALREADY_EXISTS")
    folder.mkdir(parents=True, exist_ok=False)
    config = {"block": block, "ordinal": ordinal, "requested_jobs": batch,
              "service_requested_minimum_seconds": core.DURATION_SECONDS,
              "monitor_requested_poll_seconds": core.POLL_SECONDS,
              "worker_initially_available": False,
              "post_restore_job_arrivals": 0}
    write_new(folder / "configuration.json", config)
    port = port_available()
    ctx = mp.get_context("spawn")
    service = ctx.Process(
        target=run_service, args=(port, str(folder / "service-events.jsonl"))
    )
    stop = ctx.Event()
    monitor = ctx.Process(
        target=monitor_process,
        args=(port, str(folder / "monitor-samples.jsonl"), stop),
    )
    service_started = False
    monitor_started = False
    try:
        service.start()
        service_started = True
        await ready(port)
        monitor.start()
        monitor_started = True
        await asyncio.sleep(PRESUBMISSION_MONITOR_SECONDS)
        if block == "calibration":
            enabled, receipt = await rpc(port, "enable")
            # Service gate precedes calibration tasks as preregistered.
            enable_ns = enabled["server_enable_ns"]
            response, _ = await rpc(port, "batch", count=batch)
        else:
            response, _ = await rpc(port, "batch", count=batch)
            if response.get("accepted") != batch or response.get("last_id") != batch:
                raise core.InvalidObservation("UNMATCHED_SUBMISSION_ACKNOWLEDGMENTS")
            pre_enable, _ = await rpc(port, "health")
            if (pre_enable["accepted"] != batch or pre_enable["completed"] != 0
                    or pre_enable["queued"] + pre_enable["active"] != batch
                    or pre_enable["available"] is not False):
                raise core.InvalidObservation("PRE_REPAIR_BACKLOG_FEATURE_INVALID")
            await asyncio.sleep(POST_BATCH_MONITOR_SECONDS)
            enabled, receipt = await rpc(port, "enable")
            enable_ns = enabled["server_enable_ns"]
        if (enabled.get("enabled") is not True
                or type(enable_ns) is not int or receipt < enable_ns):
            raise core.InvalidObservation("ORIGINAL_ENABLE_ACKNOWLEDGMENT_INVALID")
        if response.get("accepted") != batch or response.get("last_id") != batch:
            raise core.InvalidObservation("INCOMPLETE_BATCH_ACKNOWLEDGMENT")
        prediction_created_ns = time.monotonic_ns()
        predictions = None
        if block == "holdout":
            if cal_seconds is None or trained_baseline is None:
                raise core.InvalidObservation("HOLDOUT_FEATURES_NOT_FROZEN")
            # Both numbers exist before the service is allowed to finish a job.
            predictions = core.frozen_forecasts(
                [trained_baseline] * len(core.DIAGNOSTIC_LOADS),
                cal_seconds, batch,
            )
            if prediction_created_ns <= enable_ns:
                raise core.InvalidObservation("PRE_OUTCOME_PREDICTION_CLOCK_ERROR")
        write_new(folder / "controller-injector.json", {
            "block": block,
            "ordinal": ordinal,
            "batch_ids": list(range(1, batch + 1)),
            "batch_acknowledged": response,
            "enabled_acknowledged": enabled,
            "controller_enable_ack_ns": receipt,
            "prediction_created_ns": prediction_created_ns,
            "predictions": predictions,
            "pre_enable_outstanding": batch if block != "calibration" else None,
        })
        deadline = time.monotonic() + DRAIN_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            state, _ = await rpc(port, "health")
            if (state["accepted"] == batch and state["completed"] == batch
                    and state["queued"] == state["active"] == 0):
                break
            await asyncio.sleep(.012)
        else:
            raise core.InvalidObservation("SOURCE_SERVICE_DID_NOT_DRAIN")
        await asyncio.sleep(FOLLOWUP_SECONDS)
        stop.set()
        monitor.join(timeout=ROLE_JOIN_SECONDS)
        if monitor.is_alive() or monitor.exitcode != 0:
            raise core.InvalidObservation("INDEPENDENT_MONITOR_PROCESS_FAILED")
        shut, _ = await rpc(port, "shutdown")
        if shut.get("shutdown") is not True:
            raise core.InvalidObservation("SERVICE_REFUSED_CLEAN_SHUTDOWN")
        service.join(timeout=ROLE_JOIN_SECONDS)
        if service.is_alive() or service.exitcode != 0:
            raise core.InvalidObservation("SERVICE_DID_NOT_EXIT_CLEANLY")
        events = read_jsonlines(folder / "service-events.jsonl")
        samples = read_jsonlines(folder / "monitor-samples.jsonl")
        event_audit = core.validate_service_events(
            events, batch, calibration=block == "calibration"
        )
        if event_audit["server_enable_ns"] != enable_ns:
            raise core.InvalidObservation("MISMATCHED_SOURCE_ENABLE_TIMESTAMP")
        if block != "calibration":
            positive_pre = [
                s for s in samples
                if s["server_snapshot_ns"] < enable_ns
                and s["queued"] + s["active"] == batch
                and s["completed"] == 0
                and s["available"] is False
            ]
            if not positive_pre:
                raise core.InvalidObservation("PRE_ENABLE_MONITOR_MISSED_BACKLOG")
        recovery = core.recovery_elapsed(samples, enable_ns, batch)
        if predictions and prediction_created_ns >= (
            enable_ns + int(recovery * 1e9)
        ):
            raise core.InvalidObservation("HOLDOUT_PREDICTION_AFTER_OUTCOME")
        record = {
            "block": block, "ordinal": ordinal,
            "requested_jobs": batch, "source_trial_valid": True,
            "server_enable_ns": enable_ns,
            "pre_enable_outstanding": batch if block != "calibration" else None,
            "recovery_seconds": recovery if block != "calibration" else None,
            "predictions": predictions,
            "event_log_sha256": sha(folder / "service-events.jsonl"),
            "monitor_log_sha256": sha(folder / "monitor-samples.jsonl"),
            "controller_log_sha256": sha(folder / "controller-injector.json"),
            "original_event_count": len(events),
            "original_monitor_samples": len(samples),
            "independent_job_identity_audit": event_audit,
            "server_process_exit_code": service.exitcode,
            "monitor_process_exit_code": monitor.exitcode,
        }
        if block == "calibration":
            record["calibrated_service_interval_seconds"] = (
                core.calibration_interval(events)
            )
        write_new(folder / "trial-summary.json", record)
        return record
    finally:
        stop.set()
        if monitor_started:
            process_cleanup(monitor)
        if service_started:
            process_cleanup(service)


def run_original(folder: Path) -> dict:
    if folder.exists():
        raise core.InvalidObservation("ORIGINAL_FIRST_RUN_DIRECTORY_EXISTS")
    folder.mkdir(parents=True, exist_ok=False)
    if (not os.environ.get("GITHUB_SHA")
            or not os.environ.get("GITHUB_RUN_ID")):
        raise core.InvalidObservation("HOSTED_WORKFLOW_ID_AND_SOURCE_REQUIRED")
    provenance = {
        "study": core.PROTOCOL,
        "protocol_commit": core.PROTOCOL_ONLY_SHA,
        "pre_source_correction_commit": core.CALIBRATION_CORRECTION_SHA,
        "source_commit": os.environ["GITHUB_SHA"],
        "first_workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "protocol_sha256": sha(PROTOCOL_PATH),
        "addendum_sha256": sha(ADDENDUM_PATH),
        "fixed_calibration_jobs": 12,
        "diagnostic_order": list(core.DIAGNOSTIC_LOADS),
        "holdout_order": list(core.HOLDOUT_LOADS),
        "software_only_one_host": True,
        "actual_network_edge_restoration_performed": False,
    }
    write_new(folder / "provenance.json", provenance)
    record = {**provenance, "calibration": None,
              "diagnostic": [], "heldout": [],
              "original_trials_valid": False,
              "status": "RP_U006_MEASUREMENT_INVALID"}
    failure = None
    try:
        cal = asyncio.run(one_trial(
            folder / "calibration", block="calibration", ordinal=0, batch=12,
        ))
        record["calibration"] = cal
        interval = cal["calibrated_service_interval_seconds"]
        for i, n in enumerate(core.DIAGNOSTIC_LOADS, start=1):
            observation = asyncio.run(one_trial(
                folder / f"diagnostic-{i:02d}", block="diagnostic",
                ordinal=i, batch=n,
            ))
            record["diagnostic"].append(observation)
        training_targets = [x["recovery_seconds"] for x in record["diagnostic"]]
        availability_baseline = float(median(training_targets))
        record["training_median_recovery_seconds"] = availability_baseline
        record["calibrated_completion_interval_seconds"] = interval
        # From this point on, no diagnostic/calibration source is edited.
        for i, n in enumerate(core.HOLDOUT_LOADS, start=1):
            observation = asyncio.run(one_trial(
                folder / f"holdout-{i:02d}", block="holdout",
                ordinal=i, batch=n, cal_seconds=interval,
                trained_baseline=availability_baseline,
            ))
            record["heldout"].append(observation)
        record["original_trials_valid"] = True
        decision = core.evaluate_original(record)
        record.update(decision)
    except (OSError, RuntimeError, ValueError, TypeError,
            KeyError, TimeoutError, asyncio.TimeoutError) as exc:
        failure = {"kind": type(exc).__name__,
                   "code": str(exc)[:250],
                   "completed_diagnostic": len(record["diagnostic"]),
                   "completed_holdout": len(record["heldout"])}
        record["failure"] = failure
        record["status"] = "RP_U006_MEASUREMENT_INVALID"
    write_new(folder / "summary.json", record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = run_original(args.output)
    print(json.dumps({
        "status": report["status"],
        "valid": report["original_trials_valid"],
        "source_commit": report["source_commit"],
        "diagnostic_trials": len(report["diagnostic"]),
        "heldout_trials": len(report["heldout"]),
        "failure": report.get("failure"),
        "availability_only_MAE_seconds": report.get("availability_only_MAE_seconds"),
        "outstanding_aware_MAE_seconds": report.get("outstanding_aware_MAE_seconds"),
        "state_forecast_strict_wins_of_eight": report.get("state_forecast_strict_wins_of_eight"),
    }, indent=2, sort_keys=True))
    if report["status"] == "RP_U006_MEASUREMENT_INVALID":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
