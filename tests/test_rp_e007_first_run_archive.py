"""Permanent first-run source-byte audit for prospective RP-E007-P01.

This test NEVER executes new hosted measurements. It checks the original
first run, its entire SHA-256 file manifest, all 27 sampled recovery
replays, and the prospectively registered held-out forecast decision.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from experiments.rp_e007_temporal_backlog import evaluate

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVE = PROJECT / "docs/results/RP-E007-P01-first-run"
FIRST_RUN = "40129313787"
FIRST_SOURCE = "b9ddd525cd5f00be21d212695f3c5d3cc77e9d36"


def read(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    return obj


def test_archived_first_execution_identity_and_registered_result():
    original = read(ARCHIVE / "evaluation.json")
    inventory = read(ARCHIVE / "archive-index.json")
    assert inventory["workflow_run_id"] == original["new_workflow_run_id"] == FIRST_RUN
    assert inventory["source_commit"] == original["new_source_commit"] == FIRST_SOURCE
    assert inventory["decision"] == original["decision"] == "PASS_TREND_INCREMENT"
    assert original["errors"] == []
    assert original["historical_rp_e006_data_reused"] is False
    assert original["new_lean_theorem"] is False
    assert original["physical_law_test"] == "NOT_PERFORMED"
    assert original["hardware_independence"] == "NOT_ESTABLISHED"


def test_exact_first_run_bytes_match_the_permanent_archive_sha256_index():
    inventory = read(ARCHIVE / "archive-index.json")
    original_hashes = inventory["file_sha256"]
    replayed = {
        str(file.relative_to(ARCHIVE)): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(ARCHIVE.rglob("*"))
        if file.is_file() and file.name != "archive-index.json"
    }
    assert len(replayed) == len(original_hashes) == 221
    assert replayed == original_hashes


def test_new_observations_are_replayed_before_scoring_again():
    archived = read(ARCHIVE / "evaluation.json")
    result = evaluate(ARCHIVE / "raw", PROJECT, FIRST_RUN, FIRST_SOURCE)
    assert result == archived
    assert result["original_training_trials_audited"] == 18
    assert result["original_heldout_trials_audited"] == 9
    assert result["verified_original_role_file_count"] == 216
    assert len(result["scoring"]["heldout_trial_predictions"]) == 9


def test_registered_trend_gain_is_preserved_not_fitted_from_holdout():
    result = read(ARCHIVE / "evaluation.json")
    score = result["scoring"]
    maes = score["heldout_mae_s"]
    assert score["frozen_threshold_ratio"] == 0.9
    assert maes["static"] > 0
    assert maes["two_sample_trend"] <= 0.9 * maes["static"]
    assert maes["two_sample_trend"] < maes["train_constant"]
    assert score["decision"] == "PASS_TREND_INCREMENT"
    assert all(
        item["latest_pre_end_ns"] <= item["injector_end_ns"]
        for item in score["heldout_trial_predictions"]
    )
    assert all(
        item["previous_pre_end_ns"] < item["latest_pre_end_ns"]
        for item in score["heldout_trial_predictions"]
    )


def test_source_log_mutation_is_rejected_without_replacing_observation(tmp_path):
    shutil.copytree(ARCHIVE / "raw", tmp_path / "raw")
    log = (
        tmp_path / "raw/rp-e007-p01-test/"
        "test-140-120-r0/monitor-samples.jsonl"
    )
    assert log.is_file()
    log.write_bytes(log.read_bytes() + b"\n")
    outcome = evaluate(tmp_path / "raw", PROJECT, FIRST_RUN, FIRST_SOURCE)
    assert outcome["decision"] == "STOP_INSTRUMENTATION"
    assert outcome["original_training_trials_audited"] == 18
    assert outcome["original_heldout_trials_audited"] == 0
    assert any(item["block"] == "test" for item in outcome["errors"])


def test_no_cross_study_claim_or_physical_measurements_in_original_result():
    archive = read(ARCHIVE / "evaluation.json")
    assert archive["physical_law_test"] == "NOT_PERFORMED"
    assert archive["hardware_independence"] == "NOT_ESTABLISHED"
    assert archive["new_lean_theorem"] is False
    assert archive["historical_rp_e006_data_reused"] is False
