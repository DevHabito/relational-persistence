"""RP-E012-D01 synthetic-only adversarial tests for original Borg v3 triage.

Tests do NOT fetch a single Google production trace row or score a
forecast. The official source is downloaded only by reviewed main CI.
"""

from __future__ import annotations

from hashlib import sha1
import json

import pytest

from experiments import rp_e012_d01_schema as d01


def synthetic_proto(*, omit: tuple[str, str] | None = None,
                    extra: tuple[str, str] | None = None) -> str:
    pieces = [
        "syntax = \"proto2\";",
        "package google.cluster_data;",
    ]
    for block, fields in d01.REQUIRED_FIELDS.items():
        pieces.append(f"message {block} {{")
        for i, name in enumerate(fields, 1):
            if omit == (block, name):
                continue
            pieces.append(f"  optional int64 {name} = {i};")
        if extra is not None and extra[0] == block:
            pieces.append(f"  optional int64 {extra[1]} = 90;")
        if block == "MachineEvent":
            pieces.append("  enum NestedEventType {")
            pieces.append("    ADD = 1;")
            pieces.append("  }")
        pieces.append("}")
    for block, fields in d01.REQUIRED_ENUMS.items():
        pieces.append(f"enum {block} {{")
        for i, name in enumerate(fields, 1):
            if omit == (block, name):
                continue
            pieces.append(f"  {name} = {i};")
        pieces.append("}")
    return "\n".join(pieces) + "\n"


def synthetic_sources(monkeypatch, text: str):
    original = text.encode("utf-8")
    md = b"# ClusterData 2019 traces\nBorg clusterdata-2019\n"
    monkeypatch.setattr(d01, "SOURCE_BLOBS", {
        "clusterdata_trace_format_v3.proto": d01.publisher_blob_sha(original),
        "ClusterData2019.md": d01.publisher_blob_sha(md),
    })
    return original, md


def test_fixed_official_authority_and_publisher_git_blob_identities():
    assert d01.COMMIT == "48b12446464b0422abcc18e0ec5b0b13e2f3a90c"
    assert d01.REPO == "google/cluster-data"
    assert d01.SOURCE_BLOBS["clusterdata_trace_format_v3.proto"] == (
        "83101ef12604a6c9ce4a44288791a17869c2caf1"
    )
    assert d01.SOURCE_BLOBS["ClusterData2019.md"] == (
        "22a38cab107ce8dedf18c86c1c2b25607980cf26"
    )
    assert d01.source_url("clusterdata_trace_format_v3.proto").startswith(
        "https://raw.githubusercontent.com/google/cluster-data/48b124"
    )
    with pytest.raises(d01.SchemaFailure, match="Unregistered"):
        d01.source_url("other-file.proto")


def test_git_blob_sha_is_git_algorithm_not_plain_bytes_sha():
    original = b"synthetic\n"
    expect = sha1(b"blob 10\0" + original).hexdigest()
    assert d01.publisher_blob_sha(original) == expect
    assert d01.publisher_blob_sha(original) != sha1(original).hexdigest()


def test_independent_regex_and_line_oracles_match_all_synthetic_fields():
    text = synthetic_proto()
    a = d01.parse_regex_schema(text)
    b = d01.parse_line_schema(text)
    assert a == b
    for name, required in d01.REQUIRED_FIELDS.items():
        assert set(required).issubset(a["messages"][name])
    for name, required in d01.REQUIRED_ENUMS.items():
        assert set(required).issubset(a["enums"][name])
    assert "ADD" not in a["enums"]["EventType"]


def test_all_registered_schema_gates_on_clean_synthetic_source(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    audit = d01.audit_verified_sources(raw, readme)
    assert audit["decision"] == "SCHEMA_EVENT_METADATA_PRESENT_RUNTIME_CAP_UNVERIFIED"
    assert audit["two_independent_parsers_agree"] is True
    assert audit["required_event_metadata"]["all_prespecified_event_gates_pass"]
    assert audit["runtime_cap_evidence"][
        "explicit_hard_runtime_cap_field_in_pinned_proto"
    ] is False
    assert audit["real_runtime_cap_enforcement_verified"] is False
    assert audit["raw_production_rows_examined"] == 0
    assert audit["predictions_computed"] is False


@pytest.mark.parametrize("omission", [
    ("InstanceEvent", "time"), ("InstanceEvent", "resource_request"),
    ("InstanceUsage", "end_time"), ("EventType", "SCHEDULE"),
    ("EventType", "UPDATE_RUNNING"),
    ("MissingType", "EXISTS_BUT_NO_CREATION"),
])
def test_missing_required_metadata_fails_schema_capability_gate(
    monkeypatch, omission,
):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto(omit=omission))
    report = d01.audit_verified_sources(raw, readme)
    assert report["two_independent_parsers_agree"]
    assert report["decision"] == "SCHEMA_REQUIRED_EVENT_METADATA_MISSING"
    assert report["required_event_metadata"]["missing_required"][
        "messages" if omission[0] in d01.REQUIRED_FIELDS else "enums"
    ][omission[0]] == [omission[1]]


def test_inserting_runtime_cap_field_never_proves_enforcement(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto(
        extra=("InstanceEvent", "runtime_limit")
    ))
    outcome = d01.audit_verified_sources(raw, readme)
    assert outcome["decision"] == "SCHEMA_EVENT_METADATA_PRESENT_ENFORCEMENT_UNKNOWN"
    assert outcome["runtime_cap_evidence"]["publisher_exact_matching_fields"] == [
        "runtime_limit"
    ]
    assert outcome["real_runtime_cap_enforcement_verified"] is False


def test_assigned_memory_is_not_runtime_enforcement(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    result = d01.audit_verified_sources(raw, readme)
    assert "assigned_memory" in result["required_event_metadata"][
        "schema_fields"]["InstanceUsage"]
    assert result["runtime_cap_evidence"][
        "assigned_memory_is_not_wallclock_runtime_cap"
    ]
    assert result["runtime_cap_evidence"]["publisher_exact_matching_fields"] == []


def test_wrong_source_digest_prevents_all_schema_parsing(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    fake_source = raw + b"\n"
    def forbidden(*_):
        raise AssertionError("Corrupted original must not reach parser")
    monkeypatch.setattr(d01, "parse_regex_schema", forbidden)
    report = d01.audit_verified_sources(fake_source, readme)
    assert report["decision"] == "SCHEMA_SOURCE_IDENTITY_MISMATCH"


def test_wrong_utf8_does_not_become_missing_fields(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    bad = raw + b"\xff"
    monkeypatch.setitem(d01.SOURCE_BLOBS,
                        "clusterdata_trace_format_v3.proto",
                        d01.publisher_blob_sha(bad))
    decision = d01.audit_verified_sources(bad, readme)
    assert decision["decision"] == "SCHEMA_SOURCE_IDENTITY_MISMATCH"
    assert "UTF-8" in decision["errors"][0]["reason"]


def test_same_input_oracles_can_detect_parser_disagreement(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    def sabotage(_):
        return {"messages": {}, "enums": {}, "all_publisher_field_names": []}
    monkeypatch.setattr(d01, "parse_line_schema", sabotage)
    result = d01.audit_verified_sources(raw, readme)
    assert result["decision"] == "SCHEMA_PARSER_DISAGREEMENT"
    assert result["two_independent_parsers_agree"] is False


def test_reconstructed_events_never_assumed_causally_executed():
    assert d01.event_available_before(99, 100, reconstructed=False)
    assert not d01.event_available_before(100, 100, reconstructed=False)
    assert not d01.event_available_before(101, 100, reconstructed=False)
    assert not d01.event_available_before(99, 100, reconstructed=True)


@pytest.mark.parametrize("start,end,origin,visible", [
    (0, 300, 301, True),
    (0, 300, 300, False),
    (0, 300, 299, False),
    (0, 300, 150, False),
    (300, 300, 301, False),
    (320, 200, 301, False),
])
def test_five_minute_usage_window_never_leaks_future(
    start, end, origin, visible,
):
    assert d01.usage_window_available_before(start, end, origin) == visible


def test_original_result_does_not_contain_raw_trace_content(monkeypatch):
    raw, readme = synthetic_sources(monkeypatch, synthetic_proto())
    result = d01.audit_verified_sources(raw, readme)
    encoded = json.dumps(result, sort_keys=True)
    assert "original_code_commit" not in result
    assert "raw_trace" not in encoded
    assert "actual_future_runtime" not in encoded
    assert result["new_lean_theorem_claimed"] is False
    assert result["physical_law_claimed"] is False


def test_first_blocked_original_is_permanently_written_as_blocked(monkeypatch, tmp_path):
    def blocked(_):
        raise TimeoutError("fixture official raw host inaccessible")
    monkeypatch.setattr(d01, "download_original", blocked)
    result_path = tmp_path / "first" / "audit.json"
    result = d01.first_run(result_path)
    assert result["decision"] == "SCHEMA_SOURCE_ACCESS_BLOCKED"
    assert json.loads(result_path.read_text()) == result
    with pytest.raises(ValueError, match="overwrite"):
        d01.first_run(result_path)
