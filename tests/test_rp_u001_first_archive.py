"""Immutable first-original RP-U001 finite network experiment evidence.

No raw ecological data exist for this exact finite experiment. These
checks anchor the original automatic GitHub Actions audit by SHA-256
and do not rerun/retune the registered graph after seeing its result.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "docs/results/RP-U001-A01-first-run"
ORIGINAL_SHA = "ac1c94e2c71624ccf4fd3e54c6df4f8ca2f166d78975c625d4d0b533e2615ab0"
PREREG = "81ce6d186c3ba1a86c25297a30fb0f6a27cb7d4e"
CODE_SHA = "01023aaeb77059697f7cbcb73637518934d724cd"
FIRST_ID = "40490582350"


def audited():
    raw = (ORIGINAL / "audit.json").read_bytes()
    data = json.loads(raw)
    index = json.loads((ORIGINAL / "archive-index.json").read_text("utf-8"))
    return raw, data, index


def test_first_original_json_bytes_and_git_provenance_permanently_pinned():
    raw, data, index = audited()
    assert sha256(raw).hexdigest() == ORIGINAL_SHA
    assert index["first_json_sha256"] == ORIGINAL_SHA
    assert data["protocol"] == index["protocol"] == "RP-U001-A01"
    assert data["preregistration_commit"] == index["frozen_protocol_commit"] == PREREG
    assert data["original_code_commit"] == index["original_code_commit"] == CODE_SHA
    assert data["first_run_id"] == index["first_run_id"] == FIRST_ID
    assert data["original_decision"] == index["original_result"] == (
        "FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED"
    )
    assert data["errors"] == []
    assert sorted(f.name for f in ORIGINAL.iterdir()) == [
        "archive-index.json", "audit.json"
    ]


def test_frozen_source_graph_baseline_and_exact_counts_at_all_damage_levels():
    _, data, _ = audited()
    assert sorted(data["graphs"]) == ["A", "B"]
    for name, expected in {
        "A": [1, 4, 2, 0, 0],
        "B": [1, 3, 2, 0, 0],
    }.items():
        graph = data["graphs"][name]
        assert graph["vertices"] == 6
        assert graph["edges"] == 7
        assert graph["source_terminal_degree"] == 2
        assert graph["target_terminal_degree"] == 2
        assert graph["counts_by_removed_vertex_count"] == expected
        assert graph["relabeling_casewise_verified"] is True
        assert [row["tested_subsets"] for row in
                graph["all_full_sweep_records"]] == [1, 4, 6, 4, 1]
        assert [row["function_retained_subsets"] for row in
                graph["all_full_sweep_records"]] == expected
        assert sum(len(row["exact_set_outcomes"]) for row in
                   graph["all_full_sweep_records"]) == 16


def test_first_original_reachability_survives_single_failure_differently():
    _, data, _ = audited()
    a = data["graphs"]["A"]["all_full_sweep_records"][1]["exact_set_outcomes"]
    b = data["graphs"]["B"]["all_full_sweep_records"][1]["exact_set_outcomes"]
    assert [(x["removed"], x["bfs_reachable"]) for x in a] == [
        ([1], True), ([2], True), ([3], True), ([4], True)
    ]
    assert [(x["removed"], x["bfs_reachable"]) for x in b] == [
        ([1], True), ([2], False), ([3], True), ([4], True)
    ]
    assert all(x["bfs_reachable"] == x["dfs_reachable"] for x in a + b)
    assert set(x["surviving_vertex_fraction"] for x in a + b) == {"5/6"}


def test_registered_two_node_negative_control_must_not_be_suppressed():
    _, data, _ = audited()
    a = data["graphs"]["A"]["all_full_sweep_records"][2]
    b = data["graphs"]["B"]["all_full_sweep_records"][2]
    assert (a["function_retention_fraction"],
            b["function_retention_fraction"]) == ("1/3", "1/3")
    assert a["function_retained_subsets"] == b["function_retained_subsets"] == 2
    assert data["negative_control_strict_superiority_all_k"] is True


def test_stronger_two_path_function_refutes_generic_continuity_claim():
    _, data, _ = audited()
    a = data["registered_two_disjoint_path_control"]["A"]
    b = data["registered_two_disjoint_path_control"]["B"]
    assert a["initial_has_two_disjoint_routes"] is True
    assert b["initial_has_two_disjoint_routes"] is False
    assert a["single_deletion_cases_retaining_two_disjoint_routes"] == 0
    assert b["single_deletion_cases_retaining_two_disjoint_routes"] == 0


def test_exact_finite_toy_cannot_be_described_as_real_empirical_law():
    _, data, index = audited()
    assert data["measured_ecological_or_technological_data_used"] is False
    assert data["empirical_bio_function_preservation_verified"] is False
    assert data["cross_domain_physical_law_claimed"] is False
    assert data["new_mathematical_principle_claimed"] is False
    assert "no recovery or dynamics" in data["scope"]
    assert index["real_external_domain_rows_read"] == 0
    assert index["new_universal_scientific_law_claimed"] is False
    assert index["original_negative_external_forecasts_changed"] is False


def test_sha_mutation_rejected():
    raw, _, _ = audited()
    assert sha256(raw + b"\n").hexdigest() != ORIGINAL_SHA
