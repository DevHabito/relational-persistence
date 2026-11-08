"""Archive regression for the first D07 strictly inadmissible key population."""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest


ARCHIVE = Path("docs/results/RP-U005-D07-first-run")
ORIGINAL_SHA = "def2803179d61114d41c03c3e0d429f0858694fbe73bee0a6e9d72d0e46e5be7"
EXPECTED = {
    "occ_2026": (6789484, 1929271),
    "int_2026": (6078331, 1293508),
}


def original(root=ARCHIVE):
    content = (root / "audit.json").read_bytes()
    manifest = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(content).hexdigest() != ORIGINAL_SHA:
        raise ValueError("First D07 report bytes do not match pinned SHA-256")
    if manifest["first_original_audit_json_sha256"] != ORIGINAL_SHA:
        raise ValueError("First D07 manifest report digest differs")
    return json.loads(content), manifest


def test_first_original_outcome_not_reinterpreted_as_real_world_no_matches():
    report, manifest = original()
    assert manifest["first_run_id"] == "42517705179"
    assert manifest["protocol_commit"] == "723681a8aa599eeeb20576c06530fe3f9c947796"
    assert report["decision"] == manifest["first_original_result"] == "BOTH_SOURCE_KEY_CENSUS_AUDITED"
    assert report["policy_effect_estimated"] is False
    assert report["original_raw_rows_or_keys_uploaded"] is False
    assert report["census"]["semantic_incident_identity_proven"] is False
    assert report["census"]["event_time_consistency_tested"] is False


def test_all_12_million_keys_rejected_on_exact_month_rule():
    report, manifest = original()
    sources = report["original_source_files"]
    assert {s["source_id"] for s in sources} == set(EXPECTED)
    for row in sources:
        total, bad_code = EXPECTED[row["source_id"]]
        assert row["original_csv_records"] == total
        assert row["valid_candidate_key_rows"] == 0
        assert row["invalid_candidate_key_rows"] == total
        assert row["invalid_key_reason_counts_nonexclusive"]["invalid_competence_month"] == total
        assert row["invalid_key_reason_counts_nonexclusive"]["invalid_occurrence_code"] == bad_code
        assert row["invalid_key_reason_counts_nonexclusive"]["invalid_competence_year"] == 0
        assert row["invalid_key_reason_counts_nonexclusive"]["invalid_distributor"] == 0
        assert row["zip_member_crc_eof_checked"] is True
        assert row["original_compressed_sha256"] == manifest["original_zip_sha256"][row["source_id"]]
        assert row["decompressed_sha256"] == manifest["original_decoded_sha256"][row["source_id"]]
    assert report["census"]["literal_candidate_key_cross_source"]["matched_distinct_candidate_keys"] == 0
    assert all(
        r["distinct_valid_candidate_keys"] == 0
        for r in report["census"]["per_source"].values()
    )


def test_forged_manifest_and_altered_json_cannot_pass(tmp_path):
    for name in ("archive-index.json", "audit.json"):
        copyfile(ARCHIVE / name, tmp_path / name)
    damaged = (tmp_path / "audit.json").read_bytes() + b" "
    (tmp_path / "audit.json").write_bytes(damaged)
    manifest_path = tmp_path / "archive-index.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["first_original_audit_json_sha256"] = sha256(damaged).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="pinned SHA-256"):
        original(tmp_path)
