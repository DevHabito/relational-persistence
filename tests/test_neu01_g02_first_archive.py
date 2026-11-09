"""Verify first unsuccessful header gate and first successful amplitude-QC originals.

No participant EEG values included in this archive/check.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile

import pytest

from experiments import neu01_g02_original_signal_qc as qc

FAILED=Path("docs/results/NEU-01-G02-first-attempt/audit.json")
ROOT=Path("docs/results/NEU-01-G02-R02-first-signal")
FIRST=ROOT/"audit.json"
INDEX=ROOT/"archive-index.json"
EXPECTED_FAILED_SHA="1b14fb32bce882c737350260a70dcfade14086e0cc29ec3dd042dd19d8ece59d"
EXPECTED_SUCCESS_SHA="2b72a36e7692533130c890a28294ab8b8b5bc739b566697c9fa946bf26528ff2"


def original(failure=FAILED,success=FIRST,index=INDEX):
    first_failed=failure.read_bytes()
    first_success=success.read_bytes()
    provenance=json.loads(index.read_text(encoding="utf-8"))
    if sha256(first_failed).hexdigest()!=EXPECTED_FAILED_SHA:
        raise ValueError("original first G02 failure was altered")
    if sha256(first_success).hexdigest()!=EXPECTED_SUCCESS_SHA:
        raise ValueError("original first G02-R02 sample QC was altered")
    if provenance["first_failed_run"]["original_failed_report_sha256"]!=EXPECTED_FAILED_SHA:
        raise ValueError("failed source metadata index altered")
    if provenance["first_successful_amplitude_run"]["sha256"]!=EXPECTED_SUCCESS_SHA:
        raise ValueError("successful source metadata index altered")
    return json.loads(first_failed),json.loads(first_success),provenance


def test_first_attempt_failed_before_any_amplitude_then_separate_protocol_preceded_success():
    failure,success,index=original()
    assert failure["decision"]=="INSTRUMENT_FAILURE"
    assert failure["error_code"]=="CHANNEL_SCALING_OR_UNIT_UNSPECIFIED"
    assert "tasks" not in failure
    assert index["first_failed_run"]["run_id"]==42637541779
    assert index["first_failed_run"]["original_amplitude_samples_examined"]==0
    assert index["pre_amplitude_revised_protocol_commit"]==qc.REVISION_SHA
    assert qc.PROTOCOL_SHA==index["first_protocol_only_commit"]
    assert success["pre_original_signal_content_addendum_commit"]==qc.REVISION_SHA
    assert success["original_failed_first_attempt"]==42637541779
    assert index["first_successful_amplitude_run"]["run_id"]==42638326092
    assert success["decision"]=="SOURCE_NATIVE_NUMERIC_QC_CENSUS_COMPLETE_CALIBRATION_UNVERIFIED"


def test_complete_two_recording_native_numeric_integrity_and_full_epoch_census():
    _,report,_=original()
    assert report["all_source_objects_authenticated"] is True
    assert report["total_original_float32_values_examined"]==18300000
    assert report["total_ten_second_channel_epochs_examined"]==3660
    assert report["lzc_computed"] is False
    assert report["original_signal_values_published"] is False
    assert report["subjective_self_or_clinical_claim"] is False
    assert report["aggregate_source_qc_review_flags_present"] is False
    assert report["unit_calibration_status"]=="NOT_ESTABLISHED"
    assert report["calibrated_physical_amplitude_ready"] is False
    assert set(report["tasks"])=={"eyesclosed","eyesopen"}
    for task in report["tasks"].values():
        h=task["source_header_details"]
        q=task["sample_integrity"]
        assert h["header_resolution_counts"]=={"1":61}
        assert h["header_unit_counts"]=={"MISSING":61}
        assert h["header_channels_missing_declared_resolution"]==0
        assert h["header_channels_missing_declared_unit"]==61
        assert h["header_calibration_complete"] is False
        assert q["total_original_float32_values"]==9150000
        assert q["finite_sample_count"]==9150000
        assert q["total_ten_second_channel_epochs"]==1830
        assert q["finite_ten_second_channel_epochs"]==1830
        assert q["nan_sample_count"]==q["positive_infinity_sample_count"]==q["negative_infinity_sample_count"]==0
        assert q["channels_with_nonfinite_values"]==0
        assert q["channels_exactly_constant_full_record"]==0
        assert q["ten_second_channel_epochs_exactly_constant"]==0
        assert q["ten_second_channel_epochs_with_relative_ptp_extreme"]==0
        assert q["external_artifact_free_status"]=="NOT_ESTABLISHED"
        assert q["physical_adc_clipping_status"]=="NOT_IDENTIFIABLE_WITHOUT_CALIBRATION"
        assert q["lzc_result_computed"] is False
        assert len(task["verified_file_identity"])==2


def test_full_original_zero_and_repetition_asymmetry_is_not_an_eeg_claim():
    _,report,idx=original()
    closed=report["tasks"]["eyesclosed"]["sample_integrity"]
    opened=report["tasks"]["eyesopen"]["sample_integrity"]
    assert closed["exact_zero_sample_count"]==23558
    assert opened["exact_zero_sample_count"]==0
    assert closed["exact_adjacent_equal_within_channel_pairs"]==195420
    assert opened["exact_adjacent_equal_within_channel_pairs"]==7
    assert closed["median_native_numeric_epoch_ptp"]==61.5
    assert opened["median_native_numeric_epoch_ptp"]==57.717540741
    assert idx["no_lzc_or_psychological_or_thermodynamic_result"] is True
    assert idx["no_identifiable_original_signal_samples_published"] is True
    assert idx["clinical_mental_health_biomarker_claim"] is False


def test_first_original_sha_guard_rejects_tampering_even_with_forged_index(tmp_path):
    for src,name in ((FAILED,"failure.json"),(FIRST,"audit.json"),(INDEX,"archive-index.json")):
        copyfile(src,tmp_path/name)
    forged=tmp_path/"audit.json"
    forged.write_bytes(forged.read_bytes()+b" ")
    ix=tmp_path/"archive-index.json"
    meta=json.loads(ix.read_text(encoding="utf-8"))
    meta["first_successful_amplitude_run"]["sha256"]=sha256(forged.read_bytes()).hexdigest()
    ix.write_text(json.dumps(meta),encoding="utf-8")
    with pytest.raises(ValueError,match="first G02-R02 sample QC was altered"):
        original(tmp_path/"failure.json",forged,ix)
