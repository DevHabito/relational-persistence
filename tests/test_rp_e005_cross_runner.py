"""RP-E005-P01 deterministic negative controls and historical archive replay.

The historical RP-E004-P02 archive is *not* new RP-E005 data. Synthetic
provenance test fixtures cannot establish independent hosted measurements.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from experiments.rp_e005_cross_runner import (
    ELIGIBLE, SLOTS, SOURCE_FILES, audit_one, evaluate, load_json, sha256,
)
from experiments.rp_e005_replica import run_replica

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "docs/results/RP-E004-P02-first-run"
P02_PROTOCOL = ROOT / "docs/preregistration/RP-E004-P02.md"
E005_PROTOCOL = ROOT / "docs/preregistration/RP-E005-P01.md"
HISTORICAL_SHA = json.loads(
    (HISTORICAL / "summary.json").read_text(encoding="utf-8")
)["git_sha"]
FAKE_RUN = "synthetic-test-not-a-real-hosted-run"


def synthetic_replica(tmp_path: Path, slot: str) -> Path:
    target = tmp_path / f"rp-e005-p01-{slot}"
    shutil.copytree(HISTORICAL, target / "p02")
    (target / "replica-provenance.json").write_text(
        json.dumps({
            "protocol": "RP-E005-P01",
            "job_slot": slot,
            "github_run_id": FAKE_RUN,
            "source_commit": HISTORICAL_SHA,
            "runner_label": "ubuntu-24.04",
            "runner_name": "FAKE_NOT_REAL",
            "python_version": "3.12.15",
            "platform": "Linux-synthetic-test",
            "p02_execution_returncode": 0,
            "e005_preregistration_sha256": sha256(E005_PROTOCOL),
            "p02_preregistration_sha256": sha256(P02_PROTOCOL),
            "physical_instrument_independence": "NOT_ESTABLISHED",
            "predictive_index_validation": "NOT_PERFORMED",
        }, sort_keys=True), encoding="utf-8",
    )
    return target


def test_original_p02_files_independently_replay_as_single_historical_fixture(tmp_path):
    slot = SLOTS[0]
    folder = synthetic_replica(tmp_path, slot)
    report = audit_one(
        slot, folder, source_sha=HISTORICAL_SHA,
        run_id=FAKE_RUN, e005_prereg_sha=sha256(E005_PROTOCOL),
        p02_prereg_sha=sha256(P02_PROTOCOL),
    )
    assert report["p02_decision"] == "PASS_AUDITABLE_INSTRUMENTATION"
    assert report["independently_replayed_trials"] == 4
    assert len(report["source_log_sha256"]) == 24
    assert len(report["eligible_measurements"]) == len(ELIGIBLE)


def test_clone_from_same_original_is_rejected_as_independent_measurement(tmp_path):
    synthetic_replica(tmp_path, SLOTS[0])
    synthetic_replica(tmp_path, SLOTS[1])
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["decision"] == "STOP_REPLICATION_AUDIT"
    assert result["completed_valid_replicas"] == 2
    assert len(result["sha256_original_role_and_trace_files"]) == 48
    assert any("Identical P02 summary bytes" in x["reason"]
               for x in result["failures"])
    assert result["index_predictive_validation"] == "NOT_PERFORMED"


def test_missing_replica_always_stops_even_with_valid_other_run(tmp_path):
    synthetic_replica(tmp_path, SLOTS[0])
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["decision"] == "STOP_REPLICATION_AUDIT"
    assert result["completed_valid_replicas"] == 1


def test_both_missing_replicas_stops_with_explicit_failure_records(tmp_path):
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["decision"] == "STOP_REPLICATION_AUDIT"
    assert result["completed_valid_replicas"] == 0
    assert len(result["failures"]) == 2


@pytest.mark.parametrize("field,forged", [
    ("job_slot", "runner-b"),
    ("source_commit", "deadbeef"),
    ("github_run_id", "another-run"),
    ("p02_execution_returncode", 124),
    ("runner_label", "ubuntu-slim"),
    ("predictive_index_validation", "VALIDATED"),
])
def test_forged_source_metadata_fails_closed(tmp_path, field, forged):
    path = synthetic_replica(tmp_path, SLOTS[0])
    meta = path / "replica-provenance.json"
    value = load_json(meta)
    value[field] = forged
    meta.write_text(json.dumps(value), encoding="utf-8")
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["decision"] == "STOP_REPLICATION_AUDIT"
    assert result["completed_valid_replicas"] == 0


def test_mutated_raw_sample_bytes_cannot_pass_saved_hash(tmp_path):
    path = synthetic_replica(tmp_path, SLOTS[0])
    event = path / "p02" / ELIGIBLE[0] / "monitor-samples.jsonl"
    event.write_bytes(event.read_bytes() + b"\n")
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert any("source log" in f["reason"] for f in result["failures"])
    assert result["completed_valid_replicas"] == 0


def test_missing_monitor_trace_cannot_be_silently_imputed(tmp_path):
    path = synthetic_replica(tmp_path, SLOTS[0])
    (path / "p02" / ELIGIBLE[0] / "monitor-samples.jsonl").unlink()
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["completed_valid_replicas"] == 0
    assert any("missing source" in f["reason"] for f in result["failures"])


def test_changed_recovery_label_is_not_accepted_without_matching_source(tmp_path):
    path = synthetic_replica(tmp_path, SLOTS[0])
    summary = path / "p02/summary.json"
    data = load_json(summary)
    data["trials"][0]["health_replay"]["recovered_at_ns"] += 1
    summary.write_text(json.dumps(data), encoding="utf-8")
    report = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert report["completed_valid_replicas"] == 0
    assert "recomputed trial differs" in report["failures"][0]["reason"]


def test_undefined_index_controls_preserved_in_historical_record():
    raw = load_json(HISTORICAL / "summary.json")
    values = {trial["trial_id"]: trial["candidate_index_inverse_seconds"]
              for trial in raw["trials"]}
    assert values["positive-disabled-01"] is None
    assert values["sham-01"] is None
    assert all(values[x] is not None for x in ELIGIBLE)


def test_no_cross_vm_monotonic_subtraction_is_allowed(tmp_path):
    result = evaluate(tmp_path, ROOT, FAKE_RUN, HISTORICAL_SHA)
    assert result["cross_runner_monotonic_clock_subtraction"] == "PROHIBITED"
    assert result["physical_hardware_independence"] == "NOT_ESTABLISHED"
    assert result["empirical_physical_law_test"] == "NOT_PERFORMED"


@pytest.mark.parametrize("slot", ("runner-c", "", "runner-A"))
def test_runner_slot_cannot_be_changed(slot, tmp_path):
    with pytest.raises(ValueError, match="Unregistered runner slot"):
        run_replica(slot, tmp_path / "unused", ROOT)


def test_existing_observation_directory_is_not_overwritten(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", HISTORICAL_SHA)
    monkeypatch.setenv("GITHUB_RUN_ID", FAKE_RUN)
    path = tmp_path / "observed"
    path.mkdir()
    (path / "first_run").write_text("historical bytes")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        run_replica(SLOTS[0], path, ROOT)


def test_empty_run_identity_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        evaluate(tmp_path, ROOT, "", HISTORICAL_SHA)


def test_fixed_six_original_role_files_per_trial():
    assert len(SOURCE_FILES) == 6
    assert len(SLOTS) * 4 * len(SOURCE_FILES) == 48
