"""Synthetic/adversarial G05 tests. No human EEG source is needed."""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import struct

import pytest

from experiments import neu01_g05_numeric_runs as g05


def encode(channels):
    n = len(channels[0])
    assert all(len(x) == n for x in channels)
    return b"".join(
        struct.pack("<" + "f" * len(channels),
                    *(channels[column][frame] for column in range(len(channels))))
        for frame in range(n)
    )


def slow_oracle(channels):
    """A separate direct loop, not the NumPy run detector."""
    zero_hist, nonzero_hist = Counter(), Counter()
    nonzero_values = integers = integer_pairs = e00 = enn = zeros = zero_runs = 0
    per_channel = []
    for x in channels:
        zeros += sum(v == 0.0 for v in x)
        nonzero_values += sum(v != 0.0 for v in x)
        integers += sum(v != 0.0 and float(v).is_integer() for v in x)
        pairs = 0
        start = 0
        while start < len(x):
            end = start + 1
            while end < len(x) and x[end] == x[start]:
                end += 1
            value = x[start]
            length = end - start
            if value == 0.0:
                zero_runs += 1
            if length >= 2:
                pairs += length - 1
                if value == 0.0:
                    e00 += length - 1
                    zero_hist[length] += 1
                else:
                    enn += length - 1
                    nonzero_hist[length] += 1
                    if float(value).is_integer():
                        integer_pairs += length - 1
            start = end
        per_channel.append(pairs)
    return {
        "Z": zeros, "R0": zero_runs, "E00": e00, "Enn": enn,
        "N": nonzero_values, "Nint": integers, "Eint": integer_pairs,
        "h0": {str(k): v for k, v in sorted(zero_hist.items())},
        "hn": {str(k): v for k, v in sorted(nonzero_hist.items())},
        "pairs": per_channel,
    }


def check_case(channels):
    r = g05.count_native(encode(channels), channels=len(channels), frames=len(channels[0]))
    c, d = r["census"], r["diagnostic"]
    old = slow_oracle(channels)
    assert (c["exact_zero_values"], c["zero_runs"], c["zero_zero_equal_adjacent"],
            c["nonzero_equal_adjacent"]) == (old["Z"], old["R0"], old["E00"], old["Enn"])
    assert (d["native_nonzero_samples"], d["native_integer_nonzero_samples"],
            d["native_integer_nonzero_equal_pairs"]) == (old["N"], old["Nint"], old["Eint"])
    assert d["zero_repeat_run_histogram_all_lengths"] == old["h0"]
    assert d["nonzero_repeat_run_histogram_all_lengths"] == old["hn"]
    assert c["within_channel_equal_adjacent"] == sum(old["pairs"])
    assert c["median_per_channel_equal_adjacent_count"] == sorted(old["pairs"])[len(channels)//2]
    assert c["max_per_channel_equal_adjacent_count"] == max(old["pairs"])
    assert d["max_zero_repeat_run_length"] == max((int(k) for k in old["h0"]), default=0)
    assert d["max_nonzero_repeat_run_length"] == max((int(k) for k in old["hn"]), default=0)


def test_exhaustive_two_channel_three_frame_cases():
    for row in product((-1.0, 0.0, 0.5), repeat=6):
        check_case((row[:3], row[3:]))


def test_signed_zeros_fractional_and_negative_integer_runs():
    check_case(((0.0, -0.0, 0.0, 3.0, 3.0, 3.0),
                (-1.25, -1.25, 0.5, 0.5, 0.5, 0.5),
                (-2.0, -2.0, -2.0, -2.0, -2.0, -2.0)))


def test_zero_plateaus_long_and_discontinuous_runs():
    check_case(((0.0,) * 11, (5.0,) * 11))
    check_case(((0.0, 1.0, 0.0, 0.0, 2.0, 2.0, 0.0),))
    check_case(((0.0, 1.0, 0.0, 1.0), (1.0, 0.0, 1.0, 0.0)))


def test_nonfinite_and_malformed_length_fail_closed():
    with pytest.raises(g05.SourceNotEligible, match="SIZE_OR_TYPE_INVALID"):
        g05.count_native(b"bad", frames=3, channels=1)
    with pytest.raises(g05.SourceNotEligible, match="NONFINITE"):
        g05.count_native(encode(((0.0, float("nan"), 1.0),)), frames=3, channels=1)


def test_original_g04_hash_and_scope_are_frozen_before_source():
    assert len(g05.ORIGINAL_G04.read_bytes()) == g05.ORIGINAL_G04_BYTES
    assert sha256(g05.ORIGINAL_G04.read_bytes()).hexdigest() == g05.ORIGINAL_G04_SHA
    assert g05.original_g04()["status"] == "INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH"
    assert len(g05.SUBJECTS) == 3 and len(g05.TASKS) == 2


def test_changed_g04_oracle_is_rejected(monkeypatch, tmp_path):
    original = g05.ORIGINAL_G04.read_bytes()
    changed = original.replace(b"130304", b"130305", 1)
    assert changed != original
    path = tmp_path / "audit.json"
    path.write_bytes(changed)
    monkeypatch.setattr(g05, "ORIGINAL_G04", path)
    with pytest.raises(g05.SourceNotEligible, match="DIGEST_FAILURE"):
        g05.original_g04()


def test_known_g04_comparison_accepts_true_archive_and_rejects_tampering():
    original = g05.original_g04()
    fresh = {}
    for subject in g05.SUBJECTS:
        fresh[subject] = {}
        for task in g05.TASKS:
            item = original["recordings"][subject][task]
            fresh[subject][task] = {
                "eeg_sha256": item["eeg_sha256"],
                "units_missing": item["unit_metadata"]["physical_unit_missing"],
                "census": dict(item["census"]),
            }
    g05.compare_to_g04(fresh, original)
    fresh["sub-03"]["eyesclosed"]["census"]["zero_zero_equal_adjacent"] += 1
    with pytest.raises(g05.RecountMismatch, match="sub-03/eyesclosed/zero_zero_equal_adjacent"):
        g05.compare_to_g04(fresh, original)
