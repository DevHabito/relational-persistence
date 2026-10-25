"""Pin the FIRST original RP-F006 synthetic certificate and all claim limits.

The same exact rational experiment may be replayed, but no replay can
replace this first source-report SHA, registered decision or protocol.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from experiments.rp_f006_queue_observability import audit_witness

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "docs/results/RP-F006-A01-first-run"
SHA_FIRST = "5b1a7a0bc5bda671ae542fc02d25d995df8bccc85f1929d2e8dcf73a932b4a5d"
FIRST_RUN = "40205665104"
FIRST_CODE = "406e92399da3f572f5c7852db016ba79421cca13"


def read_original():
    raw = (ORIGINAL / "audit.json").read_bytes()
    return raw, json.loads(raw), json.loads(
        (ORIGINAL / "archive-index.json").read_text("utf-8")
    )


def test_original_first_run_and_exact_sha_are_immutable():
    raw, audit, index = read_original()
    assert sha256(raw).hexdigest() == index["first_report_sha256"] == SHA_FIRST
    assert audit["protocol"] == index["protocol"] == "RP-F006-A01"
    assert audit["decision"] == index["first_verdict"] == (
        "FINITE_NONIDENTIFIABILITY_VERIFIED"
    )
    assert index["first_run_id"] == FIRST_RUN
    assert index["first_code_commit"] == FIRST_CODE
    assert audit["first_preregistered_code"] == (
        "3670d7d9bb15e69c6d354f056ecc4de87b27d55c"
    )


def test_original_exact_outcomes_have_neither_tuning_nor_rounded_tolerance():
    _, report, _ = read_original()
    assert report["short_target_wait_s"] == "1"
    assert report["long_target_wait_s"] == "100"
    assert report["full_pre_origin_observations_identical"] is True
    bound = report["exact_rational_obstruction"]
    assert bound["label_separation_s"] == "99"
    assert bound["equal_weighted_minimax_prediction_s"] == "101/2"
    assert bound["unavoidable_maximum_absolute_error_s"] == "99/2"
    assert bound["equal_weighting_is_synthetic_assumption_only"] is True
    assert Fraction(bound["unavoidable_maximum_absolute_error_s"]) == Fraction(99, 2)


def test_original_frozen_p01_style_heuristics_preserved_even_when_unfavorable():
    _, report, _ = read_original()
    models = report["frozen_candidate_and_baseline_predictions"]
    assert {name: case["prediction_s"] for name, case in models.items()} == {
        "history": "1", "static": "0", "trend": "0"
    }
    assert {name: case["long_abs_error_s"] for name, case in models.items()} == {
        "history": "99", "static": "100", "trend": "100"
    }
    assert all(report["registered_negative_controls"].values())


def test_both_independent_dispatch_replays_and_public_sources_agree():
    _, report, _ = read_original()
    ob = report["registered_common_observation"]
    assert ob["q_minus_120"] == ob["q_minus_60"] == ob["q_pre_target"] == 0
    assert ob["past_started_count"] == 1
    assert ob["historical_wait_median_s"] == "1"
    assert ob["historical_start_rate_per_s"] == "1/3540"
    assert ob["running_job_age_s"] == "30"
    assert ob["running_job_observed_busy"] is True
    assert len(ob["all_pre_origin_events"]) == 5
    assert len(ob["all_public_requests"]) == 3
    for name in ("world_short", "world_long"):
        item = report[name]
        assert item["no_overlapping_service"] is True
        assert item["fcfs_arrival_and_start_order"] is True
        assert item["independent_dispatch_replay_agrees"] is True
        assert item["work_conservation_before_origin_asserted"] is False
        assert item["global_work_conservation_claimed"] is False
        assert item["fixed_pre_origin_dispatch_lags_seconds"] == {
            "H": "1", "R": "1", "T": "0"
        }


def test_no_external_credibility_or_new_physics_claimed():
    _, report, index = read_original()
    assert report["source"] == "SYNTHETIC_ONLY"
    assert index["original_external_data_used"] is False
    assert index["existing_empirical_results_modified"] is False
    assert index["new_physical_law_claimed"] is False
    for label in (
        "empirical_external_validation_claimed", "new_queuing_theorem_claimed",
        "scalar_C_validated", "physical_law_claimed",
    ):
        assert report[label] is False


def test_complete_independent_rational_replay_matches_archived_report():
    _, prior, _ = read_original()
    assert audit_witness() == prior


def test_report_modification_would_break_first_sha():
    raw, _, _ = read_original()
    assert sha256(raw + b"\n").hexdigest() != SHA_FIRST


def test_first_archive_contains_only_the_original_report_and_manifest():
    assert sorted(p.name for p in ORIGINAL.iterdir()) == [
        "archive-index.json", "audit.json"
    ]
