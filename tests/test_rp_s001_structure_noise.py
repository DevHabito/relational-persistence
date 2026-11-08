"""RP-S001-P01 adverse and independent finite reliability tests.

Tests are synthetic-only; the registered source search result is first
printed and archived by the separate one-time Actions workflow.
"""
from fractions import Fraction
from itertools import combinations
import subprocess
import sys

import pytest

from experiments import rp_s001_structure_noise as study


def test_source_edge_universe_and_complete_unfiltered_combinatorics():
    assert study.VERTICES == tuple(range(6))
    assert len(study.EDGES) == 14
    assert (0, 5) not in study.EDGES
    assert len(tuple(combinations(study.EDGES, 8))) == study.TOTAL_SOURCE_GRAPHS == 3003
    assert len(study.FAIL_SUBSETS) == 28
    assert all(len(subset) == 2 for subset in study.FAIL_SUBSETS)
    assert len(set(study.FAIL_SUBSETS)) == 28


def test_inadmissible_or_wrongly_canonical_graph_rejected():
    accepted = tuple(study.EDGES[:8])
    assert study.graph_valid_basic(accepted)
    assert not study.graph_valid_basic(accepted + ((0, 5),))
    assert not study.graph_valid_basic(accepted[:-1])
    assert not study.graph_valid_basic(tuple(reversed(accepted)))
    assert not study.graph_valid_basic(tuple(sorted(accepted[:-1] + (accepted[0],))))
    with pytest.raises(study.StudyError, match="INVALID_GRAPH"):
        study.certified_survival_count(accepted[:-1])


def test_independent_bfs_dfs_stress_across_canonical_eight_edge_fixtures():
    for graph in combinations(study.EDGES, 8):
        # Deterministic sparse set of complete graphs covering the source universe.
        if graph[0] != (0, 1):
            continue
        for subset in study.FAIL_SUBSETS:
            remaining = study.remove_by_indices(graph, subset)
            assert study.bfs_reachable(remaining) == study.dfs_path_reachable(remaining)
        # This is a test, not the original registered all-graph source result.
        break


def test_remove_subset_checks_duplicate_and_out_of_range():
    graph = tuple(study.EDGES[:8])
    with pytest.raises(study.StudyError, match="INVALID_REMOVAL"):
        study.remove_by_indices(graph, (1, 1))
    with pytest.raises(study.StudyError, match="INVALID_REMOVAL"):
        study.remove_by_indices(graph, (8,))
    assert study.remove_by_indices(graph, (0, 2)) == tuple(
        e for i, e in enumerate(graph) if i not in (0, 2))


def test_source_mincut_separately_matches_deletion_fixtures():
    candidate = tuple(study.EDGES[:8])
    # This is an arbitrary valid 8-edge source candidate, not a selected result.
    assert study.exact_st_edge_cut(candidate) == study.deletion_mincut_check(candidate)
    assert 0 <= study.exact_st_edge_cut(candidate) <= 2


def test_exact_temporal_dependence_with_identical_single_tick_marginals():
    fixed = tuple([True]*14 + [False]*14)
    output = study.temporal_controls(fixed)
    assert output["one_time_survival"] == {"numerator": 1, "denominator": 2}
    assert output["frozen_two_edge_failure_set_sustained_3"] == {
        "numerator": 1, "denominator": 2}
    assert output["independent_new_failure_set_each_tick_sustained_3"] == {
        "numerator": 1, "denominator": 8}
    assert output["three_step_independent_successful_schedules"] == 14**3
    assert output["three_step_total_schedules"] == 28**3
    assert output["strict_temporal_gap"] is True
    assert output["same_uniform_per_tick_failure_distribution"] is True
    assert output["emergent_physical_time_tested"] is False


@pytest.mark.parametrize("successful,gap", [(0, False), (1, True),
                                             (14, True), (27, True),
                                             (28, False)])
def test_temporal_gap_positive_only_for_nondegenerate_one_time_fractions(successful,gap):
    outcomes = tuple(i < successful for i in range(28))
    output = study.temporal_controls(outcomes)
    assert output["strict_temporal_gap"] is gap
    assert Fraction(**{
        "numerator": output["one_time_survival"]["numerator"],
        "denominator": output["one_time_survival"]["denominator"],
    }) == Fraction(successful, 28)


def test_incorrect_temporal_schedule_universe_rejected():
    with pytest.raises(study.StudyError, match="TEMPORAL_INPUT"):
        study.temporal_controls((True, False))
    with pytest.raises(study.StudyError, match="TEMPORAL_INPUT"):
        study.temporal_controls(tuple([True]*29))


def test_min_cut_is_not_random_reliability_by_definition():
    # A single deleted edge cannot sever this two-route fixture.
    graph = tuple(sorted((
        (0,1),(0,2),(1,3),(2,4),(3,5),(4,5),(1,2),(3,4)
    )))
    assert study.graph_valid_basic(graph)
    assert study.connected_whole_graph(graph)
    assert study.exact_st_edge_cut(graph) == 2
    assert study.deletion_mincut_check(graph) == 2
    assert all(study.bfs_reachable(study.remove_by_indices(graph,(i,)))
               for i in range(8))
    k, checks = study.certified_survival_count(graph)
    assert k == sum(checks)
    assert len(checks) == 28
    assert 0 < k < 28


def test_validation_survives_python_optimized_interpreter():
    probe = (
        "from experiments.rp_s001_structure_noise import "
        "remove_by_indices, EDGES, StudyError;"
        "g=tuple(EDGES[:8]);"
        "\ntry:\n remove_by_indices(g,(1,1)); print('BAD')"
        "\nexcept StudyError:\n print('GUARD_ACTIVE')"
    )
    call = subprocess.run([sys.executable,"-O","-c",probe],
                          capture_output=True,text=True,timeout=30,check=False)
    assert call.returncode == 0
    assert call.stdout.strip() == "GUARD_ACTIVE"
