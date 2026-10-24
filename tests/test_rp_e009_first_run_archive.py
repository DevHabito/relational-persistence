"""RP-E009 FIRST hosted executable service outcome integrity regression.

This test never reruns the TCP service or changes the 18 original
measurements. Its positive verdict is limited to hosted software.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from experiments.rp_e009_evaluate import evaluate

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVE = PROJECT / "docs/results/RP-E009-P01-first-run"
SOURCE = "d940d39a7ac32d83fc6b638c056cad6982ec4a00"
FIRST_RUN = "40134924622"


def read(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(result, dict)
    return result


def test_original_registered_executable_transfer_identity():
    original = read(ARCHIVE / "evaluation.json")
    manifest = read(ARCHIVE / "archive-index.json")
    assert manifest["workflow_id"] == original["workflow_run_id"] == FIRST_RUN
    assert manifest["source_commit"] == original["source_commit"] == SOURCE
    assert manifest["original_first_run_verdict"] == "PASS_EXECUTABLE_TRANSFER"
    assert original["decision"] == "PASS_EXECUTABLE_TRANSFER"
    assert original["errors"] == []
    assert original["diagnostic_trials_replayed"] == 9
    assert original["heldout_trials_replayed"] == 9
    assert original["verified_original_source_file_count"] == 126


def test_every_original_event_byte_matches_immutable_first_sha256_manifest():
    manifest = read(ARCHIVE / "archive-index.json")
    expected = manifest["original_file_sha256"]
    actual = {
        str(path.relative_to(ARCHIVE)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ARCHIVE.rglob("*"))
        if path.is_file() and path.name != "archive-index.json"
    }
    assert len(actual) == len(expected) == 131
    assert actual == expected


def test_original_18_case_event_log_replay_reproduces_full_registered_decision():
    original = read(ARCHIVE / "evaluation.json")
    replayed = evaluate(ARCHIVE / "raw", PROJECT, FIRST_RUN, SOURCE)
    assert replayed == original
    assert replayed["decision"] == "PASS_EXECUTABLE_TRANSFER"
    assert len(replayed["scoring"]["heldout_cases"]) == 9


def test_frozen_positive_result_and_subgroups_remain_exactly_classified():
    original = read(ARCHIVE / "evaluation.json")
    score = original["scoring"]
    assert score["registered_threshold"] == .9
    assert score["mae_seconds"]["static"] > 0
    assert score["mae_seconds"]["trend"] <= .9 * score["mae_seconds"]["static"]
    assert score["trend_wins"] == 7
    assert score["ties"] == 2
    assert score["trend_losses"] == 0
    for mode in ("uniform", "early_burst", "late_burst"):
        errors = score["per_arrival_mode_mae_seconds"][mode]
        assert errors["trend"] < errors["static"]


def test_future_status_never_used_in_any_original_holdout_forecast():
    original = read(ARCHIVE / "evaluation.json")
    for observation in original["scoring"]["heldout_cases"]:
        assert observation["previous_pre_end_ns"] < observation["latest_pre_end_ns"]
        assert observation["latest_pre_end_ns"] <= observation["injector_end_ns"]
        assert observation["observed_B_work_per_second"] > 0
        assert observation["sampled_recovery_s"] >= 0


def test_changed_original_server_event_log_forces_stop(tmp_path):
    shutil.copytree(ARCHIVE / "raw", tmp_path / "raw")
    source = (
        tmp_path / "raw/rp-e009-p01-holdout/"
        "holdout-070-uniform/service-events.jsonl"
    )
    assert source.is_file()
    source.write_bytes(source.read_bytes() + b"\n")
    replayed = evaluate(tmp_path / "raw", PROJECT, FIRST_RUN, SOURCE)
    assert replayed["decision"] == "STOP_TRANSFER_AUDIT"
    assert replayed["diagnostic_trials_replayed"] == 9
    assert replayed["heldout_trials_replayed"] == 0
    assert any(e["block"] == "holdout" for e in replayed["errors"])


def test_physical_and_scalar_law_claims_remain_explicitly_unperformed():
    original = read(ARCHIVE / "evaluation.json")
    assert original["physical_independence"] == "NOT_ESTABLISHED"
    assert original["physical_law_test"] == "NOT_PERFORMED"
    assert original["prior_RP_E007_observations_reused"] is False
    assert original["new_lean_theorem"] is False
