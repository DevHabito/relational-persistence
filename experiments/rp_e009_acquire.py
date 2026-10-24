"""Prospective RP-E009 observations on an executable asyncio TCP queue.

No prior RP-E006/007/008 service code or experimental observations are
used. Every trial launches a fresh separate server OS process.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import multiprocessing as mp
import os
import platform
import random
import socket
import time
from pathlib import Path

from experiments.rp_e009_tcp_service import run_server

PROTOCOL = "RP-E009-P01"
TARGETS = (40, 70, 100)
ARRIVAL_MODES = ("uniform", "early_burst", "late_burst")
SPLIT_SEEDS = {"diagnostic": 20261028, "holdout": 20261029}
ORIGINAL_FILES = (
    "calibration.json", "controller.json", "injector.json",
    "monitor-samples.jsonl", "service-events.jsonl",
    "feature-snapshot.json", "configuration.json",
)
HEALTH_INTERVAL_SECONDS = 0.025
HEALTH_FOLLOWUP_SECONDS = 1.1
SERVER_START_SECONDS = 6.0


def write_json(path: Path, data: object) -> None:
    if path.exists():
        raise ValueError(f"Refusing to overwrite original evidence: {path}")
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registered_trials(split: str) -> list[dict]:
    if split not in SPLIT_SEEDS:
        raise ValueError("Only the prospective two blocks are registered")
    result = [
        {"trial_id": f"{split}-{n:03d}-{mode}",
         "work_units": n, "arrival_mode": mode}
        for n in TARGETS for mode in ARRIVAL_MODES
    ]
    random.Random(SPLIT_SEEDS[split]).shuffle(result)
    return result


def pick_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


async def rpc(port: int, operation: str) -> tuple[dict, int]:
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1", port), timeout=2
    )
    try:
        writer.write(json.dumps({"op": operation}).encode("utf-8") + b"\n")
        await asyncio.wait_for(writer.drain(), timeout=2)
        raw = await asyncio.wait_for(reader.readline(), timeout=2)
        observed = time.monotonic_ns()
        response = json.loads(raw)
        if not isinstance(response, dict) or "error" in response:
            raise RuntimeError(f"Service rejected {operation}: {response}")
        return response, observed
    finally:
        writer.close()
        await writer.wait_closed()


async def start_ready(port: int) -> None:
    stop = time.monotonic() + SERVER_START_SECONDS
    while time.monotonic() < stop:
        try:
            r, _ = await rpc(port, "ping")
            if r == {"ready": True}:
                return
        except (OSError, asyncio.TimeoutError, RuntimeError):
            await asyncio.sleep(.02)
    raise RuntimeError("Fresh independent TCP service did not become ready")


async def calibrate(port: int) -> dict:
    start = time.monotonic_ns()
    for j in range(1, 61):
        reply, _ = await rpc(port, "enqueue")
        if reply.get("accepted") is not True or reply.get("job") != j:
            raise ValueError("Incomplete calibration task sequence")
    until = time.monotonic() + 6
    while time.monotonic() < until:
        row, received = await rpc(port, "health")
        if (row["accepted"] == 60 and row["completed"] == 60
                and row["queued"] == 0 and row["active"] == 0):
            if received <= start:
                raise ValueError("Invalid calibration time order")
            return {
                "first_enqueue_sent_ns": start,
                "last_completed_observed_ns": received,
                "accepted": 60, "completed": 60,
                "prechange_duration_cycle_ms": [8, 12, 16],
                "observed_B_work_per_second": 60e9 / (received - start),
            }
        await asyncio.sleep(.025)
    raise RuntimeError("Calibration service failed to drain")


def planned_spacing_ms(mode: str, position: int, work_units: int) -> int:
    if mode not in ARRIVAL_MODES or work_units not in TARGETS:
        raise ValueError("Unregistered workload cell")
    if mode == "uniform":
        return 3
    first_half = position < work_units // 2
    if mode == "early_burst":
        return 1 if first_half else 5
    return 5 if first_half else 1


async def monitor(port: int, end_holder: dict, output: Path) -> int:
    samples = []
    deadline = time.monotonic() + 9
    while time.monotonic() < deadline:
        sample, observed = await rpc(port, "health")
        if sample["phase"] != "experiment":
            raise ValueError("Health recorded in calibration phase")
        samples.append({
            "observed_ns": observed,
            "server_snapshot_ns": sample["server_snapshot_ns"],
            "queued": sample["queued"],
            "active": sample["active"],
            "accepted": sample["accepted"],
            "completed": sample["completed"],
        })
        end = end_holder.get("end_ns")
        if end is not None and observed - end >= int(
            HEALTH_FOLLOWUP_SECONDS * 1e9
        ):
            break
        await asyncio.sleep(HEALTH_INTERVAL_SECONDS)
    else:
        raise RuntimeError("Insufficient monitor followup")
    if output.exists():
        raise ValueError("Refusing existing health trace")
    with output.open("w", encoding="utf-8") as stream:
        for entry in samples:
            stream.write(json.dumps(entry, sort_keys=True) + "\n")
    return len(samples)


async def inject(port: int, spec: dict, end_holder: dict) -> dict:
    sends = []
    acknowledgements = []
    first_send_ns = None
    for position in range(spec["work_units"]):
        send_ns = time.monotonic_ns()
        if first_send_ns is None:
            first_send_ns = send_ns
        response, ack_ns = await rpc(port, "enqueue")
        if (response.get("accepted") is not True
                or response.get("job") != position + 1):
            raise ValueError("Incomplete or reordered intervention work")
        sends.append(send_ns)
        acknowledgements.append(ack_ns)
        await asyncio.sleep(
            planned_spacing_ms(spec["arrival_mode"],
                               position, spec["work_units"]) / 1000
        )
    end_ns = acknowledgements[-1]
    end_holder["end_ns"] = end_ns
    return {
        "work_units": spec["work_units"],
        "arrival_mode": spec["arrival_mode"],
        "accepted": len(sends),
        "first_enqueue_sent_ns": first_send_ns,
        "end_ns": end_ns,
        "accepted_send_timestamps_ns": sends,
        "acknowledged_timestamps_ns": acknowledgements,
        "spacing_schedule_is_minimum_not_actual": True,
    }


async def live_trial(port: int, folder: Path, spec: dict) -> dict:
    await start_ready(port)
    calibration = await calibrate(port)
    write_json(folder / "calibration.json", calibration)
    reset, _ = await rpc(port, "reset")
    if reset.get("reset") is not True:
        raise ValueError("Incomplete calibration reset")
    changed, acknowledged = await rpc(port, "accelerate")
    if changed.get("changed") is not True:
        raise ValueError("Service speed change absent")
    controller = {
        "actual_service_applied_ns": changed["service_applied_ns"],
        "acknowledged_ns": acknowledged,
        "speed_factor": 2, "before_intervention": True,
    }
    write_json(folder / "controller.json", controller)
    await asyncio.sleep(.065)
    flag: dict = {}
    watcher = asyncio.create_task(
        monitor(port, flag, folder / "monitor-samples.jsonl")
    )
    await asyncio.sleep(.05)
    try:
        injection = await inject(port, spec, flag)
        write_json(folder / "injector.json", injection)
        recorded = await watcher
    finally:
        if not watcher.done():
            watcher.cancel()
            try:
                await watcher
            except asyncio.CancelledError:
                pass
    if recorded < 10:
        raise ValueError("Too few original monitor observations")
    # The frozen pair snapshot must originate from samples no later
    # than the end marker; this is checked again by an independent job.
    from experiments.rp_e007_temporal_backlog import pre_end_pair
    samples = [
        json.loads(line) for line in
        (folder / "monitor-samples.jsonl").read_text().splitlines()
    ]
    previous, latest = pre_end_pair(samples, injection["end_ns"])
    snapshot = {
        "previous_observed_ns": previous["observed_ns"],
        "latest_observed_ns": latest["observed_ns"],
        "previous_queued_and_active": previous["queued"] + previous["active"],
        "latest_queued_and_active": latest["queued"] + latest["active"],
        "source": "two original TCP health responses prior to injector end",
    }
    write_json(folder / "feature-snapshot.json", snapshot)
    return {
        "trial_id": spec["trial_id"], "monitor_samples": recorded,
        "observed_B_work_per_second": calibration["observed_B_work_per_second"],
        "accepted_intervention_work": injection["accepted"],
    }


async def trial(folder: Path, spec: dict) -> dict:
    if folder.exists():
        raise ValueError("Existing trial record must not be replaced")
    folder.mkdir(parents=True, exist_ok=False)
    write_json(folder / "configuration.json", spec)
    port = pick_port()
    process = mp.get_context("spawn").Process(
        target=run_server, args=(port, str(folder / "service-events.jsonl"))
    )
    process.start()
    try:
        return await live_trial(port, folder, spec)
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=4)
        if process.exitcode is None:
            process.kill()
            process.join(timeout=2)


def acquire(split: str, folder: Path) -> dict:
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("Original hosted measurements cannot be overwritten")
    source_sha = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not source_sha or not run_id:
        raise ValueError("Original GitHub source commit and workflow ID required")
    folder.mkdir(parents=True, exist_ok=True)
    project = Path(__file__).resolve().parents[1]
    provenance = {
        "protocol": PROTOCOL, "split": split,
        "source_commit": source_sha, "workflow_run_id": run_id,
        "preregistration_sha256": digest(
            project / "docs/preregistration/RP-E009-P01.md"
        ),
        "runtime": platform.python_version(),
        "platform": platform.platform(),
        "trial_order": registered_trials(split),
        "independent_physical_system": "NOT_ESTABLISHED",
        "predictive_scalar_C_test": "NOT_PERFORMED",
    }
    write_json(folder / "provenance.json", provenance)
    completed = []
    for spec in provenance["trial_order"]:
        try:
            observed = asyncio.run(trial(folder / spec["trial_id"], spec))
            observed["file_sha256"] = {
                name: digest(folder / spec["trial_id"] / name)
                for name in ORIGINAL_FILES
            }
            completed.append(observed)
        except (ValueError, OSError, RuntimeError, KeyError, TypeError,
                asyncio.TimeoutError) as error:
            completed.append({
                "trial_id": spec["trial_id"],
                "failure": f"{type(error).__name__}: {error}",
            })
    report = {
        **provenance,
        "original_trials": completed,
        "acquisition_gate": (
            "PASS_ALL_RECORDED" if len(completed) == 9 and
            all("failure" not in x for x in completed)
            else "STOP_TRANSFER_AUDIT"
        ),
    }
    write_json(folder / "summary.json", report)
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=tuple(SPLIT_SEEDS), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = acquire(args.split, args.output)
    print(json.dumps({
        "split": args.split, "status": report["acquisition_gate"],
        "trials": len(report["original_trials"]),
        "failures": [x for x in report["original_trials"] if "failure" in x],
    }, sort_keys=True))
    if report["acquisition_gate"] != "PASS_ALL_RECORDED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
