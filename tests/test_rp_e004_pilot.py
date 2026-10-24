"""Synthetic-only regression checks for the frozen RP-E004-P01 pilot.

These tests don't constitute independent physical instrument validation.
"""

import pytest

from experiments.rp_e004_pilot import (
    RECOVERY_DWELL_NS,
    TRIALS,
    SEED,
    evaluate_feasibility,
    sustained_idle_start,
)


def test_idle_requires_complete_sustained_dwell():
    x = [
        (10, False),
        (20, True),
        (20 + RECOVERY_DWELL_NS - 1, True),
    ]
    assert sustained_idle_start(x, 20, RECOVERY_DWELL_NS) is None
    x.append((20 + RECOVERY_DWELL_NS, True))
    assert sustained_idle_start(x, 20, RECOVERY_DWELL_NS) == 20


def test_intermediate_queue_activity_resets_recovery_clock():
    r = [
        (100, True), (200, False), (300, True),
        (300 + RECOVERY_DWELL_NS - 1, True),
    ]
    assert sustained_idle_start(r, 0, RECOVERY_DWELL_NS) is None
    r.append((300 + RECOVERY_DWELL_NS, True))
    assert sustained_idle_start(r, 0, RECOVERY_DWELL_NS) == 300


def test_idle_before_external_intervention_end_is_ignored():
    x = [(10, True), (10 + RECOVERY_DWELL_NS, True)]
    assert sustained_idle_start(x, 10 + RECOVERY_DWELL_NS + 1, RECOVERY_DWELL_NS) is None


def test_monitor_rejects_nonmonotonic_sample_times():
    with pytest.raises(ValueError, match="Nonmonotonic"):
        sustained_idle_start([(10, True), (9, True)], 0, RECOVERY_DWELL_NS)
    with pytest.raises(ValueError, match="Nonmonotonic"):
        sustained_idle_start([(10, True), (10, True)], 0, RECOVERY_DWELL_NS)


def test_all_three_trials_required():
    positive = {"positive": True, "schema_verdict": "STRUCTURALLY_ADMISSIBLE"}
    sham = {"positive": False, "schema_verdict": "SHAM_UNDEFINED_INDEX"}
    assert evaluate_feasibility([positive, positive, sham]) == "PROCEED_TO_SEPARATE_STUDY_DESIGN"
    assert evaluate_feasibility([positive, sham]) == "STOP_INSTRUMENTATION_UNRELIABLE"


def test_missing_sham_or_positive_stops():
    positive = {"positive": True, "schema_verdict": "STRUCTURALLY_ADMISSIBLE"}
    sham = {"positive": False, "schema_verdict": "SHAM_UNDEFINED_INDEX"}
    assert evaluate_feasibility([positive, positive, positive]) == "STOP_INSTRUMENTATION_UNRELIABLE"
    assert evaluate_feasibility([positive, sham, sham]) == "STOP_INSTRUMENTATION_UNRELIABLE"


def test_zero_sham_never_assigned_defined_index():
    proper = {"positive": False, "schema_verdict": "SHAM_UNDEFINED_INDEX"}
    wrong = {"positive": False, "schema_verdict": "STRUCTURALLY_ADMISSIBLE"}
    positive = {"positive": True, "schema_verdict": "STRUCTURALLY_ADMISSIBLE"}
    assert evaluate_feasibility([positive, positive, proper]) == "PROCEED_TO_SEPARATE_STUDY_DESIGN"
    assert evaluate_feasibility([positive, positive, wrong]) == "STOP_INSTRUMENTATION_UNRELIABLE"


def test_frozen_schedule_contains_two_interventions_and_one_sham():
    import random

    first = list(TRIALS)
    second = list(TRIALS)
    random.Random(SEED).shuffle(first)
    random.Random(SEED).shuffle(second)
    assert first == second
    assert len(first) == 3
    assert sum(item.startswith("positive") for item in first) == 2
    assert sum(item.startswith("sham") for item in first) == 1
