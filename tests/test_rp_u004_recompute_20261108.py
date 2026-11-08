"""Retrospective RP-U004 independent recomputation and adversarial controls.

These regressions check an independently written implementation against the
previously frozen outcome. They are NOT a new blinded hypothesis test.
"""
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

import pytest

from experiments import rp_u004_recompute_20261108 as independent


ARCHIVE = Path("docs/results/RP-U004-P01-first-run")
WITNESS = (
    (0, 4), (0, 5), (1, 4), (2, 4),
    (3, 4), (3, 5), (3, 6), (4, 6),
)


@pytest.fixture(scope="module")
def recomputed():
    return independent.recompute()


def test_independent_source_census_and_original_sha256(recomputed):
    index = json.loads((ARCHIVE / "archive-index.json").read_text())
    assert recomputed["source_count"] == 18_140
    assert recomputed["strata_count"] == 305
    assert recomputed["singleton_strata"] == 20
    assert recomputed["paired_strata"] == 285
    assert recomputed["chosen_graphs"] == 570
    assert recomputed["failure_cases"] == 2_850
    assert recomputed["source_digest"] == index["accepted_family_sha256"]
    assert recomputed["chosen_digest"] == index["selected_family_sha256"]
    assert len(set(independent.source_graphs())) == 18_140


def test_independent_finite_scores_work_and_offline_oracles(recomputed):
    assert recomputed["original_F2_graphs"] == 142
    assert recomputed["subset_function_table_entries"] == 25_040
    assert recomputed["offline_F1_sum"] == 16_052
    assert recomputed["offline_F2_sum"] == 3_386
    expected = {
        "ASC": [15_695, 2_877, 14_250, 0],
        "DEGREE": [15_825, 3_106, 14_250, 0],
        "GREEDY_F1": [16_046, 3_286, 28_450, 14_200],
        "GREEDY_F2": [16_046, 3_286, 28_450, 14_200],
        "LOOKAHEAD2_F1": [16_052, 3_386, 53_410, 14_200],
        "LOOKAHEAD2_F2": [16_052, 3_386, 53_410, 14_200],
    }
    assert recomputed["policies"] == expected


def test_independent_negative_neutral_and_positive_cases(recomputed):
    assert recomputed["case_differences"] == {
        "F1_0": 2844, "F1_1": 6,
        "F2_0": 2784, "F2_1": 39, "F2_2": 20, "F2_3": 7,
    }
    assert recomputed["F2_winning_cases_by_degree"] == {3: 25, 4: 18, 5: 23}
    assert 39 + 2 * 20 + 3 * 7 == 100
    assert 2784 + 39 + 20 + 7 == 2850


def test_original_full_byte_archive_still_matches_manifest():
    index = json.loads((ARCHIVE / "archive-index.json").read_text())
    raw = (ARCHIVE / "audit.json").read_bytes()
    assert sha256(raw).hexdigest() == index["original_audit_sha256"]
    original = json.loads(raw)
    assert original["protocol"] == index["protocol"] == "RP-U004-P01"
    assert len(original["cases"]) == 2850
    assert original["physical_data_rows"] == 0
    assert original["verdict"] == index["first_verdict"]


def test_independent_f1_f2_oracles_on_broken_second_route():
    present = {0, 1, 2, 6}
    two_paths = ((0, 1), (1, 6), (0, 2), (2, 6))
    assert independent.function_pair(two_paths, present) == (1, 1)
    assert independent.function_pair(two_paths[:-1], present) == (1, 0)
    assert independent.function_pair(((0, 1), (2, 6)), present) == (0, 0)


def test_oracle_mutation_is_not_silently_accepted(monkeypatch):
    with monkeypatch.context() as altered:
        altered.setattr(independent, "path_masks", lambda unused: iter(()))
        with pytest.raises(AssertionError, match="Independent F1 oracles differ"):
            independent.function_pair(
                ((0, 1), (1, 6), (0, 2), (2, 6)), {0, 1, 2, 6}
            )


def test_original_connectivity_invariant_under_all_internal_relabels():
    initial = independent.function_pair(WITNESS, set(range(7)))
    for perm in permutations((1, 2, 3, 4, 5)):
        mapping = {0: 0, 6: 6}
        mapping.update(zip((1, 2, 3, 4, 5), perm))
        edges = tuple(tuple(sorted((mapping[a], mapping[b]))) for a, b in WITNESS)
        assert independent.function_pair(edges, set(range(7))) == initial
