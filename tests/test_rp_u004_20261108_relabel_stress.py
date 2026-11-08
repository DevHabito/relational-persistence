"""Deterministic stress: F1/F2 must be graph-isomorphism invariants.

This test deliberately does not compare repair policy selections: the
benchmark's numerical vertex-label tie breakers can change policy choices.
"""
from collections import defaultdict
from itertools import permutations

from experiments import rp_u004_recompute_20261108 as audit


def test_every_chosen_source_under_all_120_internal_label_permutations():
    groups = defaultdict(list)
    for graph in audit.source_graphs():
        groups[audit.degree_vector(graph)].append(graph)

    chosen = [
        graph
        for _, group in sorted(groups.items()) if len(group) > 1
        for graph in (min(group), max(group))
    ]
    assert len(chosen) == 570

    checks = 0
    for graph in chosen:
        original = audit.function_pair(graph, set(range(7)))
        for perm in permutations((1, 2, 3, 4, 5)):
            remap = dict(zip((1, 2, 3, 4, 5), perm))
            remap.update({0: 0, 6: 6})
            renamed = tuple(
                tuple(sorted((remap[a], remap[b]))) for a, b in graph
            )
            assert audit.function_pair(renamed, set(range(7))) == original
            checks += 1

    assert checks == 570 * 120 == 68_400
