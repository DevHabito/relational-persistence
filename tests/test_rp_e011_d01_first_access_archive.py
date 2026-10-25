"""Immutable original RP-E011-D01 source-access failure archive regression.

This archived ALCF source block does not contain a downloaded dataset and
MUST NOT be silently reclassified as a prediction loss or source success.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E011-D01-first-run"
SOURCE_RUN = "40148017404"
SOURCE_CODE = "af2f25ddf19258bb7581a21362619d9f951f951a"
FIRST_HASH = "28bd3d11dd0fdbb9789cff251233cef468889b43bcd3942100634e73ae4a0248"


def test_original_official_first_attempt_is_provenance_blocked_not_negative_model():
    source = json.loads((ARCHIVE / "audit.json").read_text())
    index = json.loads((ARCHIVE / "archive-index.json").read_text())
    assert source["protocol"] == index["protocol"] == "RP-E011-D01"
    assert source["first_github_run_id"] == index["original_first_run_id"] == SOURCE_RUN
    assert source["first_github_source_commit"] == index["source_code_sha"] == SOURCE_CODE
    assert source["decision"] == index["registered_first_verdict"] == "SOURCE_ACCESS_BLOCKED"
    assert source["acquisition"] is None and source["schema"] is None
    assert source["errors"] == [{
        "stage": "official-source-access",
        "reason": "Cannot access official URL: HTTPError",
    }]
    assert source["queue_prediction_scored"] is False
    assert source["physical_law_validated"] is False


def test_first_original_metadata_sha256_is_immutable():
    original = (ARCHIVE / "audit.json").read_bytes()
    index = json.loads((ARCHIVE / "archive-index.json").read_text())
    assert sha256(original).hexdigest() == index["original_report_sha256"] == FIRST_HASH
    assert sha256(original + b"\n").hexdigest() != FIRST_HASH
    assert index["downloaded_official_original_stored_in_git"] is False
    assert index["source_version_pinned_before_first_run"] is False


def test_jsspp_alternative_does_not_supersede_alcf_failure():
    source = json.loads((ARCHIVE / "audit.json").read_text())
    assert "ALCF" not in source["provider"]  # Provider name spelled out
    assert source["provider"] == "Argonne Leadership Computing Facility"
    assert "20220809_20221231" in source["official_resource_page"]
    assert "jsspp.org" not in source["official_resource_page"]
