"""Permanent byte-for-byte regression against the first RP-E005 hosted run.

This test never regenerates observational logs or invokes hosted services.
It independently replays the original archived data and insists that
the existing outcome and original byte hashes remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from experiments.rp_e005_cross_runner import evaluate

REPO = Path(__file__).resolve().parents[1]
ARCHIVE = REPO / "docs/results/RP-E005-P01-first-run"


def read_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_original_e005_archive_has_original_first_run_provenance():
    index = read_record(ARCHIVE / "archive-index.json")
    result = read_record(ARCHIVE / "evaluation.json")
    assert index["archive_policy"] == "first-run original bytes; no reexecution"
    assert index["workflow_run"] == result["workflow_run_id"] == "40124159620"
    assert index["source_commit"] == result["source_commit"] == (
        "542395dab0e23d7972ede8467c9283190d8381dc"
    )
    assert result["decision"] == index["independent_replay_decision"]
    assert result["decision"] == "PASS_TWO_RUNNER_REPLAY"
    assert result["failures"] == []


def test_every_archived_original_byte_still_matches_sha256_index():
    index = read_record(ARCHIVE / "archive-index.json")
    indexed = index["file_sha256"]
    real = {
        str(path.relative_to(ARCHIVE)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ARCHIVE.rglob("*"))
        if path.is_file() and path.name != "archive-index.json"
    }
    assert len(indexed) == len(real) == 53
    assert indexed == real


def test_stored_original_software_measurements_replay_without_modification():
    recorded = read_record(ARCHIVE / "evaluation.json")
    independently_recomputed = evaluate(
        ARCHIVE / "raw", REPO,
        run_id=recorded["workflow_run_id"],
        source_sha=recorded["source_commit"],
    )
    assert independently_recomputed == recorded
    assert recorded["replayed_trials"] == 8
    assert recorded["verified_raw_source_file_count"] == 48
    assert len(recorded["replicas"]) == 2
    assert all(r["independently_replayed_trials"] == 4
               for r in recorded["replicas"])


def test_no_false_physical_or_predictive_status_in_original_report():
    recorded = read_record(ARCHIVE / "evaluation.json")
    assert recorded["empirical_physical_law_test"] == "NOT_PERFORMED"
    assert recorded["index_predictive_validation"] == "NOT_PERFORMED"
    assert recorded["physical_hardware_independence"] == "NOT_ESTABLISHED"
    assert recorded["cross_runner_monotonic_clock_subtraction"] == "PROHIBITED"
    assert all(len(r["eligible_measurements"]) == 2
               for r in recorded["replicas"])
    assert all(item["candidate_is_not_predictively_validated"]
               for r in recorded["replicas"]
               for item in r["eligible_measurements"])


def test_mutated_archival_trace_does_not_pass_independent_replay(tmp_path):
    shutil.copytree(ARCHIVE / "raw", tmp_path / "raw")
    record = read_record(ARCHIVE / "evaluation.json")
    trace = (
        tmp_path / "raw/rp-e005-p01-runner-a/p02/"
        "positive-controlled-01/monitor-samples.jsonl"
    )
    trace.write_bytes(trace.read_bytes() + b"\n")
    rerun = evaluate(
        tmp_path / "raw", REPO,
        run_id=record["workflow_run_id"],
        source_sha=record["source_commit"],
    )
    assert rerun["decision"] == "STOP_REPLICATION_AUDIT"
    assert rerun["completed_valid_replicas"] == 1
    assert any("mutated or unverified" in x["reason"] for x in rerun["failures"])
