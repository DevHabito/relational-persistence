"""Retrospective archive integrity tests for original G03 first-source result.

These tests do NOT rerun the original 54.9 million EEG values and cannot
constitute an independent source-level reproduction. They keep the historical
aggregate evidence byte-identical, with all six original records present.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

EXPECTED = "b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c"
REPORT = Path("docs/results/NEU-01-G03-first-run/audit.json")
INDEX = Path("docs/results/NEU-01-G03-first-run/archive-index.json")
COHORT = ("sub-02", "sub-03", "sub-04")


def test_first_aggregate_original_byte_identity():
    body = REPORT.read_bytes()
    assert len(body) == 10117
    assert sha256(body).hexdigest() == EXPECTED
    assert body.endswith(b"\n")


def test_archive_index_is_tied_to_original_hosted_job_and_digest():
    info = json.loads(INDEX.read_text(encoding="utf-8"))
    assert info["original_aggregate_json"]["sha256"] == EXPECTED
    assert info["original_hosted_run"]["run_id"] == 42657980659
    assert info["original_hosted_run"]["job_id"] == 129301529684
    assert info["original_hosted_run"]["synthetic_tests_passed_first"] == 19
    assert info["protocol_committed_before_new_original_amplitude"] == (
        "ed0d77e5a3812ec1931ec6b7e3dbdcc0e87777b3"
    )
    assert info["original_implementation_and_workflow_sha"] == (
        "f8ab6bd59e4b1cbe26e6322a4f83a4c08212df04"
    )


def test_full_original_numeric_denominators_and_all_negative_cases_visible():
    r = json.loads(REPORT.read_text(encoding="utf-8"))
    assert r["decision"] == "DESCRIPTIVE_DIRECTION_REPLICATED_IN_ALL_THREE"
    assert r["participants"] == list(COHORT)
    assert r["condition_order"] == ["eyesclosed", "eyesopen"]
    assert r["source_objects_authenticated"] == 12
    assert r["tsv_blobs_authenticated"] == 6
    assert r["observed_original_values"] == 54900000
    assert r["observed_original_adjacencies"] == 54899634
    assert r["original_signals_published"] is False
    assert r["lzc_computed"] is False
    assert r["clinical_or_thermodynamic_conclusion"] is False
    signs = {"positive": 0, "zero": 0, "negative": 0}
    zero_signs = dict(signs)
    for subject in COHORT:
        condition = r["recordings"][subject]
        all_counts = {}
        for task in ("eyesclosed", "eyesopen"):
            d = condition[task]
            counts = d["native_census"]
            assert counts["total_native_values"] == 9150000
            assert counts["finite"] == 9150000
            assert counts["nan"] == counts["pos_inf"] == counts["neg_inf"] == 0
            assert counts["within_channel_possible_adjacencies"] == 9149939
            assert 0 <= counts["exact_zero_values"] <= 9150000
            assert 0 <= counts["within_channel_equal_adjacent"] <= 9149939
            assert d["source_unit_declarations"]["header_unit_counts"] == {"MISSING": 61}
            assert d["source_unit_declarations"]["header_calibration_complete"] is False
            assert d["source_identity"]["vhdr"]["annex_md5_verified"] is True
            assert d["source_identity"]["eeg"]["annex_md5_verified"] is True
            assert d["source_identity"]["channels_tsv_git_blob_verified"] is True
            assert len(d["source_identity"]["eeg"]["sha256"]) == 64
            all_counts[task] = counts
        difference = (all_counts["eyesclosed"]["within_channel_equal_adjacent"]
                      - all_counts["eyesopen"]["within_channel_equal_adjacent"])
        zero_difference = (all_counts["eyesclosed"]["exact_zero_values"]
                           - all_counts["eyesopen"]["exact_zero_values"])
        archived = r["pair_differences"][subject]
        assert archived["paired_equal_difference_numerator"] == difference
        assert archived["paired_equal_common_denominator"] == 9149939
        assert archived["paired_zero_difference_numerator"] == zero_difference
        assert archived["paired_zero_common_denominator"] == 9150000
        signs["positive" if difference > 0 else "negative" if difference < 0 else "zero"] += 1
        zero_signs["positive" if zero_difference > 0 else "negative" if zero_difference < 0 else "zero"] += 1
    assert signs == r["primary_direction_signs"]
    assert zero_signs == r["secondary_zero_direction_signs"]


def test_mutated_archive_cannot_pass_pinned_sha():
    data = REPORT.read_bytes()
    altered = data.replace(b"130491", b"130492", 1)
    assert altered != data
    assert sha256(altered).hexdigest() != EXPECTED
