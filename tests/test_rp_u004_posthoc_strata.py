"""Regression guards for a retrospective U004 subgroup audit.

These are post-result consistency tests, not preregistered subgroup wins.
The original experiment and archived first-run bytes are never rewritten.
"""

from __future__ import annotations

import pytest

from experiments.rp_u004_posthoc_diagnostics import analyze, read_frozen_archive


@pytest.fixture(scope="module")
def frozen_original():
    return read_frozen_archive()


def test_posthoc_degree_classification_matches_original_case_records(frozen_original):
    report = analyze(frozen_original)
    assert report["scenarios"] == 2850
    assert report["F2_case_differences"] == {0: 2784, 1: 39, 2: 20, 3: 7}
    assert report["F1_case_differences"] == {0: 2844, 1: 6}
    assert report["F2_total_difference"] == 100
    assert report["F1_total_difference"] == 6

    strata = report["F2_by_original_failed_vertex_degree"]
    assert {degree: row["scenarios"] for degree, row in strata.items()} == {
        "1": 920, "2": 800, "3": 520,
        "4": 350, "5": 200, "6": 60,
    }
    assert {degree: row["F2_wins"] for degree, row in strata.items()} == {
        "1": 0, "2": 0, "3": 25,
        "4": 18, "5": 23, "6": 0,
    }
    assert {degree: row["F2_total_difference"] for degree, row in strata.items()} == {
        "1": 0, "2": 0, "3": 25,
        "4": 30, "5": 45, "6": 0,
    }
    assert sum(row["scenarios"] for row in strata.values()) == 2850
    assert sum(row["F2_wins"] for row in strata.values()) == 66
    assert sum(row["F2_total_difference"] for row in strata.values()) == 100


def test_posthoc_result_preserves_original_negative_controls(frozen_original):
    report = analyze(frozen_original)
    assert report["F2_by_initial_function"]["absent"] == {
        "scenarios": 2140, "F2_wins": 0, "F2_ties": 2140,
        "F2_losses": 0, "F2_total_difference": 0,
    }
    assert report["F2_by_initial_function"]["present"] == {
        "scenarios": 710, "F2_wins": 66, "F2_ties": 644,
        "F2_losses": 0, "F2_total_difference": 100,
    }
    assert report["equal_repair_budget_cases"] == 2850
    assert report["greedy_objective_orders_identical_cases"] == 2850
    assert report["lookahead_objective_orders_identical_cases"] == 2850
    assert report["lookahead_at_both_reported_offline_bounds"] == 2850
    assert report["observed_real_world_rows"] == 0
    assert report["new_preregistered_hypothesis"] is False
    assert report["new_lean_theorem_claimed"] is False
    assert report["status"].startswith("RETROSPECTIVE_")


def test_a_tampered_case_cannot_match_the_original_aggregate(frozen_original):
    value = frozen_original["cases"][0]["policies"]["LOOKAHEAD2_F2"]
    original_value = value["F2_uptime"]
    try:
        value["F2_uptime"] += 1
        with pytest.raises(ValueError, match="published aggregates"):
            analyze(frozen_original)
    finally:
        value["F2_uptime"] = original_value


def test_absent_original_f2_cannot_hide_a_positive_repair_score(frozen_original):
    case = next(case for case in frozen_original["cases"] if case["original_F2"] == 0)
    record = case["policies"]["ASC"]
    original = record["F2_uptime"]
    try:
        record["F2_uptime"] = 1
        with pytest.raises(ValueError, match="F2 appeared under subset-only repair"):
            analyze(frozen_original)
    finally:
        record["F2_uptime"] = original
