"""Immutable first G10 eight-source aggregate archive integrity and scope."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from experiments import neu01_g10_pre_source as g


ORIGINAL_SHA = "5d7c239260da9d9d65cda652c617fdfe906affdff88f85be1a829877f49568c5"
ORIGINAL_BYTES = 36006
ARCHIVE = Path("docs/results/NEU-01-G10-P01-first-run/audit.json")


def test_first_source_bytes_and_original_sha256_unchanged():
    body = ARCHIVE.read_bytes()
    assert len(body) == ORIGINAL_BYTES
    assert sha256(body).hexdigest() == ORIGINAL_SHA


def test_eight_source_rows_match_frozen_manifest_and_ieee_census():
    data = json.loads(ARCHIVE.read_bytes())
    assert data["study"] == "NEU-01-G10-P01"
    assert data["status"] == "G10_EIGHT_PAIR_CENSUS_COMPLETE"
    assert data["protocol_commit"] == g.PROTOCOL_COMMIT
    assert data["count_directly_identical"] == 8
    assert data["count_directly_different"] == 0
    assert data["all_eight_purposively_preselected_pairs_included"] is True
    assert len(data["first_original_source_rows"]) == len(g.PAIRS)
    for pair, row in zip(g.PAIRS, data["first_original_source_rows"], strict=True):
        assert (row["subject"], row["session"], row["task"]) == (
            pair.subject, pair.session, pair.task
        )
        assert row["status"] == "DIRECT_ARRAYS_IDENTICAL"
        assert row["root_eeg_signal_read"] is True
        assert row["derivative_waveform_read"] is True
        assert row["source_identities"]["root"]["publisher_pointer_md5_verified"] is True
        assert row["source_identities"]["derivative"]["publisher_pointer_md5_verified"] is True
        assert row["metadata_gate"]["metadata_gate_passed"] is True
        match = row["direct_IEEE_comparison"]
        assert match["all_aligned_numeric_values_count"] == g.DIRECT_POSITIONS
        assert match["numeric_equal_count"] == g.DIRECT_POSITIONS
        assert match["ieee_64bit_pattern_equal_count"] == g.DIRECT_POSITIONS
        assert match["numeric_differ_count"] == 0
        assert match["ieee_64bit_pattern_differ_count"] == 0
        assert match["numeric_equal_but_ieee_bits_differ_count"] == 0
        assert match["canonical_64bit_content_digests_identical"] is True
        assert match["source_original_double_canonical_sha256"] == (
            match["derivative_double_canonical_sha256"]
        )


def test_pinned_sidecar_classification_disagreement_preserved_not_erased():
    data = json.loads(ARCHIVE.read_bytes())
    conflicting = [
        (x["subject"], x["session"], x["task"])
        for x in data["first_original_source_rows"]
        if x["bids_sidecar_channel_metadata"][
            "source_sidecar_classification_disagrees_with_tsv"
        ]
    ]
    assert conflicting == [
        ("sub-37", 2, "eyesclosed"), ("sub-37", 2, "eyesopen")
    ]
    assert data["source_author_processing_history_identified"] is False
    assert data["physical_units_independently_calibrated"] is False
    assert data["source_amplitudes_published"] is False


def test_archive_index_matches_original_workflow_and_sha():
    index = json.loads(Path(
        "docs/results/NEU-01-G10-P01-first-run/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert index["first_original_audit_sha256"] == ORIGINAL_SHA
    assert index["first_original_audit_bytes"] == ORIGINAL_BYTES
    assert index["first_original_source_status"] == "G10_EIGHT_PAIR_CENSUS_COMPLETE"
    assert index["fixed_pairs"] == 8
    assert index["new_aligned_sample_positions"] == 73200000
    assert index["direct_bitwise_equal_pairs"] == 8
    assert index["full_source_commit_python_311_pytest"] == 1002
    assert index["full_source_commit_python_312_pytest"] == 1002
