"""Verify immutable original G09 first five-derivative source audit outcome."""
from hashlib import sha256
import json
from pathlib import Path

ORIGINAL=Path("docs/results/NEU-01-G09-P01-first-run/audit.json")
INDEX=Path("docs/results/NEU-01-G09-P01-first-run/archive-index.json")
SHA="bb3350806c1b86a886f2e79a47b52f967fc34176d598c60742b4b4d1be9dfdba"


def test_first_full_five_pair_audit_original_bytes_sha256():
    original=ORIGINAL.read_bytes()
    assert len(original)==15338
    assert sha256(original).hexdigest()==SHA
    assert original.endswith(b"\n")


def test_pre_source_g09_freeze_and_real_original_runner_provenance():
    i=json.loads(INDEX.read_text())
    assert i["protocol_only_commit"]=="090efb85c4869ded1b968c9af883662a7eb0902d"
    assert i["first_implementation_commit"]=="926a2665d9f9fffffe98fad752496572cdd9fc0f"
    assert i["first_real_source_workflow_run_id"]==43338356181
    assert i["pre_source_synthetic_adversarial_tests_passed"]==8
    assert i["first_original_audit_json"]["sha256"]==SHA
    assert i["original_artifact"]["id"]==13997394683
    assert i["full_regression_at_first_source_commit"]["python_311_passed"]==980
    assert i["full_regression_at_first_source_commit"]["python_312_passed"]==980
    assert i["conclusion_scope"]["new_direct_positions_checked"]==45750000
    assert i["conclusion_scope"]["six_pair_total_positions_checked"]==54900000


def test_every_one_of_five_fixed_source_derived_pairs_exact_at_ieee64():
    data=json.loads(ORIGINAL.read_text())
    assert data["study"]=="NEU-01-G09-P01"
    assert data["status"]=="FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE"
    assert data["number_exact_bitwise_identical_pairs"]==5
    assert data["number_numerically_different_pairs"]==0
    assert data["preexisting_G08_D03_one_pair_identity_known"] is True
    assert data["new_participants_or_independent_human_sample"] is False
    assert data["causal_processing_stage_identified"] is False
    assert data["physical_units_calibration_verified"] is False
    assert data["source_amplitude_values_uploaded"] is False
    pairs=data["first_original_five_pair_results"]
    assert len(pairs)==5
    assert [(p["participant"],p["task"]) for p in pairs]==[
        ("sub-02","eyesopen"),("sub-03","eyesclosed"),("sub-03","eyesopen"),
        ("sub-04","eyesclosed"),("sub-04","eyesopen")
    ]
    for p in pairs:
        assert p["status"]=="EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
        assert p["metadata_gate"]["metadata_gate_passed"] is True
        assert p["metadata_gate"]["matched_channel_labels_same_positions"]==61
        assert p["metadata_gate"]["time_grid_max_abs_error_ms"]==0
        assert p["bids_units"]["units_declared_in_bids_channels_tsv"]=="uV"
        assert p["derivative_source_identity"]["bytes"]==73824136
        assert p["derivative_source_identity"]["fully_authenticated_publisher_md5"] is True
        assert len(p["derivative_source_identity"]["actual_sha256"])==64
        assert p["root_eeg_signal_read"] is True
        c=p["direct_IEEE_comparison"]
        assert c["all_aligned_numeric_values_count"]==9150000
        assert c["numeric_equal_count"]==9150000
        assert c["numeric_differ_count"]==0
        assert c["ieee_64bit_pattern_equal_count"]==9150000
        assert c["ieee_64bit_pattern_differ_count"]==0
        assert c["canonical_64bit_content_digests_identical"] is True
        assert c["source_original_double_canonical_sha256"]==c["derivative_double_canonical_sha256"]
        assert c["fixed_500_frame_shift_exact_numeric_equal_count"]<9150000
        assert c["fixed_reversed_61_channel_exact_numeric_equal_count"]<9150000


def test_first_g09_source_original_sha_catches_mutations():
    b=ORIGINAL.read_bytes()
    changed=b.replace(b"FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE",b"UNVERIFIED_RESULT",1)
    assert b!=changed
    assert sha256(changed).hexdigest()!=SHA
