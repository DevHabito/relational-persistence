"""Permanent regression of the *first* RP-E006 hosted held-out result.

This does not rerun the queue or replace test observations. The originally
recorded negative verdict must not be edited into a pass.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from experiments.rp_e006_evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/results/RP-E006-P01-first-run"
FIRST_SOURCE = "9f4c488105f3e86b5912865974f9f686c9c0627a"
FIRST_RUN = "40126290924"


def record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_first_run_identity_and_negative_primary_verdict_are_immutable():
    original = record(ARCHIVE / "evaluation.json")
    index = record(ARCHIVE / "archive-index.json")
    assert original["source_commit"] == index["source_commit"] == FIRST_SOURCE
    assert original["workflow_run_id"] == index["workflow_run_id"] == FIRST_RUN
    assert original["decision"] == "NO_REGISTERED_PREDICTIVE_GAIN"
    assert index["decision"] == original["decision"]
    assert original["errors"] == []
    assert original["replayed_training_trials"] == 18
    assert original["replayed_heldout_trials"] == 9
    assert original["physical_law_test"] == "NOT_PERFORMED"
    assert original["external_hardware_replication"] == "NOT_ESTABLISHED"


def test_all_first_run_source_bytes_preserve_their_original_hashes():
    index = record(ARCHIVE / "archive-index.json")
    observed = {
        str(p.relative_to(ARCHIVE)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ARCHIVE.rglob("*"))
        if p.is_file() and p.name != "archive-index.json"
    }
    assert len(observed) == len(index["file_sha256"]) == 221
    assert observed == index["file_sha256"]


def test_independent_replay_recomputes_the_recorded_negative_prediction():
    original = record(ARCHIVE / "evaluation.json")
    recalculated = evaluate(ARCHIVE / "raw", ROOT, FIRST_RUN, FIRST_SOURCE)
    assert recalculated == original
    assert len(recalculated["source_sha256"]) == 216
    assert recalculated["heldout_scoring"]["decision"] == (
        "NO_REGISTERED_PREDICTIVE_GAIN"
    )
    assert len(recalculated["heldout_scoring"]["heldout_predictions"]) == 9


def test_queue_baseline_is_better_than_registered_index_predictor():
    report = record(ARCHIVE / "evaluation.json")
    mae = report["heldout_scoring"]["test_mae_seconds"]
    assert mae["queue_fluid"] < mae["index_only"]
    assert mae["load_only"] < mae["index_only"]
    assert mae["constant"] > mae["index_only"]
    assert not (mae["index_only"] <= 0.9 * mae["queue_fluid"])
    assert all(value >= 0 for value in mae.values())


def test_frozen_first_run_models_are_fit_from_training_labels_only():
    report = record(ARCHIVE / "evaluation.json")
    fitted = report["models"]
    assert set(fitted) == {
        "index_only", "constant", "queue_fluid", "tau_only", "load_only",
    }
    assert fitted["index_only"]["feature"] == "reciprocal_C"
    assert fitted["queue_fluid"] == {
        "calibration": "unfitted backlog/(2*B)",
    }


def test_mutated_original_health_trace_cannot_reproduce_successful_data_gate(tmp_path):
    shutil.copytree(ARCHIVE / "raw", tmp_path / "raw")
    change = (
        tmp_path / "raw/rp-e006-p01-test/"
        "test-140-120-r0/monitor-samples.jsonl"
    )
    assert change.is_file()
    change.write_bytes(change.read_bytes() + b"\n")
    verdict = evaluate(tmp_path / "raw", ROOT, FIRST_RUN, FIRST_SOURCE)
    assert verdict["decision"] == "STOP_INSTRUMENTATION"
    assert any(x.get("split") == "test" for x in verdict["errors"])
    assert verdict["replayed_training_trials"] == 18


def test_undefined_zero_load_outside_this_positive_only_software_domain():
    report = record(ARCHIVE / "evaluation.json")
    assert report["heldout_scoring"]["test_samples"] == 9
    assert all(
        entry["index_inverse_seconds"] > 0
        for entry in report["heldout_scoring"]["heldout_predictions"]
    )
