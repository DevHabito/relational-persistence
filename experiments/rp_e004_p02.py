"""RP-E004-P02: registered single-host instrumentation audit, not a physical-law test.

P01 remains immutable. P02 stores every health probe and the service's
application timestamp. Its replay algorithm uses only injector and probe
records, never B, I or controller latency.
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
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from experiments.rp_e004_pilot import (
    ACTION_SERVICE_SECONDS, FOLLOWUP_SECONDS, INITIAL_SERVICE_SECONDS,
    POLL_SECONDS, RECOVERY_DWELL_NS, await_empty, await_service,
    join_role, pick_local_port, request, sha256, write_log,
)
from relational_persistence.measurement_gate import (
    CapacityCalibration, ControllerResponse, ExternalDisturbance,
    IndependentRecovery, MeasurementGateError, TrialEvidence,
    validate_evidence,
)

TRIAL_NAMES = (
    "positive-controlled-01", "positive-controlled-02",
    "positive-disabled-01", "sham-01",
)
SEED = 20261024
GAP_LIMIT_NS = 150_000_000
CALIBRATION_TASKS = 180
CALIBRATION_WINDOWS = 3
CALIBRATION_POLL_SECONDS = 0.25
CALIBRATION_RATE_VARIATION = 0.25
SPARSE_TASKS = 12
SPARSE_SPACING_SECONDS = 0.04
INJECTION_TASKS = 120
INJECTION_SPACING_SECONDS = 0.003
SHAM_SECONDS = 0.36


def log_jsonline(path: Path, data: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()


def read_jsonlines(path: Path) -> list[dict]:
    result = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"Invalid JSONL row {number}") from exc
            if not isinstance(obj, dict):
                raise ValueError("Expected object per probe line")
            result.append(obj)
    return result


def serve_p02(port: int, actions: Path) -> None:
    actions.parent.mkdir(parents=True, exist_ok=True)
    actions.touch()
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
            pass

        def reply(self, body: dict, status: int = 200) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path != "/status":
                self.reply({"error": "not_found"}, 404)
                return
            with lock:
                snapshot = {**state, "server_snapshot_ns": time.monotonic_ns()}
                snapshot["queued"] = backlog.qsize()
            self.reply(snapshot)

        def do_POST(self) -> None:
            if self.path == "/work":
                try:
                    backlog.put_nowait(1)
                except queue.Full:
                    self.reply({"accepted": False}, 503)
                    return
                self.reply({"accepted": True})
            elif self.path == "/action":
                with lock:
                    state["interval"] = ACTION_SERVICE_SECONDS
                    applied = time.monotonic_ns()
                    log_jsonline(actions, {
                        "server_applied_ns": applied,
                        "server_pid": os.getpid(),
                        "requested_interval_seconds": ACTION_SERVICE_SECONDS,
                    })
                self.reply({"changed": True, "server_applied_ns": applied})
            else:
                self.reply({"error": "not_found"}, 404)

    threading.Thread(target=worker, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever(poll_interval=0.05)
    finally:
        running.clear()
        server.server_close()


def calibrate_p02(port: int, path: Path) -> None:
    sparse_before = request(port, "/status")["completed"]
    sparse_start = time.monotonic_ns()
    for _ in range(SPARSE_TASKS):
        if not request(port, "/work", "POST").get("accepted"):
            raise RuntimeError("Sparse calibration work rejected")
        time.sleep(SPARSE_SPACING_SECONDS)
    sparse_end = time.monotonic_ns()
    sparse_completed = request(port, "/status")["completed"] - sparse_before
    if sparse_completed != SPARSE_TASKS:
        raise RuntimeError("Sparse calibration did not complete all tasks")
    if request(port, "/status")["queued"] != 0:
        raise RuntimeError("Sparse-calibration queue failed to drain")
    for _ in range(CALIBRATION_TASKS):
        if not request(port, "/work", "POST").get("accepted"):
            raise RuntimeError("Saturated calibration work rejected")
    windows = []
    prior = request(port, "/status")
    prior_time = time.monotonic_ns()
    for _ in range(CALIBRATION_WINDOWS):
        time.sleep(CALIBRATION_POLL_SECONDS)
        current = request(port, "/status")
        current_time = time.monotonic_ns()
        windows.append({
            "start_ns": prior_time, "end_ns": current_time,
            "completed_delta": current["completed"] - prior["completed"],
            "queued_start": prior["queued"], "queued_end": current["queued"],
            "active_start": prior["active"], "active_end": current["active"],
            "start_service_snapshot_ns": prior["server_snapshot_ns"],
            "end_service_snapshot_ns": current["server_snapshot_ns"],
        })
        prior, prior_time = current, current_time
    write_log(path, {
        "role": "calibration", "logger_id": f"calibrator-{os.getpid()}",
        "pid": os.getpid(), "windows": windows,
        "sparse_probe": {
            "start_ns": sparse_start, "end_ns": sparse_end,
            "completed": sparse_completed, "nominal_submissions": SPARSE_TASKS,
        },
    })


def inject_p02(port: int, path: Path, positive: bool) -> None:
    onset = time.monotonic_ns()
    delivered = 0
    if positive:
        for _ in range(INJECTION_TASKS):
            if request(port, "/work", "POST").get("accepted") is True:
                delivered += 1
            else:
                raise RuntimeError("Unaccepted positive work request")
            time.sleep(INJECTION_SPACING_SECONDS)
    else:
        time.sleep(SHAM_SECONDS)
    end = time.monotonic_ns()
    write_log(path, {
        "role": "injector", "logger_id": f"injector-{os.getpid()}",
        "pid": os.getpid(), "onset_ns": onset, "end_ns": end,
        "delivered": delivered, "attempted": INJECTION_TASKS if positive else 0,
        "sham": not positive,
    })


def control_p02(port: int, stop: mp.Event, path: Path, enabled: bool) -> None:
    sent = applied = acknowledged = None
    observed_depth = None
    if enabled:
        deadline = time.monotonic() + FOLLOWUP_SECONDS + 3
        while not stop.is_set() and time.monotonic() < deadline:
            state = request(port, "/status")
            if state["queued"] > 5:
                sent = time.monotonic_ns()
                reply = request(port, "/action", "POST")
                acknowledged = time.monotonic_ns()
                if reply.get("changed") is not True:
                    raise RuntimeError("Service did not acknowledge action")
                applied = reply["server_applied_ns"]
                observed_depth = state["queued"]
                break
            time.sleep(POLL_SECONDS)
    else:
        stop.wait(timeout=FOLLOWUP_SECONDS + 3)
    write_log(path, {
        "role": "controller", "logger_id": f"controller-{os.getpid()}",
        "pid": os.getpid(), "enabled": enabled, "request_sent_ns": sent,
        "server_applied_ns": applied, "acknowledged_ns": acknowledged,
        "observed_depth": observed_depth,
    })


def probe_p02(port: int, injector_path: Path, report: Path, raw: Path) -> None:
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.touch()
    injector_end = None
    first_idle = None
    confirmed_at = None
    deadline = time.monotonic() + FOLLOWUP_SECONDS + 4
    polls = 0
    while time.monotonic() < deadline:
        status = request(port, "/status")
        t = time.monotonic_ns()
        log_jsonline(raw, {
            "observed_ns": t,
            "server_snapshot_ns": status["server_snapshot_ns"],
            "queued": status["queued"], "active": status["active"],
            "completed": status["completed"],
        })
        polls += 1
        if injector_end is None and injector_path.exists():
            injector_end = json.loads(injector_path.read_text())["end_ns"]
            deadline = min(deadline, time.monotonic() + FOLLOWUP_SECONDS)
        if injector_end is not None and t >= injector_end:
            if status["queued"] == 0 and status["active"] == 0:
                if first_idle is None:
                    first_idle = t
                elif t - first_idle >= RECOVERY_DWELL_NS:
                    confirmed_at = t
                    break
            else:
                first_idle = None
        time.sleep(POLL_SECONDS)
    stop_time = time.monotonic_ns()
    write_log(report, {
        "role": "monitor", "logger_id": f"monitor-{os.getpid()}",
        "pid": os.getpid(), "recovered_at_ns": first_idle if confirmed_at is not None else None,
        "confirmed_at_ns": confirmed_at, "observation_end_ns": stop_time,
        "logged_injector_end_ns": injector_end, "sample_count": polls,
        "probe_cadence_requested_ns": int(POLL_SECONDS * 1e9),
        "dwell_ns": RECOVERY_DWELL_NS,
    })


def replay_monitor(samples: list[dict], event_end_ns: int, dwell_ns: int,
                   gap_limit_ns: int) -> dict:
    """Independent-from-B/I/tau replay of *sampled* sustained idle.

    A trace with missing, repeated, backwards or large-gap samples is invalid
    rather than interpolated. Unobserved states between probes are unknown.
    """
    if not samples:
        raise ValueError("Empty health sample stream")
    prior = None
    first = None
    confirmed = None
    max_gap = 0
    after_end = 0
    for row in samples:
        stamp = row["observed_ns"]
        origin = row["server_snapshot_ns"]
        q = row["queued"]
        active = row["active"]
        completed = row["completed"]
        if any(type(v) is not int for v in (stamp, origin, q, active, completed)):
            raise ValueError("Non-integer monotonic timestamp or workload status")
        if q < 0 or active < 0 or completed < 0 or origin > stamp:
            raise ValueError("Invalid source status or clock ordering")
        if prior is not None:
            if stamp <= prior:
                raise ValueError("Nonmonotonic sampled probe timestamps")
            if stamp >= event_end_ns and prior >= event_end_ns:
                gap = stamp - prior
                max_gap = max(max_gap, gap)
                if gap > gap_limit_ns:
                    raise ValueError("Missing or late sampled probe: gap limit exceeded")
        prior = stamp
        if stamp < event_end_ns:
            continue
        after_end += 1
        if q == 0 and active == 0:
            if first is None:
                first = stamp
            elif stamp - first >= dwell_ns and confirmed is None:
                confirmed = stamp
        else:
            first = None
            if confirmed is not None:
                raise ValueError("Nonidle reading after confirmed recovery")
    if after_end == 0:
        raise ValueError("No health probes after injection ended")
    return {
        "recovered_at_ns": first if confirmed is not None else None,
        "confirmed_at_ns": confirmed,
        "sample_count": len(samples), "after_end_samples": after_end,
        "maximum_post_end_gap_ns": max_gap,
    }


def audit_calibration(calibration: dict) -> dict:
    windows = calibration["windows"]
    if len(windows) != CALIBRATION_WINDOWS:
        raise ValueError("Must retain exactly three pretrial calibration windows")
    rates = []
    for w in windows:
        delta = w["end_ns"] - w["start_ns"]
        count = w["completed_delta"]
        if (delta <= 0 or count <= 0 or w["queued_start"] <= 0
            or w["queued_end"] <= 0 or
            w["start_service_snapshot_ns"] > w["start_ns"] or
            w["end_service_snapshot_ns"] > w["end_ns"]):
            raise ValueError("Invalid calibrated saturation window")
        rates.append(count * 1e9 / delta)
    mean = sum(rates) / len(rates)
    if max(abs(x-mean) / mean for x in rates) > CALIBRATION_RATE_VARIATION:
        raise ValueError("Calibration window rate variation exceeded 25%")
    sparse = calibration["sparse_probe"]
    if (sparse["completed"] != SPARSE_TASKS
        or sparse["end_ns"] >= windows[0]["start_ns"]
        or sparse["end_ns"] <= sparse["start_ns"]):
        raise ValueError("Sparse contrasting workload invalid")
    return {
        "rate_windows_per_second": rates,
        "calibrated_local_B": sum(w["completed_delta"] for w in windows)
            * 1e9 / sum(w["end_ns"] - w["start_ns"] for w in windows),
        "sparse_completed": sparse["completed"],
        "window_count": len(windows),
    }


def audit_trial(folder: Path, intervention: str, prereg_sha: str,
                clock_resolution_ns: int) -> dict:
    records = {name: json.loads((folder / f"{name}.json").read_text())
               for name in ("calibration", "injector", "controller", "monitor")}
    samples = read_jsonlines(folder / "monitor-samples.jsonl")
    actions = read_jsonlines(folder / "service-actions.jsonl")
    calib, injector, controller, monitor = [records[name] for name in
                                               ("calibration", "injector", "controller", "monitor")]
    if len({r["pid"] for r in records.values()}) != 4:
        raise ValueError("Role processes were not distinct")
    calibration = audit_calibration(calib)
    if calib["windows"][-1]["end_ns"] >= injector["onset_ns"]:
        raise ValueError("Calibration overlapped intervention")
    replay = replay_monitor(
        samples, injector["end_ns"], RECOVERY_DWELL_NS, GAP_LIMIT_NS
    )
    if (replay["sample_count"] != monitor["sample_count"]
        or replay["recovered_at_ns"] != monitor["recovered_at_ns"]
        or replay["confirmed_at_ns"] != monitor["confirmed_at_ns"]):
        raise ValueError("Independent replay contradicts monitor")
    if (monitor["observation_end_ns"] < samples[-1]["observed_ns"]
        or replay["confirmed_at_ns"] is not None
        and replay["confirmed_at_ns"] > monitor["observation_end_ns"]):
        raise ValueError("Monitor observations outside follow-up window")
    if monitor["logged_injector_end_ns"] != injector["end_ns"]:
        raise ValueError("Monitor event marker differs from injector")
    if any(row["server_snapshot_ns"] > row["observed_ns"] for row in samples):
        raise ValueError("Clock order invalid")

    positive = intervention != "sham-01"
    enabled = intervention.startswith("positive-controlled")
    observed = {
        "trial_id": intervention, "intervention_positive": positive,
        "controller_enabled": enabled, "calibration": calibration,
        "health_replay": replay,
        "delivered_units": injector["delivered"],
        "source_log_sha256": {
            name: sha256(folder / f"{name}.json") for name in records
        } | {
            "monitor-samples": sha256(folder / "monitor-samples.jsonl"),
            "service-actions": sha256(folder / "service-actions.jsonl"),
        },
    }
    if positive and injector["delivered"] != INJECTION_TASKS:
        raise ValueError("Positive intervention did not deliver all fixed tasks")
    if not positive and injector["delivered"] != 0:
        raise ValueError("Sham delivered nonzero work")
    if not enabled:
        if actions or any(controller[key] is not None for key in (
            "request_sent_ns", "server_applied_ns", "acknowledged_ns"
        )):
            raise ValueError("Disabled/sham controller triggered an action")
        observed["candidate_index_inverse_seconds"] = None
        observed["verdict"] = (
            "SHAM_UNDEFINED_INDEX" if not positive
            else "DISABLED_CONTROL_RECOVERY_REPLAYED"
        )
        return observed
    if len(actions) != 1:
        raise ValueError("Required one server-side action per controlled trial")
    applied = actions[0]["server_applied_ns"]
    send, ack = controller["request_sent_ns"], controller["acknowledged_ns"]
    if (applied != controller["server_applied_ns"]
        or send is None or ack is None or not send <= applied <= ack
        or ack - send > GAP_LIMIT_NS or applied <= injector["onset_ns"]):
        raise ValueError("Controller send/apply/ack clock alignment failed")
    if replay["recovered_at_ns"] is None:
        raise ValueError("Controlled trial did not meet sampled recovery gate")
    evidence = TrialEvidence(
        system_id="github-actions-p02-single-host-fifo",
        trial_id=intervention, clock_domain="common_monotonic_ns",
        clock_resolution_ns=clock_resolution_ns, work_unit="local_HTTP_task",
        calibration=CapacityCalibration(
            start_ns=calib["windows"][0]["start_ns"],
            end_ns=calib["windows"][-1]["end_ns"],
            completed_work_units=sum(w["completed_delta"] for w in calib["windows"]),
            saturated_calibration_evidence="three-measured-positive-queue-windows",
            logger_id=calib["logger_id"],
        ),
        disturbance=ExternalDisturbance(
            onset_ns=injector["onset_ns"], end_ns=injector["end_ns"],
            delivered_excess_work_units=injector["delivered"],
            logger_id=injector["logger_id"],
        ),
        controller=ControllerResponse(action_ns=applied, logger_id=controller["logger_id"]),
        recovery=IndependentRecovery(
            observation_end_ns=monitor["observation_end_ns"],
            recovered_at_ns=replay["recovered_at_ns"],
            sustained_window_ns=RECOVERY_DWELL_NS,
            frozen_criterion_sha256=prereg_sha,
            logger_id=monitor["logger_id"],
        ),
    )
    observed["measurement"] = validate_evidence(evidence)
    observed["action_timing_ns"] = {
        "request_sent": send, "service_applied": applied, "acknowledged": ack,
        "request_to_ack": ack - send,
    }
    observed["candidate_index_inverse_seconds"] = observed["measurement"]["candidate_index_inverse_seconds"]
    observed["verdict"] = "AUDITABLE_CONTROLLED_POSITIVE"
    return observed


def run_trial(ctx: mp.context.BaseContext, root: Path, trial: str, prereg_sha: str,
              resolution_ns: int) -> dict:
    folder = root / trial
    folder.mkdir(parents=True, exist_ok=True)
    port = pick_local_port()
    server = ctx.Process(target=serve_p02,
                         args=(port, folder / "service-actions.jsonl"))
    server.start()
    try:
        await_service(port, server)
        calibrator = ctx.Process(target=calibrate_p02,
                                 args=(port, folder / "calibration.json"))
        calibrator.start()
        join_role(calibrator, 12, "three-window calibrator")
        await_empty(port, 8)
        stop = ctx.Event()
        controller = ctx.Process(target=control_p02,
                         args=(port, stop, folder / "controller.json",
                               trial.startswith("positive-controlled")))
        monitor = ctx.Process(target=probe_p02,
                         args=(port, folder / "injector.json",
                               folder / "monitor.json", folder / "monitor-samples.jsonl"))
        controller.start()
        monitor.start()
        time.sleep(0.12)
        injector = ctx.Process(target=inject_p02,
                     args=(port, folder / "injector.json", trial != "sham-01"))
        injector.start()
        join_role(injector, 6, "injector")
        join_role(monitor, 14, "sampled health monitor")
        stop.set()
        join_role(controller, 4, "controller")
        return audit_trial(folder, trial, prereg_sha, resolution_ns)
    finally:
        if server.is_alive():
            server.terminate()
        server.join(timeout=3)


def decide(results: list[dict]) -> str:
    if len(results) != len(TRIAL_NAMES):
        return "STOP_INSTRUMENTATION_UNRELIABLE"
    index = {r["trial_id"]: r for r in results}
    if set(index) != set(TRIAL_NAMES):
        return "STOP_INSTRUMENTATION_UNRELIABLE"
    if (all(index[t].get("verdict") == "AUDITABLE_CONTROLLED_POSITIVE"
            for t in TRIAL_NAMES[:2])
        and index["positive-disabled-01"].get("verdict") ==
            "DISABLED_CONTROL_RECOVERY_REPLAYED"
        and index["sham-01"].get("verdict") == "SHAM_UNDEFINED_INDEX"):
        return "PASS_AUDITABLE_INSTRUMENTATION"
    return "STOP_INSTRUMENTATION_UNRELIABLE"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("rp-e004-p02-observed"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol = Path(__file__).resolve().parents[1] / "docs/preregistration/RP-E004-P02.md"
    protocol_sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    resolution_ns = max(1, int(time.get_clock_info("monotonic").resolution * 1e9))
    order = list(TRIAL_NAMES)
    random.Random(SEED).shuffle(order)
    ctx = mp.get_context("spawn")
    results = []
    for name in order:
        try:
            results.append(run_trial(ctx, args.output, name, protocol_sha, resolution_ns))
        except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
            results.append({"trial_id": name, "verdict": "STOP_TRIAL_AUDIT",
                            "error": f"{type(exc).__name__}: {exc}"})
    decision = decide(results)
    summary = {
        "protocol": "RP-E004-P02", "preregistration_sha256": protocol_sha,
        "git_sha": os.getenv("GITHUB_SHA", "not_supplied"),
        "python": platform.python_version(), "os": platform.platform(),
        "monotonic_resolution_ns": resolution_ns,
        "trial_seed": SEED, "actual_order": order, "trials": results,
        "decision": decision,
        "scientific_claim": "CONTROLLED_SOFTWARE_INSTRUMENTATION_FEASIBILITY_ONLY",
        "physical_law_test": "NOT_PERFORMED",
        "external_replicability": "NOT_ESTABLISHED",
    }
    write_log(args.output / "summary.json", summary)
    print(json.dumps({"protocol": summary["protocol"], "decision": decision,
        "verdicts": {r["trial_id"]: r["verdict"] for r in results}},
        sort_keys=True))


if __name__ == "__main__":
    main()
