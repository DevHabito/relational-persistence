"""Retrospective integrity guards for the original G04 source replay artifact.

These do NOT re-download original EEG or turn old data into a new sample.
"""
from hashlib import sha256
import json
from pathlib import Path

RESULT = Path("docs/results/NEU-01-G04-P01-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G04-P01-first-run/archive-index.json")
EXPECTED_SHA256 = "7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00"
SUBJECTS = ("sub-02", "sub-03", "sub-04")


def test_first_success_original_bytes_immutable():
    b = RESULT.read_bytes()
    assert len(b) == 6022
    assert sha256(b).hexdigest() == EXPECTED_SHA256
    assert b.endswith(b"\n")


def test_original_provenance_and_failure_chronology_kept():
    index = json.loads(INDEX.read_text())
    assert index["first_full_success"]["run_id"] == 43327626650
    assert index["first_full_success"]["synthetic_tests_passed_before_source"] == 12
    assert index["first_full_success"]["original_aggregate_json"]["sha256"] == EXPECTED_SHA256
    assert index["first_preflight_instrument_failure"]["run_id"] == 43327245478
    assert index["first_source_eligibility_failure"]["run_id"] == 43327371558
    assert index["first_source_eligibility_failure"]["partial_source_was_accessed"] is True


def test_all_six_exact_original_consistency_claims_and_bounds():
    d = json.loads(RESULT.read_text())
    assert d["status"] == "INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH"
    assert d["original_values_recounted"] == 54900000
    assert d["retrospective_same_processed_sources"] is True
    assert d["no_neural_or_thermodynamic_inference"] is True
    assert d["participants"] == list(SUBJECTS)
    assert set(d["recordings"]) == set(SUBJECTS)
    seen = 0
    closed_equal = closed_e00 = closed_enn = closed_runs = open_enn = 0
    for subject in SUBJECTS:
        for state in ("eyesclosed", "eyesopen"):
            record = d["recordings"][subject][state]
            c = record["census"]
            assert c["total_native_values"] == 9150000
            assert c["within_channel_possible_adjacencies"] == 9149939
            assert c["within_channel_equal_adjacent"] == c["zero_zero_equal_adjacent"] + c["nonzero_equal_adjacent"]
            assert c["exact_zero_values"] == c["zero_zero_equal_adjacent"] + c["zero_runs"]
            assert c["nonzero_equal_adjacent"] >= c["prior_d01_lower_bound_nonzero"]
            assert record["unit_metadata"]["physical_unit_missing"] == 61
            assert len(record["eeg_sha256"]) == 64
            seen += 1
            if state == "eyesclosed":
                closed_equal += c["within_channel_equal_adjacent"]
                closed_e00 += c["zero_zero_equal_adjacent"]
                closed_enn += c["nonzero_equal_adjacent"]
                closed_runs += c["zero_runs"]
            else:
                assert c["exact_zero_values"] == 0
                open_enn += c["nonzero_equal_adjacent"]
    assert seen == 6
    assert (closed_equal, closed_e00, closed_enn, closed_runs, open_enn) == (
        458894, 1258, 457636, 31144, 24
    )


def test_mutating_original_archive_would_break_digest():
    b = RESULT.read_bytes()
    altered = b.replace(b"130304", b"130305", 1)
    assert altered != b
    assert sha256(altered).hexdigest() != EXPECTED_SHA256
