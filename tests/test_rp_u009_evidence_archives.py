"""Preserve P01 invalid original, D01 token proof and P02 invalid original."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT=Path("docs/results")
ARCHIVES={
    "P01":(
        ROOT/"RP-U009-P01-first-run/audit.json",
        1170,"0b74889ed609a43d8924880e702d93fb8e723fd517fd718734463125991c13e3"
    ),
    "D01":(
        ROOT/"RP-U009-P01-D01-post-source-token-diagnostic/audit.json",
        2674,"8020c11a460a97552777e75ac3be0c31c02cc535a3c5eaba8d8cdc376c5e5ee0"
    ),
    "P02":(
        ROOT/"RP-U009-P02-post-source-salvage/audit.json",
        493,"ef7bea440396fcbac7b7bf06d4d301113703d364be4b6fb845622b826f1e407e"
    ),
}


def _load(name:str)->dict:
    file,size,digest=ARCHIVES[name]
    body=file.read_bytes()
    assert len(body)==size
    assert sha256(body).hexdigest()==digest
    return json.loads(body)


def test_first_p01_was_invalid_and_did_not_prove_pressure_recovery():
    p=_load("P01")
    assert p["status"]=="RP_U009_SOURCE_OR_WINDOWS_INVALID"
    assert p["failure"]["reason"]=="LOW_PRESSURE_SWITCH_MUST_BE_BINARY"
    assert p["source"]["official_zip_bytes"]==218381995
    assert p["source"]["official_zip_sha256"]==(
        "aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"
    )
    assert p["original_workflow_run_id"]=="44212185197"
    assert "all_four_fixed_windows" not in p


def test_d01_verified_decimal_binary_and_original_sample_spacing_only():
    d=_load("D01")
    assert d["status"]=="RP_U009_D01_BINARY_TEXT_ENCODING_ONLY"
    assert d["source_rows"]==1_516_948
    assert d["observed_median_gap_seconds"]==10
    assert d["all_source_lps_literal_token_counts"]=={
        "0.0":1_511_760,"1.0":5_188
    }
    assert [x["rows"] for x in d["per_window_lps_literal_tokens"]]==[
        600,7990,7976,7916
    ]
    assert d["original_first_P01_failure_sha256"]==ARCHIVES["P01"][2]
    assert d["csv_original_identity"]["original_csv_sha256"]==(
        "db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24"
    )
    assert d["no_pressure_values_read"] is True
    assert d["no_motor_current_values_read"] is True


def test_secondary_p02_remains_invalid_with_original_window_eligibility():
    p=_load("P02")
    assert p["status"]=="RP_U009_P02_SOURCE_OR_WINDOWS_INVALID"
    assert p["reason_code"]=="MAINTENANCE_WINDOW_HAS_TOO_FEW_HOUR_BUCKETS"
    assert p["first_secondary_workflow_id"]=="44213342591"
    assert p["original_P01_status_unchanged"]=="RP_U009_SOURCE_OR_WINDOWS_INVALID"
    assert "event_pairs" not in p


def test_archive_index_does_not_collapse_failed_and_diagnostic_sources():
    i=json.loads((ROOT/"RP-U009-source-evidence-index.json").read_text())
    assert i["P01_original_sha256"]==ARCHIVES["P01"][2]
    assert i["D01_original_sha256"]==ARCHIVES["D01"][2]
    assert i["P02_original_sha256"]==ARCHIVES["P02"][2]
    assert i["P01_status"]=="RP_U009_SOURCE_OR_WINDOWS_INVALID"
    assert i["D01_status"]=="RP_U009_D01_BINARY_TEXT_ENCODING_ONLY"
    assert i["P02_status"]=="RP_U009_P02_SOURCE_OR_WINDOWS_INVALID"
    assert i["source_pressures_never_reported_as_eligible_results"] is True
