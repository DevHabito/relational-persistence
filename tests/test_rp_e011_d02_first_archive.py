"""Freeze the FIRST original RP-E011-D02 source eligibility REJECTION.

D02 did not test a scheduler prediction. Its single invalid job ID may
not be hidden, reclassified or silently dropped by later code changes.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E011-D02-first-run"
FIRST_CODE = "a281772ababd8b77415008bae6434e6efddedd70"
FIRST_RUN = "40148759632"
FIRST_REPORT_SHA = "99be405c4e88dfd3646ea1812030eb7927b0a076de808f0257cd55d6e5db11f0"
SOURCE_SHA = "dd48cf7ca369d485b14add5d2baca70a1001c19d9b447688ff7639812673dc7c"


def originals() -> tuple[dict, dict]:
    return (
        json.loads((ARCHIVE / "audit.json").read_text("utf-8")),
        json.loads((ARCHIVE / "archive-index.json").read_text("utf-8")),
    )


def test_original_first_run_sha_identity_and_frozen_negative_gate():
    source, index = originals()
    assert source["protocol"] == index["protocol"] == "RP-E011-D02"
    assert source["decision"] == index["first_observed_verdict"] == "DATASET_SCHEMA_REJECTED"
    assert source["first_source_commit"] == index["original_source_code_commit"] == FIRST_CODE
    assert source["first_run_id"] == index["original_run_id"] == FIRST_RUN
    assert sha256((ARCHIVE / "audit.json").read_bytes()).hexdigest() == (
        index["first_observed_audit_sha256"]
    )
    assert index["first_observed_audit_sha256"] == FIRST_REPORT_SHA
    assert index["supersedes_RP_E011_D01"] is False


def test_source_original_hash_and_full_predeclared_rejection_evidence():
    source, _ = originals()
    assert source["source"]["sha256"] == SOURCE_SHA
    assert source["source"]["original_bytes"] == 59_430_886
    assert source["source"]["status"] == 200
    assert source["source"]["requested_url"] == (
        "https://jsspp.org/workload/logs/2017/cerit/grid-jobs.swf"
    )
    assert source["source"]["final_url"] == source["source"]["requested_url"]
    assert source["source"]["content_type"] == "application/x-shockwave-flash"
    assert source["errors"] == []
    counts = source["schema"]["counts"]
    assert counts["data_rows"] == 472_400
    assert counts["valid_numeric_prefix_rows"] == 472_400
    assert counts["standard_eligible_rows"] == 472_399
    assert counts["eligible_with_documented_extended_queue_name"] == 472_399
    assert counts["invalid_job_id"] == 1
    assert counts.get("duplicate_job_id", 0) == 0
    assert source["schema"]["distinct_documented_extended_queue_names_on_eligible_jobs"] == 13
    assert source["schema"]["parsed_record_widths"] == {"22": 472_400}
    assert source["schema"]["independent_standard_prefix_readers_agree"] is True
    assert source["schema"]["first_10_source_structure_problems"] == []


def test_no_posthoc_relaxation_or_unsupported_prediction_claims():
    source, index = originals()
    assert source["retrospective_forecast_evaluated"] is False
    assert source["scalar_C_law_tested"] is False
    assert source["physical_generalization_claimed"] is False
    assert source["schema"]["queue_wait_predictions_computed"] is False
    assert index["original_external_data_copied_into_git"] is False
    assert index["source_bytes_prehash_registered"] is False
    assert index["forecast_computed"] is False


def test_any_rewritten_original_report_breaks_integrity_hash():
    _, manifest = originals()
    bytes_ = (ARCHIVE / "audit.json").read_bytes()
    assert sha256(bytes_ + b"\n").hexdigest() != manifest["first_observed_audit_sha256"]
