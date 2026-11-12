"""Finite exhaustive checks of an elementary post-result zero-run bound."""
from __future__ import annotations
from itertools import product
import json
import pytest
from experiments.neu01_g03_posthoc_nonzero_bounds import (
    REPORT, INDEX, audit, zero_zero_upper, nonzero_equal_lower,
)


def independent_counts(channels):
    z = sum(v == 0 for ch in channels for v in ch)
    e = sum(ch[i] == ch[i - 1] for ch in channels for i in range(1, len(ch)))
    e00 = sum(ch[i] == 0 and ch[i - 1] == 0
              for ch in channels for i in range(1, len(ch)))
    enn = sum(ch[i] != 0 and ch[i] == ch[i - 1]
              for ch in channels for i in range(1, len(ch)))
    return z, e, e00, enn


def verify_bound(channels):
    z, e, e00, enn = independent_counts(channels)
    assert e00 + enn == e
    assert e00 <= zero_zero_upper(z)
    assert nonzero_equal_lower(e, z) <= enn


def test_exhaustive_one_channel():
    for n in range(1, 7):
        for seq in product((-1, 0, 1), repeat=n):
            verify_bound((seq,))


def test_exhaustive_two_channels_and_channel_boundaries():
    for seq in product((-1, 0, 1), repeat=6):
        verify_bound((seq[:3], seq[3:]))


def test_signed_zeros_and_nonzero_plateaus():
    assert independent_counts(((-0.0, 0.0, 0.0),)) == (3, 2, 2, 0)
    assert independent_counts(((2, 2, 2),)) == (0, 2, 0, 2)


@pytest.mark.parametrize(("z", "e", "bound"), [
    (0, 3, 3), (2, 1, 0), (2, 2, 1),
    (5923, 130491, 124569), (11161, 152796, 141636),
    (15318, 175607, 160290),
])
def test_exact_bound_examples(z, e, bound):
    assert nonzero_equal_lower(e, z) == bound


@pytest.mark.parametrize("bad", [-1, True, 0.2, None, "4"])
def test_invalid_integer_counts_fail(bad):
    with pytest.raises(ValueError):
        zero_zero_upper(bad)
    with pytest.raises(ValueError):
        nonzero_equal_lower(bad, 1)


def test_original_archive_and_three_independent_subject_rows():
    a = audit(REPORT.read_bytes(), INDEX.read_bytes())
    assert a["closed_nonzero_equal_pairs_lower_total"] == 426495
    assert a["independent_original_eeg_recount"] is False
    assert a["neural_mechanism_inferred"] is False
    for subject, expected in {
        "sub-02": (124569, 9, 124560),
        "sub-03": (141636, 3, 141633),
        "sub-04": (160290, 12, 160278),
    }.items():
        r = a["by_subject"][subject]
        assert (
            r["closed_nonzero_equal_pairs_lower"],
            r["open_nonzero_equal_pairs_exact"],
            r["closed_minus_open_nonzero_equal_pairs_lower"]
        ) == expected


def test_tampered_original_report_rejected():
    original = REPORT.read_bytes()
    changed = original.replace(b"130491", b"130492", 1)
    assert changed != original
    with pytest.raises(ValueError, match="checksum mismatch"):
        audit(changed, INDEX.read_bytes())


def test_tampered_original_manifest_rejected():
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    data["original_hosted_run"]["run_id"] = 1
    with pytest.raises(ValueError, match="provenance mismatch"):
        audit(REPORT.read_bytes(), json.dumps(data).encode())
