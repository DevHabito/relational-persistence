"""Permanent audit of the ORIGINAL RP-E010-D01 third-party source checkpoint.

Only metadata and source provenance are in Git. The full third-party
HPC2N bytes are NOT copied into this project. This audit deliberately
does not infer queueing outcomes or any RP physical law.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from experiments.rp_e010_source_audit import (
    EXPECTED_BLOB, EXPECTED_BYTES, REVISION, SOURCE_URL,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E010-D01-first-run"
FIRST_RUN = "40143917458"
FIRST_SOURCE = "aad2fc48d2e36fe765a1f248be67b09fdb081755"
SOURCE_SHA256 = "77b8993c73ae438385f6c0015708251f52dc316267b03ac19a406fbea2802afa"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_first_source_audit_provenance_and_original_decision():
    audit = load(ARCHIVE / "audit.json")
    index = load(ARCHIVE / "archive-index.json")
    assert audit["protocol"] == index["protocol"] == "RP-E010-D01"
    assert audit["github_first_run_id"] == index["original_workflow_run_id"] == FIRST_RUN
    assert audit["github_source_commit"] == index["original_source_commit"] == FIRST_SOURCE
    assert audit["decision"] == index["frozen_decision"] == "DATASET_SCHEMA_VERIFIED"
    assert audit["errors"] == []
    assert audit["real_world_queue_predictive_test"] == "NOT_PERFORMED"
    assert index["predictive_test"] == "NOT_PERFORMED"


def test_source_hashes_and_original_archived_metadata_cannot_change():
    index = load(ARCHIVE / "archive-index.json")
    report_path = ARCHIVE / "audit.json"
    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == (
        index["archived_audit_sha256"]
    )
    data = load(report_path)
    source = data["result"]
    assert source["identity_verified"] is True
    assert source["independent_parser_agreement"] is True
    assert source["actual_git_blob_sha1"] == EXPECTED_BLOB
    assert source["actual_bytes"] == EXPECTED_BYTES
    assert source["actual_sha256"] == SOURCE_SHA256
    assert data["source_revision"] == REVISION
    assert data["source_url"] == SOURCE_URL
    assert index["original_external_data_copied_to_git"] is False


def test_original_structural_counts_and_missing_queue_ids_are_preserved():
    source = load(ARCHIVE / "audit.json")["result"]
    original = source["counters"]
    assert original == source["independent_parser_counters"]
    assert original["data_lines"] == 202_871
    assert original["eligible_completed"] == 201_992
    assert original["header_lines"] == 31
    assert original["bad_width"] == 0
    assert original["invalid_numeric"] == 0
    assert original["duplicate_job_ids"] == 0
    assert original["unsorted_submit"] == 0
    assert original["missing_wait"] == 1
    assert original["missing_status"] == 878
    assert original["missing_queue"] == original["data_lines"]
    assert original["first_bad_lines"] == []


def test_no_observational_forecast_can_be_claimed_by_source_audit():
    record = load(ARCHIVE / "audit.json")
    assert record["decision"] == "DATASET_SCHEMA_VERIFIED"
    assert record["scalar_C_prediction_test"] == "NOT_PERFORMED"
    assert record["real_world_queue_predictive_test"] == "NOT_PERFORMED"
    assert record["original_NASA_submission_times_observed"] is False
