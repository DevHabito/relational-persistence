"""Immutable original D08 month/code format study and artifact-digest guards."""
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile
import pytest


ROOT = Path("docs/results/RP-U005-D08-first-run")
ORIGINAL_SHA = "2f7f0b27241034e62d6cd414ef1f61bd579a02f050e692de32bb5d9d91313cde"
COUNTS = {
    "occ_2026": (6789484, 1929271, 419),
    "int_2026": (6078331, 1293508, 0),
}


def read_first(root=ROOT):
    raw = (root / "audit.json").read_bytes()
    manifest = json.loads((root / "archive-index.json").read_text())
    if sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("D08 original source JSON bytes changed")
    if manifest["first_audit_json_sha256"] != ORIGINAL_SHA:
        raise ValueError("D08 first archive index digest changed")
    return json.loads(raw), manifest


def test_frozen_original_d08_status_and_source_identity():
    doc, index = read_first()
    assert index["protocol_commit"] == "7404adde5753b23e8d8a1050b6dccbe2a69cfa71"
    assert index["first_run_id"] == "42518642502"
    assert doc["decision"] == index["first_result"] == "SOURCE_FORMAT_PROFILE_COMPLETE"
    assert doc["joins_performed"] == 0
    assert doc["repair_policy_effect_computed"] is False
    assert doc["original_identifiable_values_published"] is False
    assert len(doc["source_profiles"]) == 2


def test_first_d08_month_spelling_and_code_length_totals():
    doc, index = read_first()
    for source in doc["source_profiles"]:
        total, bad, month8 = COUNTS[source["source_id"]]
        assert source["original_csv_rows"] == total
        assert source["original_zip_sha256"] == index["original_zip_sha256"][source["source_id"]]
        assert source["original_uncompressed_sha256"] == index["original_decoded_sha256"][source["source_id"]]
        assert source["zip_crc_eof_verified"] is True
        profile = source["literal_month_spelling_counts"]
        assert sum(profile.values()) == total
        assert profile["8"] == month8
        assert all(profile[f"0{i}"] == 0 for i in range(1, 10))
        assert all(profile[str(m)] == 0 for m in range(9, 13))
        assert all(profile[n] == 0 for n in (
            "EMPTY", "OTHER_ASCII_ONE_DIGIT", "OTHER_ASCII_TWO_DIGITS",
            "OTHER_ASCII_LONG_NUMERIC", "OTHER_NONNUMERIC_OR_NONASCII",
        ))
        assert source["invalid_code_rows"] == bad
        assert source["code_rows_passing_D07_code_syntax"] == total - bad
        why = source["invalid_code_reason_counts_nonexclusive"]
        assert why["CODE_LONGER_THAN_TEN"] == bad
        assert all(v == 0 for k,v in why.items() if k != "CODE_LONGER_THAN_TEN")


def test_mutated_report_rejected_even_if_companion_manifest_forged(tmp_path):
    for name in ("archive-index.json", "audit.json"):
        copyfile(ROOT / name, tmp_path / name)
    changed = (tmp_path / "audit.json").read_bytes() + b" "
    (tmp_path / "audit.json").write_bytes(changed)
    path = tmp_path / "archive-index.json"
    metadata = json.loads(path.read_text())
    metadata["first_audit_json_sha256"] = sha256(changed).hexdigest()
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="original source JSON bytes changed"):
        read_first(tmp_path)
