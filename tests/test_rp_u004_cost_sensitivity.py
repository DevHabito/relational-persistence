"""Retrospective cost-boundary regressions, not new blinded outcomes."""
from dataclasses import replace
from fractions import Fraction
import json

import pytest

from experiments.rp_u004_cost_sensitivity import (
    ARCHIVE_DIR,
    Contrast,
    read_original_contrasts,
)


@pytest.fixture(scope="module")
def original():
    return read_original_contrasts()


def test_original_f2_counts_and_exact_rational_boundary(original):
    f2 = original["F2"]
    assert f2 == Contrast(3286, 3386, 28450, 53410)
    assert f2.tick_delta() == 100
    assert f2.lookup_delta() == 24960
    assert f2.break_even_price() == Fraction(5, 1248)


def test_secondary_f1_counts_are_not_independent_confirmation(original):
    f1 = original["F1"]
    assert f1 == Contrast(16046, 16052, 28450, 53410)
    assert f1.tick_delta() == 6
    assert f1.lookup_delta() == 24960
    assert f1.break_even_price() == Fraction(1, 4160)


@pytest.mark.parametrize("metric", ["F1", "F2"])
def test_strict_advantage_tie_and_reversal_are_exact(original, metric):
    case = original[metric]
    price = case.break_even_price()
    step = Fraction(1, 1_000_000)
    assert case.net_difference(Fraction(0)) == case.tick_delta()
    assert case.net_difference(price - step) > 0
    assert case.net_difference(price) == 0
    assert case.net_difference(price + step) < 0
    assert case.net_difference(Fraction(1)) < 0


def test_missing_cost_difference_is_not_silently_divided_by_zero():
    instance = Contrast(1, 2, 7, 7)
    with pytest.raises(ValueError, match="No finite break-even"):
        instance.break_even_price()


def test_manifest_sha_corruption_fails_before_reading_results(tmp_path):
    index = json.loads((ARCHIVE_DIR / "archive-index.json").read_text(encoding="utf-8"))
    index["original_audit_sha256"] = "0" * 64
    copy = tmp_path / "archive-index.json"
    copy.write_text(json.dumps(index), encoding="utf-8")
    # Only the manifest changes; link to original data instead of copying 29 MB.
    (tmp_path / "audit.json").symlink_to((ARCHIVE_DIR / "audit.json").resolve())
    with pytest.raises(ValueError, match="archive SHA-256"):
        read_original_contrasts(tmp_path)


def test_negative_mutated_count_changes_threshold_and_is_not_original(original):
    changed = replace(original["F2"], lookahead_ticks=3385)
    assert changed.break_even_price() != Fraction(5, 1248)
    assert original["F2"] == Contrast(3286, 3386, 28450, 53410)
