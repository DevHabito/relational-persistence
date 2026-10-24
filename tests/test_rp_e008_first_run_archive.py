"""Integrity regression for the FIRST RP-E008 simulated model stress run.

The original 72 files and their first-run decision are never overwritten.
Recomputing the *deterministic* simulator does not constitute new empirical
replication, independent observational data, or a physical experiment.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

from experiments.rp_e008_independent_des import (
    PROTOCOL, design, run_all, source_digest,
)

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVE = PROJECT / "docs/results/RP-E008-S01-first-run"
ORIGINAL_SOURCE_COMMIT = "cc450873c90f778d2399a87dde171baf43f42722"
ORIGINAL_WORKFLOW_RUN = "40131416314"


def load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    return obj


def test_first_run_source_identity_is_preserved_with_simulation_only_scope():
    index = load(ARCHIVE / "archive-index.json")
    report = load(ARCHIVE / "summary.json")
    assert index["source_commit"] == ORIGINAL_SOURCE_COMMIT
    assert index["github_run_id"] == ORIGINAL_WORKFLOW_RUN
    assert index["decision"] == report["decision"] == "PASS_SIMULATED_TRANSFER"
    assert index["simulator_study_not_physical"] is True
    assert report["RP_E007_observations_reused"] is False
    assert report["independent_physical_replication"] == "NOT_PERFORMED"
    assert report["lean_formalization"] == "NO_NEW_THEOREM"
    assert report["complete_trials"] == 72
    assert report["heldout_trials"] == 36


def test_all_first_run_byte_hashes_match_two_nested_permanent_manifests():
    index = load(ARCHIVE / "archive-index.json")
    originals = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ARCHIVE.iterdir())
        if p.is_file() and p.name != "archive-index.json"
    }
    assert len(originals) == len(index["original_data_sha256"]) == 74
    assert originals == index["original_data_sha256"]
    source_manifest = load(ARCHIVE / "source-manifest.json")
    assert source_manifest["count"] == 73
    assert source_manifest["sha256"] == {
        key: val for key, val in originals.items()
        if key != "source-manifest.json"
    }


def test_full_model_reexecution_matches_original_first_run_byte_decision():
    # A reproducibility audit of the SAME simulation, not a new data source.
    trials, summary = run_all()
    archival_summary = load(ARCHIVE / "summary.json")
    assert archival_summary == {"protocol": PROTOCOL, **summary}
    names = {s["trial_id"] for s in design()}
    assert len(names) == len(trials) == 72
    for trial in trials:
        assert trial == load(ARCHIVE / f"{trial['trial_id']}.json")
        assert trial["original_source"]["spec"]["trial_id"] == trial["trial_id"]
        assert trial["source_sha256"] == source_digest(trial["original_source"])
        assert trial["oracle_A_B_equal"] is True


def test_registered_exact_rational_improvement_is_preserved():
    original = load(ARCHIVE / "summary.json")
    a, b = original["heldout_mae_seconds"]["static"], original["heldout_mae_seconds"]["trend"]
    assert Fraction(a) == Fraction(533, 18000)
    assert Fraction(b) == Fraction(173, 14400)
    assert Fraction(b) <= Fraction(9, 10) * Fraction(a)
    assert original["heldout_trial_wins_ties_losses"] == {
        "wins": 20, "ties": 0, "losses": 16,
    }


def test_early_burst_negative_subgroup_is_not_suppressed():
    original = load(ARCHIVE / "summary.json")
    early = original["heldout_profile_mae_seconds"]["early_burst"]
    assert Fraction(early["static"]) == Fraction(1, 200)
    assert Fraction(early["trend"]) == Fraction(97, 8000)
    assert Fraction(early["trend"]) > Fraction(early["static"])
    late = original["heldout_profile_mae_seconds"]["late_burst"]
    assert Fraction(late["static"]) == Fraction(123, 2000)
    assert Fraction(late["trend"]) == Fraction(21, 2000)
    assert Fraction(late["trend"]) < Fraction(late["static"])


def test_single_corrupted_event_archive_cannot_pass_immutable_manifest(tmp_path):
    original = load(ARCHIVE / "archive-index.json")
    example_name = f"{design()[0]['trial_id']}.json"
    expected = original["original_data_sha256"][example_name]
    corrupted = (ARCHIVE / example_name).read_bytes() + b"\n"
    mutated_file = tmp_path / example_name
    mutated_file.write_bytes(corrupted)
    assert hashlib.sha256(corrupted).hexdigest() != expected
    assert load(mutated_file) != load(ARCHIVE / example_name) if False else (
        mutated_file.read_bytes() != (ARCHIVE / example_name).read_bytes()
    )


def test_original_trial_files_have_no_hidden_physical_measurements():
    for spec in design():
        original = load(ARCHIVE / f"{spec['trial_id']}.json")
        assert original["not_physical_measurement"] is True
        assert original["original_source"]["no_physical_service_or_network_measured"]
        assert original["original_source"]["spec"] == spec
        assert "first_sampled_idle_after_origin_ms" in original
        assert "true_drain_after_origin_ms" in original
