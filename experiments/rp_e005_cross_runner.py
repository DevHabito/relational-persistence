"""RP-E005-P01: replay two archived P02 software measurements independently.

The aggregator consumes source bytes and *never* executes the experiment.
No test of a universal B/(I*tau) relationship is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from experiments.rp_e004_p02 import SEED, TRIAL_NAMES, audit_trial, decide, read_jsonlines
from experiments.rp_e005_idle_oracle import replay_idle_groups

PROTOCOL = "RP-E005-P01"
SLOTS = ("runner-a", "runner-b")
SOURCE_FILES = (
    "calibration.json", "controller.json", "injector.json",
    "monitor.json", "monitor-samples.jsonl", "service-actions.jsonl",
)
ELIGIBLE = ("positive-controlled-01", "positive-controlled-02")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return result


def audit_one(
    slot: str,
    directory: Path,
    *,
    source_sha: str,
    run_id: str,
    e005_prereg_sha: str,
    p02_prereg_sha: str,
) -> dict:
    """Reconstruct every P02 trial from bytes; never use its reported Y as input."""
    if slot not in SLOTS:
        raise ValueError("Unexpected job slot")
    provenance = load_json(directory / "replica-provenance.json")
    expected = {
        "protocol": PROTOCOL,
        "job_slot": slot,
        "github_run_id": run_id,
        "source_commit": source_sha,
        "runner_label": "ubuntu-24.04",
        "e005_preregistration_sha256": e005_prereg_sha,
        "p02_preregistration_sha256": p02_prereg_sha,
        "p02_execution_returncode": 0,
        "physical_instrument_independence": "NOT_ESTABLISHED",
        "predictive_index_validation": "NOT_PERFORMED",
    }
    for name, value in expected.items():
        if provenance.get(name) != value:
            raise ValueError(f"{slot}: mismatched provenance {name}")
    if not str(provenance.get("python_version", "")).startswith("3.12."):
        raise ValueError(f"{slot}: unregistered Python runtime")
    if not str(provenance.get("platform", "")).startswith("Linux-"):
        raise ValueError(f"{slot}: non-Linux runner")

    root = directory / "p02"
    summary = load_json(root / "summary.json")
    if (
        summary.get("protocol") != "RP-E004-P02"
        or summary.get("preregistration_sha256") != p02_prereg_sha
        or summary.get("git_sha") != source_sha
        or summary.get("physical_law_test") != "NOT_PERFORMED"
        or summary.get("external_replicability") != "NOT_ESTABLISHED"
    ):
        raise ValueError(f"{slot}: P02 source provenance mismatch")

    recorded_trials = summary.get("trials")
    if not isinstance(recorded_trials, list) or len(recorded_trials) != 4:
        raise ValueError(f"{slot}: must retain four trial records")
    recorded = {t.get("trial_id"): t for t in recorded_trials
                if isinstance(t, dict)}
    if len(recorded) != 4 or set(recorded) != set(TRIAL_NAMES):
        raise ValueError(f"{slot}: missing, duplicate or unexpected P02 trial")
    order = list(TRIAL_NAMES)
    random.Random(SEED).shuffle(order)
    if summary.get("actual_order") != order:
        raise ValueError(f"{slot}: trial order contradicts frozen seed")
    resolution = summary.get("monotonic_resolution_ns")
    if type(resolution) is not int or resolution <= 0:
        raise ValueError(f"{slot}: invalid monotonic clock resolution")

    audited = {}
    inventory = {}
    for trial in TRIAL_NAMES:
        folder = root / trial
        for name in SOURCE_FILES:
            path = folder / name
            if not path.is_file():
                raise ValueError(f"{slot}: missing source log {trial}/{name}")
            digest = sha256(path)
            label = name.rsplit(".", 1)[0]
            if recorded[trial].get("source_log_sha256", {}).get(label) != digest:
                raise ValueError(f"{slot}: mutated or unverified source log {trial}/{name}")
            inventory[f"{slot}/p02/{trial}/{name}"] = digest
        checked = audit_trial(folder, trial, p02_prereg_sha, resolution)
        if checked != recorded[trial]:
            raise ValueError(f"{slot}: independently recomputed trial differs: {trial}")
        # A separate contiguous-run algorithm, not P02's original
        # streaming recovery state machine, must reproduce every sample.
        original_samples = read_jsonlines(folder / "monitor-samples.jsonl")
        event_end = load_json(folder / "injector.json")["end_ns"]
        alternate_recovery = replay_idle_groups(original_samples, event_end)
        if alternate_recovery != checked["health_replay"]:
            raise ValueError(f"{slot}: distinct recovery algorithms disagree: {trial}")
        audited[trial] = checked

    if decide(list(audited.values())) != "PASS_AUDITABLE_INSTRUMENTATION":
        raise ValueError(f"{slot}: P02 trial gate failed")
    if summary.get("decision") != "PASS_AUDITABLE_INSTRUMENTATION":
        raise ValueError(f"{slot}: incorrect original decision")

    # Descriptive measurements only. Do not fit predictions or use their
    # values to decide whether the observation-quality gate passes.
    eligible_measurements = []
    for trial in ELIGIBLE:
        m = audited[trial]["measurement"]
        if (
            m["independently_observed_recovery_seconds"] is None
            or m["candidate_index_inverse_seconds"] is None
        ):
            raise ValueError(f"{slot}: undefined positive controlled observation")
        eligible_measurements.append({
            "trial_id": trial,
            "capacity_work_per_second": m["capacity_calibration_units_per_second"],
            "external_load_work_per_second": m["external_excess_intensity_units_per_second"],
            "service_action_latency_seconds": m["measured_response_latency_seconds"],
            "sampled_recovery_seconds": m["independently_observed_recovery_seconds"],
            "candidate_index_inverse_seconds": m["candidate_index_inverse_seconds"],
            "candidate_is_not_predictively_validated": True,
        })
    for trial in ("positive-disabled-01", "sham-01"):
        if audited[trial].get("candidate_index_inverse_seconds") is not None:
            raise ValueError(f"{slot}: noneligible trial assigned an index")

    return {
        "slot": slot,
        "run_id": run_id,
        "source_commit": source_sha,
        "p02_decision": summary["decision"],
        "p02_summary_sha256": sha256(root / "summary.json"),
        "independently_replayed_trials": len(audited),
        "eligible_measurements": eligible_measurements,
        "source_log_sha256": inventory,
        "scope": "same software, separately hosted VM jobs; hardware independence unverified",
    }


def evaluate(input_root: Path, repository_root: Path, run_id: str,
             source_sha: str) -> dict:
    """Fail closed, preserving attempted-run outcome even if a replica is absent."""
    p02_sha = sha256(repository_root / "docs/preregistration/RP-E004-P02.md")
    e005_sha = sha256(repository_root / "docs/preregistration/RP-E005-P01.md")
    if not run_id or not source_sha:
        raise ValueError("GitHub workflow ID and code commit are required")
    audited = []
    failures = []
    for slot in SLOTS:
        try:
            audited.append(audit_one(
                slot, input_root / f"rp-e005-p01-{slot}",
                source_sha=source_sha, run_id=run_id,
                e005_prereg_sha=e005_sha, p02_prereg_sha=p02_sha,
            ))
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
            failures.append({
                "slot": slot,
                "reason": f"{type(exc).__name__}: {exc}",
            })

    if len(audited) == 2 and audited[0]["p02_summary_sha256"] == audited[1]["p02_summary_sha256"]:
        failures.append({
            "slot": "both",
            "reason": "Identical P02 summary bytes do not establish distinct fresh observations",
        })
    files = {
        key: value
        for entry in audited for key, value in entry["source_log_sha256"].items()
    }
    if len(audited) == 2 and len(files) != 48:
        failures.append({
            "slot": "both",
            "reason": "Expected 48 original role and full-trace source files",
        })
    decision = ("PASS_TWO_RUNNER_REPLAY" if not failures and len(audited) == 2
                else "STOP_REPLICATION_AUDIT")
    return {
        "protocol": PROTOCOL,
        "decision": decision,
        "workflow_run_id": run_id,
        "source_commit": source_sha,
        "e005_preregistration_sha256": e005_sha,
        "p02_preregistration_sha256": p02_sha,
        "expected_jobs": list(SLOTS),
        "completed_valid_replicas": len(audited),
        "replayed_trials": sum(r["independently_replayed_trials"] for r in audited),
        "verified_raw_source_file_count": len(files),
        "sha256_original_role_and_trace_files": files,
        "replicas": audited,
        "failures": failures,
        "empirical_physical_law_test": "NOT_PERFORMED",
        "index_predictive_validation": "NOT_PERFORMED",
        "physical_hardware_independence": "NOT_ESTABLISHED",
        "cross_runner_monotonic_clock_subtraction": "PROHIBITED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    outcome = evaluate(args.input, root, args.run_id, args.source_sha)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "RP-E005-P01.json").write_text(
        json.dumps(outcome, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": outcome["decision"],
        "audited_replicas": outcome["completed_valid_replicas"],
        "replayed_trials": outcome["replayed_trials"],
        "verified_raw_files": outcome["verified_raw_source_file_count"],
        "failures": outcome["failures"],
        "scientific_scope": outcome["empirical_physical_law_test"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
