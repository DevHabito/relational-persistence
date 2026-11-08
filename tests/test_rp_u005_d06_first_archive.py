"""Immutable first D06 source replay regression, without any publisher-row download."""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile
import pytest

ROOT = Path("docs/results/RP-U005-D06-first-run")
FIRST_SHA = "47d69c100aff20733c5de28fb96b2aaf23e2441d624a833d2188e8675b3a5abe"
SOURCES = {
    "occ_2026": (6789484, 176074116, 2236732733,
        "7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c",
        "736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567"),
    "int_2026": (6078331, 202900063, 2328209339,
        "87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d",
        "4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce"),
}


def archive(root=ROOT):
    original = (root / "audit.json").read_bytes()
    index = json.loads((root / "archive-index.json").read_text(encoding="utf-8"))
    if sha256(original).hexdigest() != FIRST_SHA:
        raise ValueError("first D06 report bytes do not match pinned original")
    if index["first_original_json_sha256"] != FIRST_SHA:
        raise ValueError("first D06 index does not match original report")
    return json.loads(original), index


def test_original_report_is_exact_and_not_a_physical_experiment():
    report, index = archive()
    assert report["decision"] == index["original_first_run_decision"] == "BOTH_SOURCE_SCHEMAS_AUDITED"
    assert index["first_run_id"] == "42510085342"
    assert report["protocol_commit"] == index["protocol_commit"]
    assert index["protocol_commit"] == "05e41f1a85d3baf5173a9198f1938349abbd1adf"
    assert report["cross_dataset_joins_performed"] == 0
    assert report["observed_policy_effects_computed"] is False
    assert report["original_raw_rows_persisted"] is False
    assert report["new_prediction_test"] is False


def test_two_complete_original_full_sha_and_crc():
    report, index = archive()
    assert len(report["original_zip_sources"]) == 2
    for src in report["original_zip_sources"]:
        original_rows, zip_size, csv_size, zip_sha, csv_sha = SOURCES[src["source_id"]]
        assert src["decision"] == "SOURCE_COMPLETE_SCHEMA_AUDITED"
        assert src["original_zip_bytes"] == zip_size
        assert src["original_zip_sha256"] == zip_sha
        assert src["decompressed_bytes"] == csv_size
        assert src["decompressed_sha256"] == csv_sha
        assert src["total_original_csv_records"] == original_rows
        assert src["zip_crc_eof_checked"] is True
        assert src["delimiter"] == ";"
        assert len(src["original_header_columns"]) == (23 if src["source_id"] == "occ_2026" else 26)
        assert index["sources"][src["source_id"]]["original_csv_records"] == original_rows


def test_original_source_missingness_remains_visible():
    report, _ = archive()
    data = {s["source_id"]: s for s in report["original_zip_sources"]}
    assert data["occ_2026"]["empty_required_cells_by_field"]["NumTempoPreparacao"] == 4422177
    assert data["occ_2026"]["empty_required_cells_by_field"]["NumTempoDeslocamento"] == 3730035
    assert data["occ_2026"]["empty_required_cells_by_field"]["NumTempoExecucao"] == 4035775
    assert data["int_2026"]["empty_required_cells_by_field"]["DatInicioInterrupcao"] == 20299
    assert data["int_2026"]["empty_required_cells_by_field"]["DatFimInterrupcao"] == 20299


def test_manifest_tampering_cannot_cure_corrupted_original(tmp_path):
    for name in ("audit.json", "archive-index.json"):
        copyfile(ROOT / name, tmp_path / name)
    altered = (tmp_path / "audit.json").read_bytes() + b" "
    (tmp_path / "audit.json").write_bytes(altered)
    index_path = tmp_path / "archive-index.json"
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    idx["first_original_json_sha256"] = sha256(altered).hexdigest()
    index_path.write_text(json.dumps(idx))
    with pytest.raises(ValueError, match="pinned original"):
        archive(tmp_path)
