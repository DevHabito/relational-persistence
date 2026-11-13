"""Immutable original direct 9,150,000-value IEEE identity source experiment."""
from hashlib import sha256
import json
from pathlib import Path

AUDIT=Path("docs/results/NEU-01-G08-D03-first-run/audit.json")
INDEX=Path("docs/results/NEU-01-G08-D03-first-run/archive-index.json")
SHA="0a20ff8636afd7c90057fbd852c55864fd6192b9094dc7310680f40557e54e46"


def test_original_first_source_bytes_sha256():
    b=AUDIT.read_bytes()
    assert len(b)==1865
    assert sha256(b).hexdigest()==SHA
    assert b.endswith(b"\n")


def test_source_run_and_original_protocol_freeze():
    p=json.loads(INDEX.read_text())
    assert p["protocol_only_commit"]=="795f3227641e46c972ebcfaf6aedd000c667173e"
    assert p["first_source_workflow_run_id"]==43337338166
    assert p["first_source_implementation_commit"]=="9494ab39da2b4e6635147f5ae019b028968e4491"
    assert p["passing_pre_source_synthetic_tests"]==6
    assert p["original_artifact"]["id"]==13997791342
    assert p["first_original_audit_json"]["sha256"]==SHA
    assert p["full_regression_at_original_source_commit"]["python_311_passed"]==968
    assert p["full_regression_at_original_source_commit"]["python_312_passed"]==968


def test_exact_ieee_widening_not_mistaken_for_full_file_identity():
    d=json.loads(AUDIT.read_text())
    assert d["status"]=="EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
    assert d["explicitly_posthoc_after_G08_P01_and_D02"] is True
    assert d["other_five_derivative_arrays_compared"] is False
    o=d["direct_IEEE_comparison"]
    assert o["all_aligned_numeric_values_count"]==9150000
    assert o["numeric_equal_count"]==9150000
    assert o["numeric_differ_count"]==0
    assert o["ieee_64bit_pattern_equal_count"]==9150000
    assert o["ieee_64bit_pattern_differ_count"]==0
    assert o["maximum_absolute_native_numeric_difference"]==0
    assert o["canonical_64bit_content_digests_identical"] is True
    assert o["source_original_double_canonical_sha256"]==o["derivative_double_canonical_sha256"]
    assert o["fixed_500_frame_shift_exact_numeric_equal_count"]==18659
    assert o["fixed_reversed_61_channel_exact_numeric_equal_count"]==154674
    assert o["source_float32_exactly_widened_to_float64"] is True
    assert d["exact_historical_preprocessing_operations_proven"] is False
    assert d["brain_or_thermodynamic_outcome_measured"] is False
    assert d["raw_signal_uploaded"] is False


def test_mutated_original_source_outcome_not_identical():
    b=AUDIT.read_bytes()
    c=b.replace(b"EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL",b"FALSE_UNVERIFIED_IDENTITY",1)
    assert c!=b
    assert sha256(c).hexdigest()!=SHA
