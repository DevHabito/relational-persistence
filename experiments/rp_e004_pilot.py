"""RP-E004-P01: preregistered *instrument feasibility* on one cloud runner.

Four independently launched role processes log events from a single local
HTTP queue service using one OS monotonic clock. No experiment here tests
a universal persistence law, measures external physical systems, or asserts
causal independence of hardware instruments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import queue
import random
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from relational_persistence.measurement_gate import (
    CapacityCalibration,
    ControllerResponse,
    ExternalDisturbance,
    IndependentRecovery,
    MeasurementGateError,
    TrialEvidence,
    validate_evidence,
)

INITIAL_SERVICE_SECONDS = 0.012
ACTION_SERVICE_SECONDS = 0.006
CALIBRATION_REQUESTS = 120
CALIBRATION_WINDOW_SECONDS = 0.5
INJECTION_REQUESTS = 120
INJECTION_SPACING_SECONDS = 0.003
SHAM_SECONDS = 0.36
POLL_SECONDS = 0.025
RECOVERY_DWELL_NS = 500_000_000
FOLLOWUP_SECONDS = 8.0
TRIALS = ("positive-01", "positive-02", "sham-01")
SEED = 20261023


def write_log(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request(port: int, endpoint: str, method: str = "GET") -> dict:
    req = Request(
        f"http://127.0.0.1:{port}{endpoint}",
        data=b"" if method == "POST" else None,
        method=method,
    )
    with urlopen(req, timeout=2) as stream:
        if stream.status != 200:
            raise RuntimeError(f"Service returned {stream.status}")
        return json.load(stream)


def serve(port: int) -> None:
    backlog: queue.Queue[int] = queue.Queue(maxsize=512)
    lock = threading.Lock()
    state = {"active": 0, "completed": 0, "interval": INITIAL_SERVICE_SECONDS}
    running = threading.Event()
    running.set()

    def worker() -> None:
        while running.is_set():
            try:
                backlog.get(timeout=0.03)
            except queue.Empty:
                continue
            with lock:
                state["active"] += 1
                interval = state["interval"]
            try:
                time.sleep(interval)
            finally:
                with lock:
                    state["active"] -= 1
                    state["completed"] += 1
                backlog.task_done()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            return

        def respond(self, body: dict, status: int = 200) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path != "/status":
                self.respond({"error": "not_found"}, 404)
                return
            with lock:
                snapshot = dict(state)
            snapshot["queued"] = backlog.qsize()
            self.respond(snapshot)

        def do_POST(self) -> None:
            if self.path == "/work":
                try:
                    backlog.put_nowait(1)
                except queue.Full:
                    self.respond({"accepted": False}, 503)
                    return
                self.respond({"accepted": True})
            elif self.path == "/action":
                with lock:
                    state["interval"] = ACTION_SERVICE_SECONDS
                self.respond({"changed": True})
            else:
                self.respond({"error": "not_found"}, 404)

    thread = threading.Thread(target=worker, name="queue-worker", daemon=True)
    thread.start()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever(poll_interval=0.05)
    finally:
        running.clear()
        server.server_close()


def pick_local_port() -> int:
    with socket.socket() as stream:
        stream.bind(("127.0.0.1", 0))
        return int(stream.getsockname()[1])


def await_service(port: int, process: mp.Process) -> None:
    start = time.monotonic()
    while time.monotonic() - start < 5:
        if not process.is_alive():
            raise RuntimeError(f"Service exited early: {process.exitcode}")
        try:
            request(port, "/status")
            return
        except (URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(0.03)
    raise RuntimeError("Local service did not start within five seconds")


def await_empty(port: int, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        state = request(port, "/status")
        if state["queued"] == 0 and state["active"] == 0:
            return
        time.sleep(0.025)
    raise RuntimeError("Service did not fully drain after calibration")


def calibrate(port: int, path: Path) -> None:
    for _ in range(CALIBRATION_REQUESTS):
        result = request(port, "/work", "POST")
        if not result.get("accepted"):
            raise RuntimeError("Calibration work queue rejected a task")
    before = request(port, "/status")
    start = time.monotonic_ns()
    time.sleep(CALIBRATION_WINDOW_SECONDS)
    end = time.monotonic_ns()
    after = request(port, "/status")
    if before["queued"] <= 0 or after["queued"] <= 0:
        raise RuntimeError("Calibration was not demonstrably saturated")
    completed = after["completed"] - before["completed"]
    if completed <= 0:
        raise RuntimeError("No completed calibration work")
    write_log(path, {
        "role": "calibration", "pid": os.getpid(),
        "logger_id": f"calibrator-{os.getpid()}",
        "start_ns": start, "end_ns": end,
        "completed_work_units": completed,
        "queue_before": before["queued"], "queue_after": after["queued"],
        "saturation_evidence": "positive-queue-at-both-sampled-boundaries",
    })


def inject(port: int, path: Path, positive: bool) -> None:
    start = time.monotonic_ns()
    count = 0
    if positive:
        for _ in range(INJECTION_REQUESTS):
            result = request(port, "/work", "POST")
            if result.get("accepted"):
                count += 1
            time.sleep(INJECTION_SPACING_SECONDS)
    else:
        time.sleep(SHAM_SECONDS)
    end = time.monotonic_ns()
    write_log(path, {
        "role": "injector", "pid": os.getpid(),
        "logger_id": f"injector-{os.getpid()}",
        "onset_ns": start, "end_ns": end,
        "successfully_delivered_work_units": count,
        "requested_work_units": INJECTION_REQUESTS if positive else 0,
        "sham": not positive,
    })


def control(port: int, stop: mp.Event, path: Path) -> None:
    action_ns = None
    observed_threshold = None
    deadline = time.monotonic() + FOLLOWUP_SECONDS + 3
    while not stop.is_set() and time.monotonic() < deadline:
        snapshot = request(port, "/status")
        if snapshot["queued"] > 5:
            reply = request(port, "/action", "POST")
            if reply.get("changed") is True:
                action_ns = time.monotonic_ns()
                observed_threshold = snapshot["queued"]
                break
        time.sleep(POLL_SECONDS)
    write_log(path, {
        "role": "controller", "pid": os.getpid(),
        "logger_id": f"controller-{os.getpid()}",
        "action_ns": action_ns, "observed_queue_when_triggered": observed_threshold,
        "action": "requested_worker_interval_6ms" if action_ns is not None else None,
    })


def sustained_idle_start(
    readings: list[tuple[int, bool]], onset_ns: int, dwell_ns: int,
) -> int | None:
    """Confirm an uninterrupted observed idle period after the logged end."""
    start = None
    last = None
    for timestamp, idle in readings:
        if last is not None and timestamp <= last:
            raise ValueError("Nonmonotonic monitor observation timestamps")
        last = timestamp
        if timestamp < onset_ns:
            continue
        if not idle:
            start = None
        elif start is None:
            start = timestamp
        elif timestamp - start >= dwell_ns:
            return start
    return None


def monitor(port: int, injection_path: Path, path: Path) -> None:
    readings: list[tuple[int, bool]] = []
    event_end = None
    deadline = time.monotonic() + FOLLOWUP_SECONDS + 4
    recovery_at = None
    completed_at = None
    while time.monotonic() < deadline:
        state = request(port, "/status")
        observed = time.monotonic_ns()
        readings.append((observed, state["queued"] == 0 and state["active"] == 0))
        if event_end is None and injection_path.exists():
            event_end = int(json.loads(injection_path.read_text())["end_ns"])
            deadline = min(deadline, time.monotonic() + FOLLOWUP_SECONDS)
        if event_end is not None:
            recovery_at = sustained_idle_start(readings, event_end, RECOVERY_DWELL_NS)
            if recovery_at is not None:
                completed_at = time.monotonic_ns()
                break
        time.sleep(POLL_SECONDS)
    if completed_at is None:
        completed_at = time.monotonic_ns()
    write_log(path, {
        "role": "monitor", "pid": os.getpid(),
        "logger_id": f"monitor-{os.getpid()}",
        "observation_end_ns": completed_at,
        "recovered_at_ns": recovery_at,
        "sustained_window_ns": RECOVERY_DWELL_NS,
        "logged_injection_end_ns": event_end,
        "samples": len(readings),
        "probe_period_requested_ms": POLL_SECONDS * 1000,
    })


def join_role(process: mp.Process, timeout: float, role: str) -> None:
    process.join(timeout=timeout)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
        raise RuntimeError(f"{role} exceeded its fixed timeout")
    if process.exitcode != 0:
        raise RuntimeError(f"{role} exited with code {process.exitcode}")


def summarize_trial(folder: Path, positive: bool, criterion_hash: str, resolution_ns: int) -> dict:
    logs = {}
    for role in ("calibration", "injector", "controller", "monitor"):
        p = folder / f"{role}.json"
        logs[role] = json.loads(p.read_text(encoding="utf-8"))
    calibration, injection = logs["calibration"], logs["injector"]
    controller, monitored = logs["controller"], logs["monitor"]
    result = {
        "trial_id": folder.name, "positive": positive,
        "pid_by_role": {r: e["pid"] for r, e in logs.items()},
        "role_sha256": {r: sha256(folder / f"{r}.json") for r in logs},
        "controller_action_observed": controller["action_ns"] is not None,
        "monitor_recovered": monitored["recovered_at_ns"] is not None,
        "injected_completed_requests": injection["successfully_delivered_work_units"],
        "label": "controlled_software_instrumentation_only",
    }
    if not positive:
        result["candidate_index_inverse_seconds"] = None
        result["schema_verdict"] = (
            "SHAM_UNDEFINED_INDEX"
            if injection["successfully_delivered_work_units"] == 0
            and controller["action_ns"] is None
            else "STOP_SHAM_INTEGRITY"
        )
        return result

    try:
        record = TrialEvidence(
            system_id="github-actions-single-runner-queue",
            trial_id=folder.name,
            clock_domain="common_monotonic_ns",
            clock_resolution_ns=resolution_ns,
            work_unit="HTTP_work_unit",
            calibration=CapacityCalibration(
                start_ns=calibration["start_ns"],
                end_ns=calibration["end_ns"],
                completed_work_units=calibration["completed_work_units"],
                saturated_calibration_evidence=calibration["saturation_evidence"],
                logger_id=calibration["logger_id"],
            ),
            disturbance=ExternalDisturbance(
                onset_ns=injection["onset_ns"],
                end_ns=injection["end_ns"],
                delivered_excess_work_units=injection["successfully_delivered_work_units"],
                logger_id=injection["logger_id"],
            ),
            controller=ControllerResponse(
                action_ns=controller["action_ns"],
                logger_id=controller["logger_id"],
            ),
            recovery=IndependentRecovery(
                observation_end_ns=monitored["observation_end_ns"],
                recovered_at_ns=monitored["recovered_at_ns"],
                sustained_window_ns=monitored["sustained_window_ns"],
                frozen_criterion_sha256=criterion_hash,
                logger_id=monitored["logger_id"],
            ),
        )
        result["measurement"] = validate_evidence(record)
        result["schema_verdict"] = (
            "STRUCTURALLY_ADMISSIBLE"
            if monitored["recovered_at_ns"] is not None
            else "STOP_CENSORED_RECOVERY"
        )
    except (MeasurementGateError, TypeError, ValueError) as exc:
        result["schema_verdict"] = "STOP_STRUCTURAL_GATE"
        result["gate_failure"] = str(exc)
    return result


def run_trial(ctx: mp.context.BaseContext, folder: Path, positive: bool,
              criterion_hash: str, resolution_ns: int) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    port = pick_local_port()
    server = ctx.Process(target=serve, args=(port,), name="local-fifo-service")
    server.start()
    try:
        await_service(port, server)
        calibrator = ctx.Process(
            target=calibrate, args=(port, folder / "calibration.json"),
            name="independent-calibrator",
        )
        calibrator.start()
        join_role(calibrator, 9, "calibrator")
        await_empty(port, 8)
        stop = ctx.Event()
        ctl = ctx.Process(
            target=control, args=(port, stop, folder / "controller.json"),
            name="independent-controller",
        )
        health = ctx.Process(
            target=monitor,
            args=(port, folder / "injector.json", folder / "monitor.json"),
            name="independent-health-monitor",
        )
        ctl.start()
        health.start()
        time.sleep(0.12)
        generator = ctx.Process(
            target=inject, args=(port, folder / "injector.json", positive),
            name="independent-load-injector",
        )
        generator.start()
        join_role(generator, 6, "injector")
        join_role(health, 13, "health monitor")
        stop.set()
        join_role(ctl, 4, "controller")
        return summarize_trial(folder, positive, criterion_hash, resolution_ns)
    finally:
        if server.is_alive():
            server.terminate()
        server.join(timeout=3)


def evaluate_feasibility(results: list[dict]) -> str:
    if len(results) != 3:
        return "STOP_INSTRUMENTATION_UNRELIABLE"
    positive = [r for r in results if r.get("positive")]
    sham = [r for r in results if not r.get("positive")]
    if (len(positive) == 2 and len(sham) == 1
        and all(r.get("schema_verdict") == "STRUCTURALLY_ADMISSIBLE" for r in positive)
        and sham[0].get("schema_verdict") == "SHAM_UNDEFINED_INDEX"):
        return "PROCEED_TO_SEPARATE_STUDY_DESIGN"
    return "STOP_INSTRUMENTATION_UNRELIABLE"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("rp-e004-observed"))
    args = parser.parse_args()
    ctx = mp.get_context("spawn")
    folder = args.output
    folder.mkdir(parents=True, exist_ok=True)
    criterion = Path(__file__).resolve().parents[1] / "docs/preregistration/RP-E004-P01.md"
    criterion_hash = sha256(criterion)
    resolution_ns = max(1, int(time.get_clock_info("monotonic").resolution * 1e9))
    schedule = list(TRIALS)
    random.Random(SEED).shuffle(schedule)
    results: list[dict] = []
    for trial_id in schedule:
        positive = trial_id.startswith("positive")
        try:
            results.append(run_trial(
                ctx, folder / trial_id, positive, criterion_hash, resolution_ns
            ))
        except (RuntimeError, OSError, ValueError, KeyError) as exc:
            results.append({
                "trial_id": trial_id, "positive": positive,
                "schema_verdict": "STOP_PROCESS_OR_RECORD_ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            })
    summary = {
        "protocol": "RP-E004-P01",
        "registration_sha256": criterion_hash,
        "git_sha": os.environ.get("GITHUB_SHA", "not_supplied"),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "os": platform.platform(),
        "monotonic_resolution_ns": resolution_ns,
        "schedule_seed": SEED,
        "actual_order": schedule,
        "trials": results,
        "decision": evaluate_feasibility(results),
        "scientific_claim": "INSTRUMENT_FEASIBILITY_ONLY",
        "physical_law_test": "NOT_PERFORMED",
        "causal_identification": "NOT_ESTABLISHED",
        "cross_machine_replication": "NOT_PERFORMED",
    }
    write_log(folder / "summary.json", summary)
    print(json.dumps({
        "protocol": summary["protocol"], "decision": summary["decision"],
        "verdicts": [r["schema_verdict"] for r in results],
        "output": str(folder / "summary.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
