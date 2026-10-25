"""Permanent regression pins the FIRST RP-E011-D03 forensic source observation.

The original JSSPP bytes are NOT in Git and cannot be reconstructed here.
This suite authenticates the archived audit bytes and the prior D02 archive,
not the provider's unavailable-by-design row content.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D03 = ROOT / "docs/results/RP-E011-D03-first-run"
D02 = ROOT / "docs/results/RP-E011-D02-first-run"
FIRST_RUN_ID = "40181814358"
FIRST_SOURCE_COMMIT = "143d2a5193b977851de100d3dd6c230af239b1de"
FIRST_AUDIT_SHA = "a3031311456ed5949bfbc73cd4f634c6bfa688c768806a94d6998ba20719e75d"
ORIGINAL_D02_AUDIT_SHA = "99be405c4e88dfd3646ea1812030eb7927b0a076de808f0257cd55d6e5db11f0"
ORIGINAL_SOURCE_SHA = "dd48cf7ca369d485b14add5d2baca70a1001c19d9b447688ff7639812673dc7c"
ANOMALOUS_LINE_SHA = "37fa5779391bcf43b42d672f89b13206efcf3f9336f2ec31d19d1874f848056c"


def load():
    raw = (D03 / "audit.json").read_bytes()
    index = json.loads((D03 / "archive-index.json").read_text("utf-8"))
    return raw, json.loads(raw), index


def test_first_audit_is_unchanged_and_bound_to_exact_first_run():
    raw, audit, index = load()
    assert sha256(raw).hexdigest() == FIRST_AUDIT_SHA
    assert index["audit_sha256"] == FIRST_AUDIT_SHA
    assert audit["protocol"] == index["protocol"] == "RP-E011-D03"
    assert audit["decision"] == index["first_run_decision"] == "ANOMALY_LOCALIZED"
    assert audit["first_run_id"] == index["first_run_id"] == FIRST_RUN_ID
    assert audit["source_commit"] == index["source_code_commit"] == FIRST_SOURCE_COMMIT


def test_exact_external_source_bytes_are_pinned_before_row_inference():
    _, audit, index = load()
    identity = audit["source_identity"]
    assert identity["observed_bytes"] == identity["expected_bytes"] == 59_430_886
    assert identity["observed_sha256"] == identity["expected_sha256"] == (
        index["observed_source_sha256"]
    ) == ORIGINAL_SOURCE_SHA
    provider = identity["provider"]
    assert provider["status"] == 200
    assert provider["requested_url"] == provider["final_url"] == (
        "https://jsspp.org/workload/logs/2017/cerit/grid-jobs.swf"
    )
    assert provider["sha256"] == ORIGINAL_SOURCE_SHA


def test_both_id_readers_reproduce_only_first_line_zero():
    _, audit, _ = load()
    data = audit["diagnostic"]
    assert data["all_integer_id_readers_agree"] is True
    assert data["data_rows"] == 472_400
    assert data["nonpositive_job_id_count"] == 1
    assert data["duplicate_job_id_count"] == 0
    assert data["d02_valid_numeric_prefix_rows"] == 472_400
    assert data["d02_standard_eligible_rows"] == 472_399
    assert data["d02_invalid_job_ids"] == 1
    assert data["d02_duplicate_job_ids"] == 0
    assert data["d02_extended_queue_count"] == 13
    assert data["d02_parsed_widths"] == {"22": 472_400}
    assert len(data["nonpositive_job_ids"]) == 1
    source_row = data["nonpositive_job_ids"][0]
    assert source_row == {
        "physical_line": 1,
        "data_record_ordinal": 1,
        "integer_job_id": 0,
        "original_line_without_newline_sha256": ANOMALOUS_LINE_SHA,
    }


def test_d02_first_schema_rejection_is_never_overwritten():
    _, audit, index = load()
    d02raw = (D02 / "audit.json").read_bytes()
    d02 = json.loads(d02raw)
    assert sha256(d02raw).hexdigest() == ORIGINAL_D02_AUDIT_SHA
    assert audit["frozen_d02_audit_sha256"] == ORIGINAL_D02_AUDIT_SHA
    assert d02["decision"] == "DATASET_SCHEMA_REJECTED"
    assert audit["d02_first_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"
    assert index["d02_first_verdict_unchanged"] == "DATASET_SCHEMA_REJECTED"
    assert d02["source"]["sha256"] == ORIGINAL_SOURCE_SHA
    assert d02["schema"]["counts"]["invalid_job_id"] == 1


def test_no_forecast_or_bulk_source_publication_is_claimed():
    _, audit, index = load()
    assert audit["predictive_scores_computed"] is False
    assert audit["physical_law_tested"] is False
    assert index["predictions_computed"] is False
    assert index["third_party_bulk_rows_published"] is False
    assert audit["errors"] == []
    assert sorted(p.name for p in D03.iterdir()) == [
        "archive-index.json", "audit.json",
    ]


def test_one_byte_mutation_would_break_permanent_audit_digest():
    raw, _, _ = load()
    assert sha256(raw + b"\n").hexdigest() != FIRST_AUDIT_SHA
