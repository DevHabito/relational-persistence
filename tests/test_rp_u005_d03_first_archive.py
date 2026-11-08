"""RP-U005-D03 immutable first-result verification: archived CI JSON only.

This does not download, parse or evaluate any ANEEL incident records.
"""
from hashlib import sha256
import json
from pathlib import Path

import pytest


ARCHIVE = Path("docs/results/RP-U005-D03-first-run")
FIRST_SHA = "1243c3389b5800035d7feac93c91bfc0ca18c789cd1fd3ab94b5d0efe95274fa"
EXPECTED_SOURCE_SHA = {
    "occ_2026": "e12befc9c8984d6f13df545f50c2f6373e2f35318f30d986ca2a54f47a3db4dd",
    "occ_pre2026": "e3115f6d117eaca13d91f5d125c34094dcac1ee0aab8e780684486200f39aa24",
    "int_2026": "d510fabae63909fa9237215c0f17860e8144810de2e3c2ed65fd4fad516062ad",
    "int_pre2026": "e7234c20b9f8d478ffea7d83c121de8811e93a869e13e6ced38ed58b26fe566c",
}
EXPECTED_SIZE = {
    "occ_2026": 173223,
    "occ_pre2026": 161122,
    "int_2026": 178041,
    "int_pre2026": 165260,
}
EXPECTED_DATE = {
    "occ_2026": ("1.1", "28/07/2026"),
    "occ_pre2026": ("1.0", "11-10-2022"),
    "int_2026": ("1.0", "21/07/2026"),
    "int_pre2026": ("1.0", "11-10-2022"),
}


def first_archive(root=ARCHIVE):
    raw = (root / "audit.json").read_bytes()
    index = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != FIRST_SHA:
        raise ValueError("First original CI JSON byte SHA-256 mismatch")
    if index["first_audit_json_sha256"] != FIRST_SHA:
        raise ValueError("First original CI index SHA-256 mismatch")
    doc = json.loads(raw)
    return doc, index


def test_original_identity_is_independently_anchored():
    result, index = first_archive()
    assert index["first_run_id"] == "42505852818"
    assert index["source_workflow_head_sha"] == "199a18f256b7ccf02f5534f6d61af2d3152f71b4"
    assert index["protocol_commit_sha"] == "c46f1326e7de685af956f55d3f7b65d7d5cc4752"
    assert index["first_artifact_zip_sha256_from_job_log"] == (
        "73dd97df0a0d3119790ef855e14d503a165da0b121861510ba59fa343396a49e"
    )
    assert result["protocol_commit"] == index["protocol_commit_sha"]
    assert result["decision"] == index["first_original_decision"]
    assert result["decision"] == "FOUR_DICTIONARIES_AUTHENTICATED_EXPECTED_VERSIONS"
    assert result["incident_rows_read"] == 0
    assert result["policy_effect_estimated"] is False
    assert result["actual_repair_cost_measured"] is False


def test_all_four_source_hashes_and_header_dates():
    result, index = first_archive()
    assert result["source_count"] == 4
    rows = {row["source_id"]: row for row in result["source_results"]}
    assert len(rows) == 4
    assert set(rows) == set(EXPECTED_SOURCE_SHA)
    assert index["source_sha256"] == EXPECTED_SOURCE_SHA
    assert len(set(EXPECTED_SOURCE_SHA.values())) == 4
    for key, row in rows.items():
        assert "error" not in row
        assert row["http_status"] == 200
        assert row["original_pdf_sha256"] == EXPECTED_SOURCE_SHA[key]
        assert row["original_pdf_bytes"] == EXPECTED_SIZE[key]
        assert (row["version"], row["header_date"]) == EXPECTED_DATE[key]
        assert row["expected_header_year_matched"] is True
        assert row["first_page_title_matches_kind"] is True
        assert len(row["first_page_png_sha256"]) == 64
        assert row["page_count"] in (3, 4)
        assert row["final_url"] == row["source_url"]


def test_mutated_json_is_rejected_even_if_manifest_is_adjusted(tmp_path):
    from shutil import copyfile

    for name in ("audit.json", "archive-index.json"):
        copyfile(ARCHIVE / name, tmp_path / name)
    original = (tmp_path / "audit.json").read_bytes()
    altered = original + b" "
    (tmp_path / "audit.json").write_bytes(altered)
    index_path = tmp_path / "archive-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["first_audit_json_sha256"] = sha256(altered).hexdigest()
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError, match="byte SHA-256 mismatch"):
        first_archive(tmp_path)


def test_original_archive_index_mutation_is_rejected(tmp_path):
    from shutil import copyfile

    for name in ("audit.json", "archive-index.json"):
        copyfile(ARCHIVE / name, tmp_path / name)
    index_path = tmp_path / "archive-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["first_audit_json_sha256"] = "0" * 64
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError, match="index SHA-256 mismatch"):
        first_archive(tmp_path)
