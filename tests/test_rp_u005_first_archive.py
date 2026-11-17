"""Keep the first synthetic RP-U005 result immutable and explicitly scoped."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments import rp_u005_functional_backlog as program

ORIGINAL_JSON = Path("docs/results/RP-U005-P01-first-run/audit.json")
EXPECTED_SIZE = 22361
EXPECTED_SHA256 = "75858a1431555ffca853e613c35f859d181a2f43c0f1f59a11043373f0acb81b"


def _read_original() -> dict:
    body = ORIGINAL_JSON.read_bytes()
    assert len(body) == EXPECTED_SIZE
    assert sha256(body).hexdigest() == EXPECTED_SHA256
    return json.loads(body)


def test_first_result_has_exact_bytes_and_frozen_eight_world_sequence():
    original = _read_original()
    assert original["protocol"] == "RP-U005-P01"
    assert original["protocol_only_commit"] == program.PREREG
    assert original["status"] == "FINITE_TOPOLOGY_INSUFFICIENT_FOR_RECOVERY_TIME"
    assert original["registered_cases"] == 8
    assert original["ticks_per_case"] == 12
    assert original["synthetic_data_only"] is True
    assert original["observed_human_or_field_records"] == 0
    assert len(original["worlds"]) == len(program.WORLDS)
    for world, row in zip(program.WORLDS, original["worlds"], strict=True):
        assert (row["pre_arrivals_each_failed_tick"],
                row["post_arrivals_each_restored_tick"]) == (
                world.pre, world.post)
        ticks = row["twelve_complete_observations"]
        assert len(ticks) == 12
        program.verify_history(world, ticks)
        assert ticks == program.fifo_event_oracle(world)
        assert row["independent_FIFO_and_recurrence_oracles_agree"] is True
        assert row["cumulative_arrivals"] == (
            row["cumulative_delivered"] + row["end_backlog"]
        )
        assert row["first_two_sample_zero_backlog_completion_tick"] == (
            program.first_two_empty_end_ticks(ticks)
        )


def test_h1_h2_and_negative_controls_cannot_be_relabelled():
    original = _read_original()
    assert original["registered_H1_supported"] is True
    assert original["registered_H1_recovery_tick_clean"] == 4
    assert original["registered_H1_recovery_tick_stressed"] == 6
    assert original["registered_H1_difference"] == 2
    assert original["registered_H2_balanced_backlog_persists"] is True
    assert all(original["negative_controls"].values())
    by_case = {
        (r["pre_arrivals_each_failed_tick"], r["post_arrivals_each_restored_tick"]): r
        for r in original["worlds"]
    }
    assert by_case[(2, 2)]["end_backlog"] == 3
    assert by_case[(2, 2)]["first_two_sample_zero_backlog_completion_tick"] is None
    assert by_case[(0, 2)]["end_backlog"] == 0
    assert by_case[(2, 0)]["first_two_sample_zero_backlog_completion_tick"] == 5
    assert by_case[(0, 3)]["end_backlog"] == 9
    assert by_case[(2, 3)]["end_backlog"] == 12
    assert original["new_physical_or_biological_law_proven"] is False


def test_index_points_to_original_workflow_and_sha_only():
    i = json.loads(Path(
        "docs/results/RP-U005-P01-first-run/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert i["original_json_size_bytes"] == EXPECTED_SIZE
    assert i["original_json_sha256"] == EXPECTED_SHA256
    assert i["original_status"] == "FINITE_TOPOLOGY_INSUFFICIENT_FOR_RECOVERY_TIME"
    assert i["registered_cases"] == 8
    assert i["primary_recovery_clean_tick"] == 4
    assert i["primary_recovery_stressed_tick"] == 6
    assert i["secondary_balanced_no_recovery_by_last_tick"] is True
    assert i["first_original_targeted_adversarial_tests_passed"] == 11
    assert i["pre_original_python311_tests_passed"] == 779
    assert i["pre_original_python312_tests_passed"] == 779
    assert i["pre_original_lean4_ci_conclusion"] == "success"
