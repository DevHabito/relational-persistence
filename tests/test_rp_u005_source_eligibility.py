"""RP-U005-D01 source integrity and non-eligibility controls.

These tests re-read already frozen metadata, not new provider event rows.
They do not establish actual network repairs or a predictive result.
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from experiments import rp_u005_source_eligibility as gate


@pytest.fixture(scope="module")
def evidence():
    return gate.read_historical_source()


def test_original_report_is_pinned_and_historical_source_scope(evidence):
    assert evidence.original_report_sha256 == gate.PINNED_FIRST_REPORT_SHA256
    assert evidence.original_machine_sha256 == gate.PINNED_MACHINE_OBJECT_SHA256
    assert evidence.compressed_machine_bytes == 651_854
    assert evidence.machine_event_rows == 46_219
    assert evidence.machine_identifiers == 10_001
    assert evidence.complete_machine_object is True
    assert evidence.instance_collection_rows_read == 0
    assert evidence.cross_table_history_certified is False
    assert evidence.event_receipt_timing_certified is False
    assert evidence.first_page_instance_inventory_paginated is True


def test_direct_repair_policy_eligibility_is_blocked_not_rewritten(evidence):
    result = gate.decision(evidence)
    assert result["decision"] == gate.BLOCKED_VERDICT
    assert result["empirical_policy_effect_estimated"] is False
    assert result["new_external_data_downloaded"] is False
    assert result["joint_history_complete"] is False
    assert result["online_event_receipt_time_certified"] is False
    assert result["actual_relation_repair_choices_observed"].startswith("NOT_ESTABLISHED")
    assert result["physical_repair_and_decision_costs_observed"].startswith(
        "NOT_ESTABLISHED"
    )
    assert result["independent_F2_terminal_path_outcome_observed"].startswith(
        "NOT_ESTABLISHED"
    )


def test_original_archive_byte_corruption_cannot_pass(tmp_path):
    for name in ("audit.json", "archive-index.json"):
        shutil.copyfile(gate.ORIGINAL / name, tmp_path / name)
    original = (tmp_path / "audit.json").read_bytes()
    assert original
    (tmp_path / "audit.json").write_bytes(original[:-1] + b" ")
    with pytest.raises(ValueError, match="archive bytes"):
        gate.read_historical_source(tmp_path)


def test_rewritten_manifest_digest_cannot_forge_original(tmp_path):
    for name in ("audit.json", "archive-index.json"):
        shutil.copyfile(gate.ORIGINAL / name, tmp_path / name)
    raw = (tmp_path / "audit.json").read_bytes()
    modified = raw + b" "
    (tmp_path / "audit.json").write_bytes(modified)
    index = json.loads((tmp_path / "archive-index.json").read_text())
    index["first_report_sha256"] = sha256(modified).hexdigest()
    (tmp_path / "archive-index.json").write_text(json.dumps(index))
    with pytest.raises(ValueError, match="archive bytes"):
        gate.read_historical_source(tmp_path)


def test_inconsistent_event_accounting_cannot_be_promoted(monkeypatch):
    report, index, raw = gate._load_source(gate.ORIGINAL)
    report["machine_counts"]["event_type_counts"]["1"] += 1
    with monkeypatch.context() as patch:
        patch.setattr(gate, "_load_source", lambda unused: (report, index, raw))
        with pytest.raises(ValueError, match="event counts"):
            gate.read_historical_source()


def test_reconstruction_without_cross_table_rows_is_not_online_truth(
    monkeypatch,
):
    report, index, raw = gate._load_source(gate.ORIGINAL)
    report["full_online_event_release_history_proven"] = True
    with monkeypatch.context() as patch:
        patch.setattr(gate, "_load_source", lambda unused: (report, index, raw))
        with pytest.raises(ValueError, match="limitations"):
            gate.read_historical_source()


@pytest.mark.parametrize(
    "changed",
    [
        {"complete_machine_object": False},
        {"cross_table_history_certified": True},
        {"event_receipt_timing_certified": True},
        {"instance_collection_rows_read": 1},
    ],
)
def test_a_forged_readiness_flag_is_rejected(evidence, changed):
    altered = replace(evidence, **changed)
    with pytest.raises(ValueError):
        gate.decision(altered)


def test_stopping_guards_survive_optimized_interpreter():
    process = subprocess.run(
        [
            sys.executable, "-O", "-c",
            "from experiments.rp_u005_source_eligibility import _require;"
            "_require(False, 'SCIENTIFIC_GUARD_ACTIVE')",
        ],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert process.returncode != 0
    assert "SCIENTIFIC_GUARD_ACTIVE" in process.stderr
