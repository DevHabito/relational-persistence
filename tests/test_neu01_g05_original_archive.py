"""Immutability and conservation checks for first original G05 source aggregate.

These tests re-evaluate source-derived *reported aggregate counts* only.
They do not re-read EEG, prove a processing mechanism, or validate physiology.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path

FIRST = Path("docs/results/NEU-01-G05-P01-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G05-P01-first-run/archive-index.json")
SHA = "9dbf40942373aa5ec3fa9f7959b4442b9da96003c01090f76d5a4507639a21d4"
SUBS = ("sub-02", "sub-03", "sub-04")


def test_original_g05_aggregate_sha256_and_length():
    raw = FIRST.read_bytes()
    assert len(raw) == 8559
    assert sha256(raw).hexdigest() == SHA
    assert raw.endswith(b"\n")


def test_provenance_preserves_frozen_protocol_and_original_run():
    idx = json.loads(INDEX.read_text())
    assert idx["protocol_only_commit"] == "1702cbb602d35efe8a4bc3cdc484f2ad2e5f9f7a"
    assert idx["original_source_workflow_run_id"] == 43329558431
    assert idx["synthetic_tests_before_source"] == 7
    assert idx["original_aggregate_json"]["sha256"] == SHA
    assert idx["original_aggregate_json"]["bytes"] == 8559
    assert idx["github_original_artifact"]["id"] == 13993594220


def test_frozen_source_run_histograms_and_integer_reconciliation():
    d = json.loads(FIRST.read_text())
    assert d["status"] == "G05_EXACT_SOURCE_CENSUS_COMPLETE"
    assert d["total_native_float32_values"] == 54900000
    assert d["same_previously_seen_processed_source"] is True
    assert d["neural_causal_interpretation"] is False
    assert d["physical_calibration_validated"] is False
    assert d["participants"] == list(SUBS)
    assert set(d["source_derived_records"]) == set(SUBS)
    c_e = c_e0 = c_enn = c_int = c_nonzero = c_intpair = o_int = o_intpair = 0
    closed_hist = {}
    open_hist = {}
    for subject in SUBS:
        states = d["source_derived_records"][subject]
        assert set(states) == {"eyesclosed", "eyesopen"}
        for state, record in states.items():
            c = record["census"]
            info = record["diagnostic"]
            assert len(record["eeg_sha256"]) == 64
            assert record["units_missing"] == 61
            assert c["total_native_values"] == 9150000
            assert c["within_channel_possible_adjacencies"] == 9149939
            assert c["within_channel_equal_adjacent"] == (
                c["zero_zero_equal_adjacent"] + c["nonzero_equal_adjacent"]
            )
            assert c["exact_zero_values"] == c["zero_runs"] + c["zero_zero_equal_adjacent"]
            assert info["native_nonzero_samples"] + c["exact_zero_values"] == 9150000
            assert 0 <= info["native_integer_nonzero_samples"] <= info["native_nonzero_samples"]
            assert 0 <= info["native_integer_nonzero_equal_pairs"] <= c["nonzero_equal_adjacent"]
            assert (info["native_integer_nonzero_equal_pairs"]
                    + info["native_noninteger_nonzero_equal_pairs"]
                    == c["nonzero_equal_adjacent"])
            h0 = {int(k): v for k, v in info["zero_repeat_run_histogram_all_lengths"].items()}
            hn = {int(k): v for k, v in info["nonzero_repeat_run_histogram_all_lengths"].items()}
            assert all(k >= 2 and type(v) is int and v > 0 for k, v in h0.items())
            assert all(k >= 2 and type(v) is int and v > 0 for k, v in hn.items())
            assert sum((k-1)*v for k,v in h0.items()) == c["zero_zero_equal_adjacent"]
            assert sum((k-1)*v for k,v in hn.items()) == c["nonzero_equal_adjacent"]
            assert info["max_zero_repeat_run_length"] == max(h0, default=0)
            assert info["max_nonzero_repeat_run_length"] == max(hn, default=0)
            counts = closed_hist if state == "eyesclosed" else open_hist
            for k, v in hn.items():
                counts[k] = counts.get(k, 0) + v
            if state == "eyesclosed":
                c_e += c["within_channel_equal_adjacent"]
                c_e0 += c["zero_zero_equal_adjacent"]
                c_enn += c["nonzero_equal_adjacent"]
                c_int += info["native_integer_nonzero_samples"]
                c_nonzero += info["native_nonzero_samples"]
                c_intpair += info["native_integer_nonzero_equal_pairs"]
            else:
                o_int += info["native_integer_nonzero_samples"]
                o_intpair += info["native_integer_nonzero_equal_pairs"]
    assert (c_e, c_e0, c_enn, c_int, c_nonzero, c_intpair, o_int, o_intpair) == (
        458894, 1258, 457636, 2728984, 27417598, 45291, 145, 0
    )
    assert closed_hist == {2:436533, 3:10095, 4:287, 5:13}
    assert open_hist == {2:24}


def test_archive_alteration_changes_digest():
    b = FIRST.read_bytes()
    changed = b.replace(b"912943", b"912944", 1)
    assert changed != b
    assert sha256(changed).hexdigest() != SHA
