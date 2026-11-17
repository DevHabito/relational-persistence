"""Protect the original G12 source evidence from silent changes or positive relabeling."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path

from experiments import neu01_g12_rank_core as core
from experiments import neu01_g12_source_runner as source

ARCHIVE = Path("docs/results/NEU-01-G12-P01-first-run/audit.json")
ORIGINAL_SHA = "9dfc38092c3440dc7e67e2a99caba97c32ff18493cdd20f3ea11861c50bad62a"
ORIGINAL_BYTES = 53239


def original() -> dict:
    body = ARCHIVE.read_bytes()
    assert len(body) == ORIGINAL_BYTES
    assert sha256(body).hexdigest() == ORIGINAL_SHA
    return json.loads(body)


def test_evidence_byte_identity_and_full_24_source_census():
    j = original()
    assert j["study"] == "NEU-01-G12-P01"
    assert j["status"] == "G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT"
    assert j["protocol_commit"] == source.PROTOCOL_COMMIT
    assert j["source_records_requested"] == j["source_records_eligible"] == 24
    assert j["all_registered_sources_eligible"] is True
    assert len(j["first_original_source_rows"]) == len(source.SOURCES) == 24
    for record, manifest in zip(
        j["first_original_source_rows"], source.SOURCES, strict=True
    ):
        assert (record["subject"], record["session"]) == (
            manifest.subject, manifest.session
        )
        assert record["status"] == "ELIGIBLE"
        assert record["source_signal_decoded"] is True
        assert record["features_computed"] is True
        assert record["body_identity"]["root"]["publisher_MD5_body_verified"] is True
        assert record["body_identity"]["header"]["publisher_MD5_body_verified"] is True
        assert record["ordered_labels_sha256"] == source.EXPECTED_LABELS_SHA
    assert j["original_waveforms_published"] is False
    assert j["cross_dataset_external_replication"] is False


def test_archived_primary_result_cannot_be_silently_reclassified_as_positive():
    j = original()
    counts = j["model_correct_counts"]
    assert counts == {
        "power_only": 4,
        "graph_only": 7,
        "shuffled_graph_only": 2,
        "fixed_equal_fusion": 6,
        "fixed_shuffle_fusion": 4,
    }
    paired = j["paired_exact_test"]
    assert paired["improved_count"] == 2
    assert paired["harmed_count"] == 0
    assert paired["net_gain"] == 2
    assert paired["discordant"] == 2
    assert paired["one_sided_exact_discordance_p"] == 0.25
    assert paired["independent_rows_assumption_not_established"] is True
    secondary = j["joint_label_permutation_diagnostic"]
    assert secondary["seed"] == 1202
    assert secondary["permutations"] == 20_000
    assert secondary["extreme_count"] == 576
    assert secondary["one_sided_joint_label_reference_p"] == 577 / 20001
    assert secondary["not_a_power_conditional_null"] is True
    assert counts["fixed_equal_fusion"] > counts["fixed_shuffle_fusion"]
    assert paired["one_sided_exact_discordance_p"] > 0.05


def test_all_source_matrices_and_top_rank_flags_have_no_missing_rows():
    j = original()
    matrix_names = {"graph", "power", "shuffled_graph"}
    assert set(j["similarity_matrices"]) == matrix_names
    assert set(j["unit_rank_matrices"]) == matrix_names | {
        "fixed_equal_fusion", "fixed_shuffle_fusion",
    }
    for family, matrix in j["similarity_matrices"].items():
        assert len(matrix) == core.N
        assert all(len(row) == core.N for row in matrix)
        assert all(math.isfinite(float(x)) and -1 <= x <= 1
                   for row in matrix for x in row), family
    for name, matrix in j["unit_rank_matrices"].items():
        assert len(matrix) == core.N
        assert all(len(row) == core.N for row in matrix)
        assert all(math.isfinite(float(x)) and 0 <= x <= 1
                   for row in matrix for x in row), name
    for name, flag in j["model_correct_flags"].items():
        assert len(flag) == core.N
        assert all(type(x) is bool for x in flag), name
        assert sum(flag) == j["model_correct_counts"][name]


def test_original_archive_index_matches_first_real_workflow():
    idx = json.loads(Path(
        "docs/results/NEU-01-G12-P01-first-run/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert idx["original_json_sha256"] == ORIGINAL_SHA
    assert idx["original_json_length_bytes"] == ORIGINAL_BYTES
    assert idx["first_original_result"] == (
        "G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT"
    )
    assert idx["source_records_eligible"] == 24
    assert idx["primary_exact_one_sided_p"] == 0.25
    assert idx["source_implementation_py311_tests_passed"] == 1042
    assert idx["source_implementation_py312_tests_passed"] == 1042
