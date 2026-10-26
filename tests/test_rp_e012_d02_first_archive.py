"""Pin the ORIGINAL and bounded real-production RP-E012-D02 GCS evidence.

Source prefix bytes are never copied to Git. This tests the original
*report* bytes, SHA identities and exact first-prefix observations,
not any full original GCS object or independently re-fetched source.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/results/RP-E012-D02-first-run"
RUN = "40421367613"
PREREG = "e5efc72498fb3377aed4fd5302a288df95c57a23"
CODE = "1d10146eca6c6c18caa4f06b8c30415d2f5f28dd"
AUDIT_SHA = "15ffce6c25efdcd37ac23d4992db1b3f0fbfb901ba79260e2377b5268edcfb3c"


def original():
    raw = (DIR / "audit.json").read_bytes()
    report = json.loads(raw)
    index = json.loads((DIR / "archive-index.json").read_text("utf-8"))
    return raw, report, index


def test_first_run_report_bytes_and_preregistration_unchanged():
    raw, report, index = original()
    assert sha256(raw).hexdigest() == AUDIT_SHA
    assert index["first_report_sha256"] == AUDIT_SHA
    assert report["protocol"] == index["protocol"] == "RP-E012-D02"
    assert report["preregistration_commit"] == index["preregistration_commit"] == PREREG
    assert report["first_run_id"] == index["first_run_id"] == RUN
    assert report["original_code_commit"] == index["first_code_commit"] == CODE
    assert report["decision"] == index["original_decision"] == "SOURCE_PREFIX_AUDITED"
    assert report["errors"] == []
    assert sorted(path.name for path in DIR.iterdir()) == [
        "archive-index.json", "audit.json"
    ]


def test_both_original_objects_have_generation_and_exact_prefix_sha():
    _, report, _ = original()
    cases = {
        "machine_events": {
            "generation": "1596844153688368",
            "name": "machine_events-000000000000.json.gz",
            "full_object_size_bytes": "651854",
            "compressed_prefix_sha256":
                "1bd079d9e35f525287cb65995969991ab607b916ec86614653f552cfadaedd47",
        },
        "instance_events": {
            "generation": "1596841812600976",
            "name": "instance_events-000000000000.json.gz",
            "full_object_size_bytes": "465101721",
            "compressed_prefix_sha256":
                "5d0ff0b9109ae5c447089b15a4cb618accf9356e52b578ca2956a0af4c5c3ae9",
        },
    }
    assert report["source_bucket"] == "clusterdata_2019_a"
    for table, constants in cases.items():
        obj = report["table_evidence"][table]["object_metadata"]
        prefix = report["table_evidence"][table]["prefix"]
        assert obj["generation"] == constants["generation"]
        assert obj["name"] == constants["name"]
        assert obj["full_object_size_bytes"] == constants["full_object_size_bytes"]
        assert prefix["compressed_prefix_sha256"] == constants[
            "compressed_prefix_sha256"
        ]
        assert prefix["compressed_prefix_bytes_consumed"] == 16384
        assert prefix["parsed_complete_prefix_rows"] == 500
        assert prefix["http_status"] == 206
        assert prefix["server_honored_range"] is True
        assert prefix["server_object_generation_confirmed"] is True
        assert prefix["requested_range"] == "bytes=0-2097151"


def test_sample_is_not_a_full_source_or_crc_validated_complete_member():
    _, report, _ = original()
    for row in report["table_evidence"].values():
        prefix = row["prefix"]
        assert prefix["full_object_digest_verified"] is False
        assert prefix["gzip_member_end_reached"] is False
        assert prefix["gzip_trailer_validated"] is False
        assert prefix["not_a_population_representative_sample"] is True
        assert prefix["no_production_ids_or_raw_lines_retained"] is True
        assert prefix["no_provider_runtime_walltime_enforcement_verified"] is True


def test_orig_machine_add_events_and_order_inversions_remain_adverse():
    _, report, _ = original()
    p = report["table_evidence"]["machine_events"]["prefix"]
    assert p["event_type_counts_prefix_only"] == {"1": 500}
    assert p["rows_with_nonzero_missing_event_flag"] == 0
    assert p["adjacent_event_time_inversions_in_prefix"] == 258
    assert p["optional_field_presence_counts_prefix_only"]["capacity"] == 41
    assert p["time_min_microseconds_from_trace_start"] == 0
    assert p["time_max_microseconds_from_trace_start"] == 2_640_239_818_406


def test_original_instance_submit_lost_and_nonzero_missing_not_suppressed():
    _, report, _ = original()
    p = report["table_evidence"]["instance_events"]["prefix"]
    assert p["event_type_counts_prefix_only"] == {"0": 495, "8": 5}
    assert p["rows_with_declared_missing_flag"] == 5
    assert p["rows_with_nonzero_missing_event_flag"] == 5
    assert p["adjacent_event_time_inversions_in_prefix"] == 183
    assert p["optional_field_presence_counts_prefix_only"]["resource_request"] == 500
    assert p["optional_field_presence_counts_prefix_only"]["machine_id"] == 8
    assert p["time_min_microseconds_from_trace_start"] == 82_373_323_250
    assert p["time_max_microseconds_from_trace_start"] == 2_669_831_496_698


def test_first_1000_rows_do_not_claim_empirical_queue_prediction_or_hard_cap():
    _, report, index = original()
    assert report["synthetic_strict_causal_boundary_passed"] is True
    assert report["production_rows_are_nonrepresentative_prefixes"] is True
    assert report["complete_event_history_asserted"] is False
    assert report["bigquery_used"] is False
    assert report["user_auth_or_paid_query_used"] is False
    assert report["forecast_or_holdout_calculated"] is False
    assert report["physical_scalar_C_or_new_lean_theorem_claimed"] is False
    assert index["production_data_rows_committed_to_git"] is False
    assert index["no_bigquery_user_auth_or_paid_query"] is True
    assert index["original_e010_e011_negative_results_unchanged"] is True
    assert index["new_lean_theorem_claimed"] is False


def test_any_report_byte_change_would_break_original_integrity():
    raw, _, _ = original()
    assert sha256(raw + b"\n").hexdigest() != AUDIT_SHA
