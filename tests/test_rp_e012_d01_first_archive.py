"""Pin RP-E012-D01's first publisher-verified original schema verdict.

These checks never access BigQuery, GCS production rows, or forecast labels.
Original provider file blobs were downloaded only in the first Actions run.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E012-D01-first-run"
REPORT_SHA = "57d67b1e51b975f19d9907bea1fa2d3ac7a0876016be175db123c2785bfa647b"
ORIGINAL_RUN = "40234431456"
CODE_COMMIT = "25147643481b0ec1f740655254dbcc0e58dc142e"
PREREG_COMMIT = "a024612b596f1f9d2d16219437b09b80f920d52f"


def archived():
    raw = (ARCHIVE / "audit.json").read_bytes()
    return raw, json.loads(raw), json.loads(
        (ARCHIVE / "archive-index.json").read_text(encoding="utf-8")
    )


def test_first_original_verdict_is_immutable_with_its_report_digest():
    raw, result, index = archived()
    assert sha256(raw).hexdigest() == REPORT_SHA
    assert index["first_original_report_sha256"] == REPORT_SHA
    assert index["first_run_id"] == result["first_run_id"] == ORIGINAL_RUN
    assert index["first_code_commit"] == result["original_code_commit"] == CODE_COMMIT
    assert index["preregistration_commit"] == PREREG_COMMIT
    assert result["decision"] == index["first_original_decision"] == (
        "SCHEMA_EVENT_METADATA_PRESENT_RUNTIME_CAP_UNVERIFIED"
    )
    assert sorted(p.name for p in ARCHIVE.iterdir()) == [
        "archive-index.json", "audit.json",
    ]


def test_original_publisher_bytes_and_independent_git_blob_ids_pinned():
    _, result, _ = archived()
    pins = {
        "proto": (
            "clusterdata_trace_format_v3.proto", 13720,
            "83101ef12604a6c9ce4a44288791a17869c2caf1",
            "8082651c5430acaef31846287a3e1262e734f9fa6a5067fa431864aef840abde",
        ),
        "readme": (
            "ClusterData2019.md", 2323,
            "22a38cab107ce8dedf18c86c1c2b25607980cf26",
            "6209413ba5dc94e45b9dda811871b7eab406980aab5279466fa9eb48578ff6e3",
        ),
    }
    for key, (filename, length, blob_id, sha) in pins.items():
        source = result["source_identity"][key]
        assert source["filename"] == filename
        assert source["bytes"] == length
        assert source["expected_git_blob_sha1"] == source["git_blob_sha1"] == blob_id
        assert source["sha256"] == sha
        assert source["publisher_repo"] == "google/cluster-data"
        assert source["publisher_commit"] == (
            "48b12446464b0422abcc18e0ec5b0b13e2f3a90c"
        )


def test_all_source_event_gate_fields_present_without_reclassification():
    _, result, _ = archived()
    evidence = result["required_event_metadata"]
    assert evidence["all_prespecified_event_gates_pass"] is True
    assert result["two_independent_parsers_agree"] is True
    assert result["errors"] == []
    assert all(not missing for types in evidence["missing_required"].values()
               for missing in types.values())
    assert set(evidence["event_enums"]["EventType"]) == {
        "SUBMIT", "SCHEDULE", "EVICT", "FINISH",
        "UPDATE_PENDING", "UPDATE_RUNNING",
    }
    assert set(evidence["event_enums"]["MissingType"]) == {
        "SNAPSHOT_BUT_NO_TRANSITION", "NO_SNAPSHOT_OR_TRANSITION",
        "EXISTS_BUT_NO_CREATION",
    }


def test_runtime_memory_field_never_misrepresented_as_hard_duration_cap():
    _, report, _ = archived()
    runtime = report["runtime_cap_evidence"]
    assert runtime["explicit_hard_runtime_cap_field_in_pinned_proto"] is False
    assert runtime["publisher_exact_matching_fields"] == []
    assert runtime["effective_enforcement_verified_from_schema"] is False
    assert runtime["assigned_memory_is_not_wallclock_runtime_cap"] is True
    assert runtime["no_field_does_not_imply_no_internal_enforcement"] is True
    assert "assigned_memory" in report["required_event_metadata"][
        "schema_fields"]["InstanceUsage"]
    assert report["real_runtime_cap_enforcement_verified"] is False


def test_no_raw_production_rows_or_observational_outcome_ever_calculated():
    _, result, index = archived()
    assert result["raw_production_rows_examined"] == 0
    assert index["raw_production_rows_examined"] == 0
    assert index["no_external_holdout_forecast_computed"] is True
    assert result["predictions_computed"] is False
    assert result["new_lean_theorem_claimed"] is False
    assert result["physical_law_claimed"] is False
    assert result["causal_observation_rules"]["usage_window"] == (
        "end_time < origin; cannot use future-ended aggregate"
    )


def test_report_single_byte_change_breaks_pinned_digest():
    raw, _, _ = archived()
    assert sha256(raw + b"\n").hexdigest() != REPORT_SHA
