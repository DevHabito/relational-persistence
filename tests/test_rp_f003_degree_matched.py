"""Adversarial and independent regression checks for RP-F003-A01."""

from fractions import Fraction
import json
from pathlib import Path

import pytest

from experiments.rp_f003_degree_matched import (
    DENOMINATOR,
    EDGES,
    audit_matrix,
    compute,
    edges_of,
    energy_numerator,
    graph_data,
    relabel_reverse,
    require_matched_degrees,
    trace_power_40,
)


RESULT_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "results" / "RP-F003-A01.json"
)


def test_frozen_exhaustive_result_matches_committed_bytes():
    recorded = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    recomputed = compute()
    assert recomputed == recorded
    assert recomputed["connected_masks"] == 26704
    assert len(recomputed["degree_group_sizes"]) == 68
    assert sum(recomputed["degree_group_sizes"].values()) == 26704
    assert recomputed["decision"] == "PASS_EQUAL_DEGREES_INSUFFICIENT"


@pytest.mark.parametrize("mask", [0, 700, 760, (1 << len(EDGES)) - 1])
def test_independent_trace_computation(mask):
    _, _, matrix = graph_data(mask)
    assert energy_numerator(matrix) + 10**40 == trace_power_40(matrix)


def test_explicit_matched_degree_pair_has_exact_separation():
    require_matched_degrees(700, 760)
    first = Fraction(energy_numerator(graph_data(700)[2]), DENOMINATOR)
    second = Fraction(energy_numerator(graph_data(760)[2]), DENOMINATOR)
    assert second - first == Fraction(
        525983549967404698928210582872418468781,
        12500000000000000000000000000000000000000,
    )
    assert second - first >= Fraction(1, 100)


@pytest.mark.parametrize("mask", [700, 760])
def test_reverse_relabel_does_not_change_exact_outcome(mask):
    original_connected, original_degrees, original_matrix = graph_data(mask)
    reversed_connected, reversed_degrees, reversed_matrix = graph_data(relabel_reverse(mask))
    assert original_connected and reversed_connected
    assert original_degrees == reversed_degrees
    assert energy_numerator(original_matrix) == energy_numerator(reversed_matrix)


def test_registered_extreme_controls():
    complete = (1 << len(EDGES)) - 1
    assert not graph_data(0)[0]
    assert graph_data(complete)[0]
    assert Fraction(energy_numerator(graph_data(0)[2]), DENOMINATOR) == 1
    assert Fraction(energy_numerator(graph_data(complete)[2]), DENOMINATOR) == Fraction(2, 5) ** 40


@pytest.mark.parametrize("mask", [-1, 1 << len(EDGES), 3.5])
def test_out_of_range_edge_mask_rejected(mask):
    with pytest.raises(ValueError):
        edges_of(mask)


def test_unsupported_graph_size_rejected():
    with pytest.raises(ValueError):
        graph_data(700, vertex_count=7)


def test_mismatched_degree_and_tampered_edge_rejected():
    with pytest.raises(ValueError):
        require_matched_degrees(700, (1 << len(EDGES)) - 1)
    with pytest.raises(ValueError):
        require_matched_degrees(700, 700 ^ 1)


def test_malformed_or_mutated_matrix_rejected():
    edges = edges_of(700)
    _, _, matrix = graph_data(700)
    audit_matrix(matrix, edges)

    tampered = [list(row) for row in matrix]
    tampered[0][0] += 1
    with pytest.raises(ValueError):
        audit_matrix(tuple(tuple(row) for row in tampered), edges)

    with pytest.raises(ValueError):
        audit_matrix(matrix[:-1], edges)
