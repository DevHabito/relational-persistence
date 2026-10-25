"""Permanent regression checks for FIRST RP-F007-A01 synthetic evidence.

This file authenticates one original GitHub Actions report, not a fresh
field experiment. All source observations are synthetic only.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from experiments.rp_f007_residual_bounds import audit

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "docs/results/RP-F007-A01-first-run"
FIRST_SHA = "113b641c150fd604a94451460ec65a4616809efc49919fe99313b4d1a66fff54"
FIRST_RUN_ID = "40229910510"
FIRST_CODE = "4023bb11aab25174524aaa80da6319f6bf9ff171"
PROTOCOL_SHA = "93d5dc4f2c99b663bfede40d515c2dc37bc14e14"


def first_original() -> tuple[dict, dict]:
    raw = (FIRST / "audit.json").read_bytes()
    index = json.loads((FIRST / "archive-index.json").read_text("utf-8"))
    assert sha256(raw).hexdigest() == FIRST_SHA
    return json.loads(raw), index


def test_frozen_protocol_first_run_and_byte_integrity():
    report, index = first_original()
    assert report["protocol"] == index["protocol"] == "RP-F007-A01"
    assert report["decision"] == index["original_decision"] == (
        "BOUNDED_STATE_MINIMAX_VERIFIED"
    )
    assert index["original_report_sha256"] == FIRST_SHA
    assert index["first_run_id"] == FIRST_RUN_ID
    assert index["first_code_commit"] == FIRST_CODE
    assert index["preregistration_commit"] == (
        report["frozen_preregistration_commit"]
    ) == PROTOCOL_SHA
    assert sorted(f.name for f in FIRST.iterdir()) == [
        "archive-index.json", "audit.json"
    ]


def test_exact_broad_family_has_all_470_admissible_waits():
    report, _ = first_original()
    broad = report["broad_family"]
    assert broad["admissible_world_count"] == 470
    assert broad["admissible_wait_min_seconds"] == 1
    assert broad["admissible_wait_max_seconds"] == 470
    assert broad["running_elapsed_seconds_at_origin"] == 30
    assert broad["public_hard_cap_seconds"] == 500
    assert broad["public_hard_cap_enforced"] is True
    assert broad["minimax_midpoint_prediction_s"] == "471/2"
    assert broad["sharp_minimax_worst_case_error_s"] == "469/2"
    assert broad["independent_analytic_error_bound_s"] == "469/2"
    assert broad["zero_prediction_worst_case_error_s"] == "470"


def test_exact_narrow_family_has_all_60_admissible_waits():
    report, _ = first_original()
    narrow = report["narrow_family"]
    assert narrow["admissible_world_count"] == 60
    assert narrow["admissible_wait_min_seconds"] == 1
    assert narrow["admissible_wait_max_seconds"] == 60
    assert narrow["running_elapsed_seconds_at_origin"] == 30
    assert narrow["public_hard_cap_seconds"] == 90
    assert narrow["public_hard_cap_enforced"] is True
    assert narrow["minimax_midpoint_prediction_s"] == "61/2"
    assert narrow["sharp_minimax_worst_case_error_s"] == "59/2"
    assert narrow["independent_analytic_error_bound_s"] == "59/2"
    assert narrow["zero_prediction_worst_case_error_s"] == "60"


def test_formal_caps_and_minimax_are_not_conflated_with_empirical_loss():
    original, _ = first_original()
    assert original["minimax_error_decrease_s"] == "205"
    assert original["narrow_over_broad_minimax_error_ratio"] == "59/469"
    assert Fraction("469/2") - Fraction("59/2") == 205
    assert original["public_cap_change_means_public_observation_changes"] is True
    assert original["source"] == "SYNTHETIC_ONLY"
    assert original["no_external_prediction_data_used"] is True
    assert original["no_original_rp_e010_or_rp_e011_result_changed"] is True
    assert original["novel_queuing_theorem_claimed"] is False
    assert original["physical_law_or_scalar_C_claimed"] is False


def test_all_530_independently_checked_and_observations_frozen():
    original, _ = first_original()
    broad, narrow = original["broad_family"], original["narrow_family"]
    assert broad["admissible_world_count"] + narrow["admissible_world_count"] == 530
    for family in (broad, narrow):
        assert family["public_observations_identical_in_family"] is True
        assert family["independent_fcfs_dispatch_replay_for_every_world"] is True
        assert family["three_queue_state_oracles_for_every_world"] is True
        assert family["public_observation"]["running_job_age_s"] == "30"
        assert family["public_observation"]["running_walltime_limit_is_enforced"] is True
        assert len(family["public_observation"]["all_pre_origin_events"]) == 5
        assert family["public_observation"]["q_minus_120"] == 0
        assert family["public_observation"]["q_minus_60"] == 0
        assert family["public_observation"]["q_pre_target"] == 0
    assert broad["public_observation"] != narrow["public_observation"]
    assert broad["public_observation"]["all_pre_origin_events"] == (
        narrow["public_observation"]["all_pre_origin_events"]
    )


def test_all_precommitted_adversarial_controls_retained():
    original, index = first_original()
    assert original["registered_controls"] == {
        "advertised_only_500_not_a_guarantee": True,
        "changed_dispatch_rejected": True,
        "future_running_completion_oracle_is_not_public": True,
        "hard_cap_overrun_rejected": True,
        "unregistered_future_arrival_rejected": True,
    }
    assert index["external_dataset_downloaded"] is False
    assert index["existing_first_runs_modified"] is False
    assert index["new_physical_law_claimed"] is False


def test_exact_rational_complete_replay_matches_first_report():
    original, _ = first_original()
    assert audit() == original


def test_one_byte_mutation_changes_report_sha():
    raw = (FIRST / "audit.json").read_bytes()
    assert sha256(raw + b"\n").hexdigest() != FIRST_SHA
