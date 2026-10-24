"""Immutable-observation summary consistency checks for RP-E002-A01.

This validates the archived negative verdict; it NEVER refits parameters
or changes the frozen protocol based on the held-out result.
"""

import json
import math
from pathlib import Path

RESULT = Path(__file__).resolve().parents[1] / "docs/results/RP-E002-A01.json"


def load():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_registered_negative_verdict_is_not_relabelled_positive():
    result = load()
    assert result["decision"] == "H0_not_rejected"
    assert result["verdict"] == "FROZEN_H1_FAILURE"
    assert sorted(result["primary_results"]) == ["15_min", "30_min", "60_min"]
    assert all(not row["passes_both"] for row in result["primary_results"].values())


def test_all_six_registered_inequalities_fail_conjunction():
    result = load()
    threshold = result["thresholds"]["relative_mae_gain_vs_best_temporal_baseline"]
    assert threshold == result["thresholds"]["relative_mae_gain_vs_independently_tuned_permuted_graph"] == 0.01
    assert not any(
        row["relative_gain_vs_best_temporal_baseline"] >= threshold
        and row["relative_gain_vs_permuted_graph"] >= threshold
        for row in result["primary_results"].values()
    )


def test_recorded_mae_gains_are_consistent_with_rounding():
    result = load()
    for horizon, row in result["primary_results"].items():
        mae = row["sensor_balanced_mae"]
        baseline = min(mae["persistence"], mae["seasonal"])
        against_base = (baseline - mae["graph"]) / baseline
        against_placebo = (mae["permuted_graph"] - mae["graph"]) / mae["permuted_graph"]
        assert math.isclose(against_base, row["relative_gain_vs_best_temporal_baseline"], abs_tol=5e-6)
        assert math.isclose(against_placebo, row["relative_gain_vs_permuted_graph"], abs_tol=5e-6)


def test_source_provenance_and_population_are_frozen():
    result = load()
    assert result["source"]["md5"] == "d3adaa79856bf610f25558fc242c7190"
    assert result["provenance"]["preregistration_commit"] == "45866da450ce0443fc990a0ab01b6be8a853f13f"
    assert result["provenance"]["execution_commit"] == "4994f46e96ced0d0057c74c68cbb0df19d997fba"
    assert result["provenance"]["rows"] == 34272
    assert result["provenance"]["sensors"] == 207
    assert result["original_scalar_index_identification"] == "NOT_IDENTIFIED"
    assert not result["provenance"]["raw_data_in_git"]


def test_zero_inclusive_alternative_is_not_reported_as_primary_success():
    result = load()
    for horizon in result["zero_inclusive_secondary_fixed_lambdas"].values():
        assert horizon["graph_mae"] > horizon["persistence_mae"]
