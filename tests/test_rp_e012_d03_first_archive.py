"""First-original RP-E012-D03 source-audit pin: 46,219 real machine events.

Authenticate original Git-archived report SHA; no Google content downloads
or reproduction of hidden source rows in this regression suite.
"""

from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "docs/results/RP-E012-D03-first-run"
REPORT_SHA = "393ed949a3aec3e4cd27f6e6ca8f617102b855a5e0934021d3b6909be31b6f0a"
SOURCE_SHA = "b04455f48e57c303fc8987b41e35911d89f3aa31e5a6d3997f07e27749dc1791"
RUN = "40425342721"
CODE = "5d05d53c8058efab38907dc9f01a65708bf2d9f7"
PROTOCOL = "41befcd7970a86f558b50de8f66f89473920fa6e"


def read_original():
    raw = (FIRST / "audit.json").read_bytes()
    data = json.loads(raw)
    index = json.loads((FIRST / "archive-index.json").read_text("utf-8"))
    return raw, data, index


def test_original_run_commit_protocol_sha_and_first_decision_are_frozen():
    raw, data, index = read_original()
    assert sha256(raw).hexdigest() == REPORT_SHA == index["first_report_sha256"]
    assert data["protocol"] == index["protocol"] == "RP-E012-D03"
    assert data["preregistration_commit"] == index["preregistration_commit"] == PROTOCOL
    assert data["original_code_commit"] == index["original_code_commit"] == CODE
    assert data["first_run_id"] == index["first_run_id"] == RUN
    assert data["original_decision"] == index["first_original_decision"] == (
        "MACHINE_EVENTS_COMPLETE_OBJECT_AUDITED_JOINT_UNCERTIFIED"
    )
    assert data["errors"] == []
    assert sorted(file.name for file in FIRST.iterdir()) == [
        "archive-index.json", "audit.json"
    ]


def test_first_complete_actual_machine_file_provenance_not_prefix_claim():
    _, data, index = read_original()
    obj = data["machine_source"]
    assert obj["name"] == "machine_events-000000000000.json.gz"
    assert obj["generation"] == "1596844153688368"
    assert obj["advertised_full_size_bytes"] == obj["full_object_bytes_downloaded"] == 651854
    assert obj["entire_object_authenticated_not_prefix_only"] is True
    assert obj["full_object_http_status"] == 200
    assert obj["full_object_provider_md5_verified"] is True
    assert obj["publisher_generation_requested"] == obj["generation"]
    assert obj["provider_full_md5_base64"] == "vf+o5W7VQu6rr8+BfU93aw=="
    assert obj["original_full_compressed_object_sha256"] == (
        index["actual_machine_object_original_sha256"]
    ) == SOURCE_SHA
    assert obj["provider_crc32c_base64_unverified"] == "thWuKw=="


def test_exact_complete_machine_counts_and_all_original_timestamps():
    _, data, _ = read_original()
    record = data["machine_counts"]
    assert record["all_complete_machine_event_rows"] == 46219
    assert record["distinct_machine_ids_aggregate_only"] == 10001
    assert record["event_type_counts"] == {
        "1": 27777, "2": 17941, "3": 501
    }
    assert sum(record["event_type_counts"].values()) == 46219
    assert record["rows_with_capacity_field"] == 45760
    assert record["rows_with_nonzero_missing_type"] == 0
    assert record["missing_type_code_counts"] == {"0": 46219}
    assert record["original_file_adjacent_timestamp_inversions"] == 18274
    assert record["original_minimum_timestamp_us"] == 0
    assert record["original_maximum_timestamp_us"] == 2678851683489
    assert record["same_machine_same_timestamp_tie_groups"] == 0
    assert record["conflicting_same_machine_same_timestamp_type_groups"] == 0


def test_two_original_strict_before_origin_state_classifications_partition():
    _, data, _ = read_original()
    snapshots = data["machine_counts"]["snapshots_strict_before_origin"]
    assert snapshots == {
        "1000000000000": {
            "last_event_implied_active": 9841,
            "last_event_implied_removed": 63,
            "no_prior_event": 97,
        },
        "2000000000000": {
            "last_event_implied_active": 9825,
            "last_event_implied_removed": 121,
            "no_prior_event": 55,
        }
    }
    for partition in snapshots.values():
        assert sum(partition.values()) == 10001


def test_original_shard_inventory_is_not_cross_table_completeness():
    _, data, index = read_original()
    pages = data["metadata_first_page"]
    assert pages["machine_events"]["matching_shards_on_first_page"] == 1
    assert pages["machine_events"]["inventory_incomplete_due_to_pagination"] is False
    assert pages["collection_events"]["matching_shards_on_first_page"] == 10
    assert pages["collection_events"]["inventory_incomplete_due_to_pagination"] is False
    assert pages["collection_events"]["selected_first_size_bytes_metadata_only"] == (
        "133462892"
    )
    assert pages["instance_events"]["matching_shards_on_first_page"] == 50
    assert pages["instance_events"]["inventory_incomplete_due_to_pagination"] is True
    assert pages["instance_events"]["selected_first_size_bytes_metadata_only"] == (
        "465101721"
    )
    assert pages["instance_events"]["sum_first_page_listed_sizes_bytes_not_total"] == (
        "27398516613"
    )
    assert data["joint_causal_history"] == "JOINT_CAUSAL_HISTORY_NOT_CERTIFIED"
    assert index["all_cross_table_states_certified"] is False
    assert data["collection_and_instance_raw_event_rows_downloaded"] == 0
    assert index["collection_or_instance_raw_rows_downloaded"] is False


def test_first_original_scope_keeps_all_external_negatives_and_no_real_time_claim():
    _, data, index = read_original()
    assert data["full_online_event_release_history_proven"] is False
    assert data["real_running_job_hard_walltime_cap_verified"] is False
    assert data["forecast_targets_computed"] is False
    assert data["bigquery_or_paid_credentials_used"] is False
    assert data["new_lean_theorem_or_physical_law_claimed"] is False
    assert index["bigquery_or_billing_used"] is False
    assert index["prediction_or_new_lean_theorem_proposed"] is False
    assert data["machine_counts"]["timestamp_is_not_proven_online_release_time"] is True
    assert data["machine_counts"]["no_observed_machine_ids_or_event_rows_persisted"] is True
    assert data["machine_counts"]["event_implied_state_not_full_live_capacity"] is True


def test_any_mutated_original_report_breaks_registered_digest():
    raw, _, _ = read_original()
    assert sha256(raw + b"\n").hexdigest() != REPORT_SHA
