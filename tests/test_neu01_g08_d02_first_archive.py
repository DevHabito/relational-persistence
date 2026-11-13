"""Immutable original D02 source outcome; preserve initial failed synthetic run."""
from hashlib import sha256
import json
from pathlib import Path

ORIGINAL=Path("docs/results/NEU-01-G08-D02-first-run/audit.json")
INDEX=Path("docs/results/NEU-01-G08-D02-first-run/archive-index.json")
EXPECTED="a0fe888346e76de66672b41aa5634d45a5798a56633f7fd551d06de5747ae0a8"


def test_original_audit_byte_hash_and_size():
    body=ORIGINAL.read_bytes()
    assert len(body)==2332
    assert sha256(body).hexdigest()==EXPECTED
    assert body.endswith(b"\n")


def test_original_first_attempt_failed_before_source_and_is_retained():
    record=json.loads(INDEX.read_text())
    assert record["protocol_only_commit"]=="a5f5dd11d8ed95d618ca718bb7b9eec9ea32664a"
    assert record["first_pre_source_test_failure"]["workflow_run_id"]==43336398552
    assert record["first_pre_source_test_failure"]["original_source_access_attempted"] is False
    assert record["dated_pre_source_assertion_fix_commit"]=="03cdc3e6083518996c6eb98602e23b126937b59b"
    assert record["first_real_source_workflow_run_id"]==43336512537
    assert record["passing_pre_source_synthetic_tests"]==7
    assert record["original_artifact"]["id"]==13997710715
    assert record["first_original_audit_json"]["sha256"]==EXPECTED


def test_exact_zero_projected_residual_and_same_source_counts_not_overclaimed():
    x=json.loads(ORIGINAL.read_text())
    assert x["status"]=="G08_D02_RESIDUAL_CENSUS_COMPLETE"
    assert x["posthoc_after_original_G08_P01_pearson_one"] is True
    assert x["root_census_reconciles_with_G05"] is True
    assert x["root_native_census"]==x["derivative_native_census"]
    assert x["root_native_census"]["within_channel_equal_adjacent"]==130491
    assert x["root_native_census"]["nonzero_equal_adjacent"]==130304
    p=x["globally_projected_model"]
    assert p["shared_least_squares_gain"]==1.
    assert p["fixed_gain_one_relative_frobenius_residual"]==0.
    assert p["fitted_gain_relative_frobenius_residual"]==0.
    assert p["fixed_gain_one_max_abs_projected_error_native"]==0.
    assert p["fitted_gain_max_abs_projected_error_native"]==0.
    assert p["fixed_500_frame_shift_same_gain_residual"]>0.
    assert p["fixed_channel_reversal_same_gain_residual"]>0.
    assert x["source_physical_gain_validated"] is False
    assert x["neural_population_or_thermodynamics_claim"] is False
    assert x["original_binary_uploaded"] is False


def test_any_mutation_changes_first_source_digest():
    b=ORIGINAL.read_bytes()
    changed=b.replace(b"G08_D02_RESIDUAL_CENSUS_COMPLETE",b"G08_D02_UNSUPPORTED_RESULT",1)
    assert changed!=b
    assert sha256(changed).hexdigest()!=EXPECTED
