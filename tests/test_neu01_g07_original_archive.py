"""Frozen first G07 authenticated derivative status and original bytes."""
from hashlib import sha256
import json
from pathlib import Path

ORIGINAL = Path("docs/results/NEU-01-G07-P01-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G07-P01-first-run/archive-index.json")
EXPECTED = "60a328cd0cbd69f41da4ffaa8b71921b96f1c0d7fd81751b63b7f126cd1481c3"


def test_first_original_g07_aggregate_bytes_and_hash_unchanged():
    body = ORIGINAL.read_bytes()
    assert len(body) == 1133
    assert sha256(body).hexdigest() == EXPECTED
    assert body.endswith(b"\n")


def test_original_runner_provenance_frozen_including_negative_parse():
    idx = json.loads(INDEX.read_text())
    assert idx["protocol_only_commit"] == "6a0e0bd96fd5c8f4d4823c7c02fec0128c8c9d6e"
    assert idx["first_original_source_attempt_number"] == 1
    assert idx["first_original_source_workflow_run_id"] == 43332821093
    assert idx["before_source_synthetic_adversarial_tests_passed"] == 8
    assert idx["first_outcome"] == "DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED"
    assert idx["original_metadata_error_status"] == "EEGLAB_STRUCT_MISSING"
    assert idx["original_metadata_json"]["sha256"] == EXPECTED


def test_exact_md5_and_matlab_header_but_not_struct_alignment():
    d = json.loads(ORIGINAL.read_text())
    assert d["status"] == "DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED"
    assert d["source_identity"]["original_bytes"] == 73824136
    assert d["source_identity"]["publisher_annex_md5_verified"] is True
    assert d["source_identity"]["publisher_annex_md5"] == "2ba3c01f752799634414e2142544fd9b"
    assert d["source_identity"]["observed_sha256"] == "2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359"
    assert d["derivative_metadata"]["container_family"] == "MATLAB_V5"
    assert d["derivative_metadata"]["metadata_parse_status"] == "EEGLAB_STRUCT_MISSING"
    assert d["other_five_derivative_bodies_authenticated"] is False
    assert d["matched_sample_order_or_channel_alignment_verified"] is False
    assert d["processing_stage_causally_identified"] is False
    assert d["original_signal_body_uploaded"] is False
    assert d["clinical_or_thermodynamic_inference"] is False


def test_original_g07_archive_mutation_detectable():
    original = ORIGINAL.read_bytes()
    changed = original.replace(b"MATLAB_V5", b"MATLAB_V4", 1)
    assert changed != original
    assert sha256(changed).hexdigest() != EXPECTED
