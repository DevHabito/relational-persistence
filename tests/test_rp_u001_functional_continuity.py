"""RP-U001-A01 — adversarial tests for finite functional continuity.

Only fixed artificial networks. Source-authorized predictions are in
docs/preregistration/RP-U001-A01.md, frozen before implementation.
No ecological data or inference to actual Amazon regrowth.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
import json

import pytest

from experiments import rp_u001_functional_continuity as u


def graphs():
    return {name: u.canonical_edges(edges)
            for name, edges in u.GRAPH_EDGES.items()}


def test_registered_source_ref_and_graph_invariants():
    assert u.PREREG == "81ce6d186c3ba1a86c25297a30fb0f6a27cb7d4e"
    for edges in graphs().values():
        u.check_baseline(edges)
        assert len(edges) == 7
        assert len({v for e in edges for v in e}) == 6
        assert sum(0 in edge for edge in edges) == 2
        assert sum(5 in edge for edge in edges) == 2


def test_exhaust_all_subsets_independent_oracles_at_every_k():
    for name, edges in graphs().items():
        for k, expected in enumerate(u.REGISTERED_COUNTS[name]):
            sets = u.subsets_of_size(k)
            assert len(sets) == (1, 4, 6, 4, 1)[k]
            outcomes = []
            for removed in sets:
                bfs = u.reachable_bfs(edges, frozenset(removed))
                dfs = u.reachable_paths(edges, frozenset(removed))
                assert bfs is dfs
                outcomes.append(bfs)
            assert sum(outcomes) == expected


def test_single_component_contrast_at_identical_vertex_retention():
    a, b = graphs()["A"], graphs()["B"]
    assert all(u.reachable_bfs(a, {vertex}) for vertex in u.REMOVABLE)
    assert [u.reachable_bfs(b, {vertex}) for vertex in u.REMOVABLE] == [
        True, False, True, True
    ]
    assert Fraction(5, 6) == Fraction(6 - 1, 6)


def test_control_refutes_any_strict_superiority_across_all_loss_sizes():
    a, b = graphs()["A"], graphs()["B"]
    for k in (0, 2, 3, 4):
        left = sum(u.reachable_bfs(a, set(removal))
                   for removal in u.subsets_of_size(k))
        right = sum(u.reachable_bfs(b, set(removal))
                    for removal in u.subsets_of_size(k))
        assert left == right
    assert sum(u.reachable_bfs(a, set(removal))
               for removal in u.subsets_of_size(2)) == 2


def test_operational_function_definition_changes_original_result():
    a, b = graphs()["A"], graphs()["B"]
    assert u.two_vertex_disjoint_paths(a, set())
    assert not u.two_vertex_disjoint_paths(b, set())
    for network in (a, b):
        assert sum(u.two_vertex_disjoint_paths(network, {removed})
                   for removed in u.REMOVABLE) == 0


def test_fixed_relabeling_never_changes_per_case_reachability():
    assert set(u.RELABEL) == set(u.VERTICES)
    assert set(u.RELABEL.values()) == set(u.VERTICES)
    for edges in graphs().values():
        permuted = u.relabel_edges(edges)
        assert len(permuted) == len(edges)
        for k in range(5):
            for removed in u.subsets_of_size(k):
                mapped = {u.RELABEL[v] for v in removed}
                assert u.reachable_bfs(edges, set(removed)) == (
                    u.reachable_bfs(permuted, mapped)
                )
                assert u.reachable_paths(edges, set(removed)) == (
                    u.reachable_paths(permuted, mapped)
                )


def test_invalid_terminal_deletion_is_rejected_by_both_oracles():
    edges = graphs()["A"]
    for removed in ({0}, {5}, {0, 5}):
        with pytest.raises(ValueError):
            u.reachable_bfs(edges, removed)
        with pytest.raises(ValueError):
            u.reachable_paths(edges, removed)


def test_invalid_edges_duplicate_self_loop_and_outside_six_nodes():
    with pytest.raises(ValueError, match="Duplicate"):
        u.canonical_edges([(0, 1), (1, 0)])
    with pytest.raises(ValueError, match="not a simple"):
        u.canonical_edges([(1, 1)])
    with pytest.raises(ValueError, match="not a simple"):
        u.canonical_edges([(0, 6)])


def test_nonregistered_graph_edges_fail_topology_control():
    edges = u.canonical_edges([(0, 1), (1, 5)])
    with pytest.raises(ValueError, match="edge count"):
        u.check_baseline(edges)


def test_outcome_cannot_be_forced_by_fake_independent_oracle(monkeypatch):
    monkeypatch.setattr(u, "reachable_paths", lambda edges, removed: False)
    with pytest.raises(AssertionError, match="Independent"):
        u.exhaustive_one_graph(graphs()["A"])


def test_perturbed_graph_expected_counts_must_be_rejected(monkeypatch):
    fake = dict(u.GRAPH_EDGES)
    fake["B"] = fake["A"]
    monkeypatch.setattr(u, "GRAPH_EDGES", fake)
    result = u.audit()
    assert result["original_decision"] == "REGISTERED_FINITE_CONTRAST_REJECTED"
    assert result["errors"]
    assert result["new_mathematical_principle_claimed"] is False


def test_wrong_registered_k2_control_provokes_failure(monkeypatch):
    modified = dict(u.REGISTERED_COUNTS)
    modified["A"] = (1, 4, 3, 0, 0)
    monkeypatch.setattr(u, "REGISTERED_COUNTS", modified)
    result = u.audit()
    assert result["original_decision"] == "REGISTERED_FINITE_CONTRAST_REJECTED"
    assert result["errors"]


def test_every_original_failure_record_preserved_and_program_refuses_overwrite(tmp_path):
    original = u.audit()
    assert original["original_decision"] == "FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED"
    assert original["errors"] == []
    assert original["negative_control_strict_superiority_all_k"] is True
    assert original["cross_domain_physical_law_claimed"] is False
    assert original["measured_ecological_or_technological_data_used"] is False
    assert original["empirical_bio_function_preservation_verified"] is False
    assert original["new_mathematical_principle_claimed"] is False
    for name in ("A", "B"):
        assert original["graphs"][name]["relabeling_casewise_verified"] is True
        assert original["graphs"][name]["counts_by_removed_vertex_count"] == (
            list(u.REGISTERED_COUNTS[name])
        )
        assert len(original["graphs"][name]["all_full_sweep_records"]) == 5
        assert sum(len(x["exact_set_outcomes"]) for x in
                   original["graphs"][name]["all_full_sweep_records"]) == 16
    saved = tmp_path / "single_original.json"
    saved.write_text(json.dumps(original))
    with pytest.raises(SystemExit, match="refuse replacement"):
        # Run the entry function exactly as a user would, with a
        # destination that already contains the first output.
        monkeypatch = pytest.MonkeyPatch()
        try:
            monkeypatch.setattr("sys.argv", ["run", "--output", str(saved)])
            u.main()
        finally:
            monkeypatch.undo()


def test_lexicographic_subset_enumeration_prevents_favorable_selection():
    expected = (tuple(), (1,), (2,), (3,), (4,))
    assert u.subsets_of_size(0) == (expected[0],)
    assert u.subsets_of_size(1) == expected[1:]
    assert u.subsets_of_size(2) == (
        (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)
    )


def test_function_not_a_population_statistic_or_an_equilibrium():
    result = u.audit()
    assert result["original_decision"] == "FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED"
    assert "no recovery or dynamics" in result["scope"]
    assert result["graphs"]["A"]["all_full_sweep_records"][1][
        "function_retention_fraction"] == "1"
    assert result["graphs"]["B"]["all_full_sweep_records"][1][
        "function_retention_fraction"] == "3/4"
    assert result["graphs"]["A"]["all_full_sweep_records"][2][
        "function_retention_fraction"] == "1/3"
    assert result["graphs"]["B"]["all_full_sweep_records"][2][
        "function_retention_fraction"] == "1/3"
