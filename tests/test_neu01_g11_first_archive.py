"""Immutable first original NEU-01 G11 source result: fail closed on tampering."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path

from experiments import neu01_g11_source_runner as runner

AUDIT = Path("docs/results/NEU-01-G11-P01-first-run/audit.json")
DIGEST = "0a7bc6785053c4da697f8d287245a6fa93a25ce1a69f945e447f0b3829b51537"
SIZE = 33803


def _original() -> dict:
    original = AUDIT.read_bytes()
    assert len(original) == SIZE
    assert sha256(original).hexdigest() == DIGEST
    return json.loads(original)


def test_immutable_source_data_exact_digest_and_all_twenty_four_rows():
    original = _original()
    assert original["status"] == "G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT"
    assert original["protocol_commit"] == runner.PROTOCOL_COMMIT
    assert original["source_records_requested"] == 24
    assert original["source_records_eligible"] == 24
    assert original["all_requested_source_records_eligible"] is True
    assert len(original["first_original_record_results"]) == 24
    for expected, record in zip(
        runner.SOURCES, original["first_original_record_results"], strict=True
    ):
        assert (record["subject"], record["session"]) == (
            expected.subject, expected.session
        )
        assert record["status"] == "ELIGIBLE"
        assert record["waveform_read"] is True
        assert record["feature_extraction_complete"] is True
        assert record["source_authentication"]["eeg"][
            "publisher_pointer_md5_verified"
        ] is True
        assert record["source_authentication"]["vhdr"][
            "publisher_pointer_md5_verified"
        ] is True
        assert record["normalized_ordered_61_labels_sha256"] == (
            runner.CHANNEL_LABELS_SHA256
        )
    assert original["source_waveforms_published"] is False


def test_permutation_and_negative_incremental_outcome_not_inverted():
    o = _original()
    perm = o["primary_permutation"]
    assert perm["permutations"] == 20000
    assert perm["seed"] == 1101
    assert perm["extreme_count"] == 0
    assert perm["p_one_sided"] == 1 / 20001
    d = o["feature_diagnostics"]
    assert d["graph"]["unique_correct"] == 7
    assert d["power"]["unique_correct"] == 7
    assert d["shuffled_graph"]["unique_correct"] == 3
    assert d["graph"]["d"] > d["power"]["d"] > d["shuffled_graph"]["d"]
    assert o["spectral_only_increment_both_criteria"] is False
    assert o["aligned_beats_independent_epoch_shuffle"] is True


def test_full_source_similarity_census_has_fixed_shape_and_finite_entries():
    matrices = _original()["similarity_matrices"]
    assert set(matrices) == {"graph", "power", "shuffled_graph"}
    for family, matrix in matrices.items():
        assert len(matrix) == 12, family
        assert all(len(row) == 12 for row in matrix)
        assert all(math.isfinite(x) and -1 <= x <= 1
                   for row in matrix for x in row)


def test_first_source_index_original_digest_and_chronology_frozen():
    index = json.loads(Path(
        "docs/results/NEU-01-G11-P01-first-run/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert index["original_archive_sha256"] == DIGEST
    assert index["original_archive_length_bytes"] == SIZE
    assert index["first_source_status"] == "G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT"
    assert index["all_frozen_records_eligible"] == 24
    assert index["source_implementation_py311_regression_passed"] == 1023
    assert index["source_implementation_py312_regression_passed"] == 1023
