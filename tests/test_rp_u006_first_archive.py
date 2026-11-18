"""Immutable first source RP-U006 archive integrity and replay, no new measurements."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments import rp_u006_forecast_core as core
from experiments import rp_u006_observed_recovery as runner

ROOT = Path("docs/results/RP-U006-P01-first-run")
SOURCE_SUMMARY = ROOT / "summary.json"
SOURCE_SHA = "d051c72dc5c40caa23a59585c35cdd71b3c94671266a32790a28d27c22e4e897"
SOURCE_BYTES = 16963


def first_original() -> dict:
    original = SOURCE_SUMMARY.read_bytes()
    assert len(original) == SOURCE_BYTES
    assert sha256(original).hexdigest() == SOURCE_SHA
    return json.loads(original)


def test_first_original_digest_chronology_and_fifteen_trial_census():
    s = first_original()
    assert s["study"] == "RP-U006-P01"
    assert s["source_commit"] == "967909da3c1724cf23bd6226ede56d38b02cfd8c"
    assert s["protocol_commit"] == core.PROTOCOL_ONLY_SHA
    assert s["first_workflow_run_id"] == "44203138441"
    assert s["original_trials_valid"] is True
    assert s["status"] == "RP_U006_EXECUTABLE_STATE_FORECAST_GAIN_WITHIN_HOST"
    assert len(s["diagnostic"]) == 6
    assert len(s["heldout"]) == 8
    assert [x["requested_jobs"] for x in s["diagnostic"]] == list(core.DIAGNOSTIC_LOADS)
    assert [x["requested_jobs"] for x in s["heldout"]] == list(core.HOLDOUT_LOADS)
    assert len([x for x in ROOT.rglob("*") if x.is_file()]) == 78


def test_all_original_service_monitor_and_controller_sources_replay_without_fitting():
    s = first_original()
    trial_rows = [s["calibration"], *s["diagnostic"], *s["heldout"]]
    assert len(trial_rows) == 15
    all_samples = 0
    for i, row in enumerate(trial_rows):
        label = "calibration" if i == 0 else (
            f"diagnostic-{i:02d}" if i <= 6 else f"holdout-{i-6:02d}"
        )
        folder = ROOT / label
        assert len([x for x in folder.iterdir() if x.is_file()]) == 5
        for filename, key in (
            ("service-events.jsonl", "event_log_sha256"),
            ("monitor-samples.jsonl", "monitor_log_sha256"),
            ("controller-injector.json", "controller_log_sha256"),
        ):
            assert sha256((folder / filename).read_bytes()).hexdigest() == row[key]
        events = runner.read_jsonlines(folder / "service-events.jsonl")
        monitor = runner.read_jsonlines(folder / "monitor-samples.jsonl")
        compared = core.validate_service_events(
            events, row["requested_jobs"], calibration=i == 0
        )
        assert compared == row["independent_job_identity_audit"]
        assert row["source_trial_valid"] is True
        assert row["server_process_exit_code"] == 0
        assert row["monitor_process_exit_code"] == 0
        all_samples += len(monitor)
        if i:
            assert core.recovery_elapsed(
                monitor, row["server_enable_ns"], row["requested_jobs"]
            ) == row["recovery_seconds"]
        else:
            assert core.calibration_interval(events) == row[
                "calibrated_service_interval_seconds"
            ]
    assert all_samples == 302


def test_original_heldout_calibrated_error_and_outcome_unchanged():
    s = first_original()
    fit = s["training_median_recovery_seconds"]
    interval = s["calibrated_completion_interval_seconds"]
    assert interval == 0.012642039
    assert fit == 0.2400555515
    for item in s["heldout"]:
        assert item["predictions"] == core.frozen_forecasts(
            [fit] * len(core.DIAGNOSTIC_LOADS),
            interval, item["pre_enable_outstanding"]
        )
    o = core.evaluate_original(s)
    assert o["status"] == s["status"]
    assert o["state_forecast_strict_wins_of_eight"] == s[
        "state_forecast_strict_wins_of_eight"
    ] == 8
    assert o["availability_only_MAE_seconds"] == s[
        "availability_only_MAE_seconds"
    ]
    assert o["outstanding_aware_MAE_seconds"] == s[
        "outstanding_aware_MAE_seconds"
    ]
    assert s["relative_MAE_reduction"] > .88
    assert s["actual_network_edge_restoration_performed"] is False


def test_archive_index_links_first_provenance_and_raw_digest():
    data = json.loads((ROOT / "archive-index.json").read_text(encoding="utf-8"))
    assert data["original_summary_sha256"] == SOURCE_SHA
    assert data["original_summary_size_bytes"] == SOURCE_BYTES
    assert data["original_raw_source_files"] == 77
    assert data["original_intervention_trials"] == 15
    assert data["original_heldout_trials"] == 8
    assert data["original_monitor_source_samples"] == 302
    assert data["first_original_github_artifact_id"] == 14381048918
    assert data["first_source_pre_original_adversarial_tests_passed"] == 19
    assert data["source_head_python311_tests_passed"] == 798
    assert data["source_head_python312_tests_passed"] == 798
