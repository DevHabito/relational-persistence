"""First RP-U005-D04 archive identity and negative-classification regression."""
from hashlib import sha256
import json
from pathlib import Path

import pytest


ROOT = Path("docs/results/RP-U005-D04-first-run")
PINNED_REPORT_SHA = "23fdaac872176a2e1540c8facc633b67431ea4e7d8546594cda7c4e991aad1d6"
PINNED_ZIPS = {
    "occ_2026": (176074116, "7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c"),
    "int_2026": (202900063, "87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d"),
}


def load_original(root=ROOT):
    raw = (root / "audit.json").read_bytes()
    index = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != PINNED_REPORT_SHA:
        raise ValueError("Original D04 report byte hash changed")
    if index["first_original_audit_json_sha256"] != PINNED_REPORT_SHA:
        raise ValueError("D04 original index hash changed")
    return json.loads(raw), index


def test_original_failure_is_immutable():
    original, index = load_original()
    assert index["first_run_id"] == "42508927432"
    assert index["original_protocol_commit"] == "5cef0478be05ec9d53d2a7f5c23fec3d2ad5f3e9"
    assert index["original_code_commit"] == "f0ced058d12a4521ef27f99f3fdbbe70c9d9b7e6"
    assert original["decision"] == index["first_original_decision"] == "SOURCE_GATE_NOT_PASSED"
    assert original["cross_dataset_joins_performed"] == 0
    assert original["observed_policy_effects_computed"] is False
    assert original["original_raw_rows_persisted"] is False


def test_actual_zip_digests_do_not_infer_csv_success():
    original, index = load_original()
    assert len(original["original_zip_sources"]) == 2
    for item in original["original_zip_sources"]:
        expected_size, expected_digest = PINNED_ZIPS[item["source_id"]]
        assert item["original_zip_bytes"] == expected_size
        assert item["original_zip_sha256"] == expected_digest
        assert item["decision"] == "SOURCE_SCHEMA_REJECTED"
        assert item["error"] == "INVALID_HEADER_QUOTING"
        assert item["download_attempts"] == 1
        assert item["published_size_bytes"] == expected_size
        assert "decompressed_sha256" not in item
        assert "total_original_csv_records" not in item
        assert "zip_crc_eof_checked" not in item
    assert index["source_sha256"] == {key: sha for key, (_, sha) in PINNED_ZIPS.items()}


def test_a_mutated_original_report_is_not_accepted_even_if_manifest_is_forged(tmp_path):
    from shutil import copyfile
    for name in ("audit.json", "archive-index.json"):
        copyfile(ROOT / name, tmp_path / name)
    raw = (tmp_path / "audit.json").read_bytes() + b" "
    (tmp_path / "audit.json").write_bytes(raw)
    manifest = tmp_path / "archive-index.json"
    index = json.loads(manifest.read_text())
    index["first_original_audit_json_sha256"] = sha256(raw).hexdigest()
    manifest.write_text(json.dumps(index))
    with pytest.raises(ValueError, match="byte hash changed"):
        load_original(tmp_path)
