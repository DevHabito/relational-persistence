"""First original G08 fixed-grid results and immutable SHA256 regression."""
from hashlib import sha256
import json
from pathlib import Path

AUDIT=Path("docs/results/NEU-01-G08-P01-first-run/audit.json")
INDEX=Path("docs/results/NEU-01-G08-P01-first-run/archive-index.json")
FROZEN="18950086a3e0220dfc83c82210a5a84da9ad28d00e224fcdc7ac969aa842025b"


def test_original_source_json_frozen_bytewise():
    original=AUDIT.read_bytes()
    assert len(original)==2880
    assert sha256(original).hexdigest()==FROZEN
    assert original.endswith(b"\n")


def test_protocol_before_source_and_exact_runner_refs():
    i=json.loads(INDEX.read_text())
    assert i["protocol_only_commit"]=="efdeb6651f3614735d50629cdaabcf7e29c22de2"
    assert i["first_source_implementation_commit"]=="d1b34b32ed9083c406053fc7636e1e435d92cd77"
    assert i["first_original_source_workflow_run_id"]==43335456284
    assert i["synthetic_adversarial_tests_before_source"]==11
    assert i["full_regression_at_source_commit"]["python_311_passed"]==947
    assert i["full_regression_at_source_commit"]["python_312_passed"]==947
    assert i["original_artifact"]["id"]==13996733831
    assert i["original_audit"]["sha256"]==FROZEN


def test_original_g08_grids_correlations_and_nonclaims():
    d=json.loads(AUDIT.read_text())
    m=d["metadata_eligibility"]
    c=d["conditional_waveform_diagnostic"]
    assert d["status"]=="FIXED_GRID_DESCRIPTIVE_COMPARISON_COMPLETE"
    assert m["metadata_gate_passed"] is True
    assert m["metadata_rejection_reasons"]==[]
    assert m["channel_order_identical"] is True
    assert m["matched_channel_labels_same_positions"]==61
    assert m["original_ordered_labels_sha256"]==m["derivative_ordered_labels_sha256"]
    assert m["original_ordered_labels_sha256"]==m["bids_ordered_labels_sha256"]
    assert m["time_grid_max_abs_error_ms"]==0
    assert (m["first_relative_time_ms"],m["last_relative_time_ms"])==(0,299998)
    assert m["absolute_acquisition_onset_aligned"] is False
    assert d["bids_declared_unit_metadata"]["units_declared_in_bids_channels_tsv"]=="uV"
    assert d["bids_declared_unit_metadata"]["physical_scale_independently_calibrated"] is False
    assert c["fixed_zero_lag_projected"]["channels"]==61
    assert c["fixed_zero_lag_projected"]["median_signed_pearson"]==1
    assert c["fixed_zero_lag_projected"]["min_signed_pearson"]==1
    assert c["fixed_zero_lag_projected"]["count_abs_pearson_gt_0_9"]==61
    assert c["prespecified_one_second_circular_shift_control"]["median_signed_pearson"] < 0.5
    assert c["prespecified_one_second_circular_shift_control"]["count_abs_pearson_gt_0_9"]==1
    assert d["original_root_eeg_body_downloaded"] is True
    assert d["sample_level_exact_alignment_proven"] is False
    assert d["processing_stage_causally_identified"] is False
    assert d["neurophysiological_or_clinical_conclusion"] is False
    assert d["original_binary_archived"] is False


def test_mutation_detected_by_first_source_sha256():
    b=AUDIT.read_bytes()
    corrupted=b.replace(b"FIXED_GRID_DESCRIPTIVE_COMPARISON_COMPLETE",b"UNSUPPORTED_COMPLETION_CLAIM",1)
    assert corrupted!=b
    assert sha256(corrupted).hexdigest()!=FROZEN
