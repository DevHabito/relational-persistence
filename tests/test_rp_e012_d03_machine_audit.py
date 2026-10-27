"""Synthetic-only adversarial gates for preregistered RP-E012-D03.

No provider raw rows are fetched during unit tests. The source-run action
will acquire only the one selected original machine file after green CI.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import md5, sha256
from io import BytesIO
import base64
import gzip
import json
import zlib

import pytest

from experiments import rp_e012_d03_machine_audit as d03


def row(time, machine, kind, **extras):
    record = {"time": str(time), "machine_id": str(machine), "type": str(kind)}
    record.update(extras)
    return record


def source_bytes(rows):
    expanded = b"".join(
        (json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for item in rows
    )
    return gzip.compress(expanded, mtime=0), expanded


def metadata_object(body, *, name="machine_events-000000000000.json.gz"):
    return {
        "name": name, "size": str(len(body)), "generation": "1596844153688368",
        "md5Hash": base64.b64encode(md5(body).digest()).decode(),
        "crc32c": "unverified-publisher-hash",
    }


def machine_listing(obj):
    return {
        "table": "machine_events",
        "inventory_incomplete_due_to_pagination": False,
        "matching_shards_on_first_page": 1,
    }, [obj]


def test_registered_fixed_window_budget_and_original_cell_are_frozen():
    assert d03.PREREG == "41befcd7970a86f558b50de8f66f89473920fa6e"
    assert d03.BUCKET == "clusterdata_2019_a"
    assert d03.TABLES == (
        "machine_events", "collection_events", "instance_events"
    )
    assert d03.ORIGINS == (1_000_000_000_000, 2_000_000_000_000)
    assert d03.MAX_COMPRESSED == 2_097_152
    assert d03.MAX_EXPANDED == 33_554_432
    assert d03.MAX_RECORDS == 100000


def test_only_unpaginated_singular_machine_shard_can_claim_full_inventory():
    body, _ = source_bytes([row(10, 5, 1)])
    obj = metadata_object(body)
    summary, listings = machine_listing(obj)
    assert d03.select_sole_machine_source(summary, listings)["name"] == obj["name"]
    with pytest.raises(d03.MachineCoverageFailure):
        d03.select_sole_machine_source(
            {**summary, "inventory_incomplete_due_to_pagination": True}, listings)
    with pytest.raises(d03.MachineCoverageFailure):
        d03.select_sole_machine_source(summary, listings*2)
    with pytest.raises(d03.MachineCoverageFailure):
        d03.select_sole_machine_source(summary, [])


def test_original_first_instance_shard_is_too_large_not_downloaded():
    obj = metadata_object(b"a")
    obj["name"] = "machine_events-000000000000.json.gz"
    obj["size"] = "465101721"
    summary, _ = machine_listing(obj)
    with pytest.raises(d03.MachineCoverageFailure, match="exceeds"):
        d03.select_sole_machine_source(summary, [obj])


def test_exact_machine_metadata_requires_genuine_generation_and_md5():
    body, _ = source_bytes([row(10, 5, 1)])
    obj = metadata_object(body)
    summary, _ = machine_listing(obj)
    for patch in (
        {"generation": "fake"}, {"size": "0"}, {"size": "-1"},
        {"md5Hash": None}
    ):
        with pytest.raises(d03.MachineCoverageFailure):
            d03.select_sole_machine_source(summary, [{**obj, **patch}])


def test_full_machine_gzip_includes_trailer_crc_and_exact_rows():
    compressed, raw = source_bytes([row(10, 3, 1), row(12, 3, 3, capacity={
        "cpus": 2.0}), row(18, 3, 2)])
    assert d03.decompress_full_gzip(compressed) == raw
    parsed = d03.parse_machine_events(raw)
    assert [e["type"] for e in parsed] == [1, 3, 2]
    assert parsed[1]["has_capacity"] is True


def test_original_crc_corruption_fails_and_cannot_be_called_authenticated():
    compressed, _ = source_bytes([row(10, 3, 1)])
    changed = bytearray(compressed)
    changed[-5] ^= 0x12
    with pytest.raises(d03.MachineFormatFailure, match="gzip"):
        d03.decompress_full_gzip(bytes(changed))


def test_gzip_truncation_and_trailing_junk_are_rejected():
    content, _ = source_bytes([row(10, 3, 1)])
    with pytest.raises(d03.MachineFormatFailure):
        d03.decompress_full_gzip(content[:-5])
    with pytest.raises(d03.MachineFormatFailure):
        d03.decompress_full_gzip(content + b"extra")


def test_missing_required_or_numeric_instead_of_publisher_string_rejected():
    _, raw = source_bytes([row(10, 3, 1)])
    for invalid in (
        {"time": 10, "machine_id": "3", "type": "1"},
        {"machine_id": "3", "type": "1"},
        {"time": "-1", "machine_id": "3", "type": "1"},
        {"time": "10", "machine_id": None, "type": "1"},
        {"time": "010", "machine_id": "3", "type": "1"},
    ):
        with pytest.raises((d03.MachineFormatFailure, d03.MachineOracleDisagreement)):
            d03.parse_machine_events((json.dumps(invalid)+"\n").encode())


@pytest.mark.parametrize("code", ["0", "4", "99"])
def test_machine_unknown_kind_does_not_become_known_event(code):
    with pytest.raises(d03.MachineFormatFailure):
        d03.parse_machine_events(
            (json.dumps(row(10, 1, code))+"\n").encode()
        )


def test_invalid_missing_kind_and_unquoted_kind_rejected():
    for entry in (row(10, 1, 1, missing_type="6"),
                  row(10, 1, 1, missing_type=2)):
        with pytest.raises((d03.MachineFormatFailure, d03.MachineOracleDisagreement)):
            d03.parse_machine_events((json.dumps(entry)+"\n").encode())


def test_unavailable_capacity_is_not_imputed_to_zero():
    events = d03.parse_machine_events(
        (json.dumps(row(10, 3, 1))+"\n").encode()
    )
    report = d03.summarize_all_original_machine_events(events)
    assert report["rows_with_capacity_field"] == 0
    assert report["distinct_machine_ids_aggregate_only"] == 1


def test_conflicting_type_tie_marks_state_ambiguous_at_both_origins():
    events = d03.parse_machine_events((
        json.dumps(row(10, 3, 1))+"\n"
        + json.dumps(row(10, 3, 2))+"\n"
    ).encode())
    details = d03.summarize_all_original_machine_events(events)
    assert details["same_machine_same_timestamp_tie_groups"] == 1
    assert details["conflicting_same_machine_same_timestamp_type_groups"] == 1
    assert details["snapshots_strict_before_origin"][
        "1000000000000"]["ambiguous_last_event_tie"] == 1


def test_reconstructed_latest_event_never_sets_exact_active_state():
    events = d03.parse_machine_events((
        json.dumps(row(10, 3, 1))+"\n"
        + json.dumps(row(12, 3, 3, missing_type="2"))+"\n"
    ).encode())
    out = d03.independent_snapshot_oracles(events, 15)
    assert out == {"uncertain_due_to_reconstructed_event": 1}


def test_original_off_order_input_is_ordered_before_causing_state():
    events = d03.parse_machine_events((
        json.dumps(row(30, 1, 2))+"\n"
        + json.dumps(row(10, 1, 1))+"\n"
    ).encode())
    data = d03.summarize_all_original_machine_events(events)
    assert data["original_file_adjacent_timestamp_inversions"] == 1
    assert d03.independent_snapshot_oracles(events, 20) == {
        "last_event_implied_active": 1
    }
    assert d03.independent_snapshot_oracles(events, 31) == {
        "last_event_implied_removed": 1
    }


def test_event_exactly_at_origin_is_not_visible_and_future_id_unknown():
    events = d03.parse_machine_events((
        json.dumps(row(10, 1, 1))+"\n"
        + json.dumps(row(20, 1, 2))+"\n"
        + json.dumps(row(20, 2, 1))+"\n"
    ).encode())
    assert d03.independent_snapshot_oracles(events, 20) == {
        "last_event_implied_active": 1, "no_prior_event": 1
    }
    assert d03.independent_snapshot_oracles(events, 21) == {
        "last_event_implied_active": 1, "last_event_implied_removed": 1
    }


def test_independent_oracle_disagreement_is_fatal(monkeypatch):
    events = [{"time": 10, "machine": 1, "type": 1, "missing": 0,
               "has_capacity": True}]
    monkeypatch.setattr(d03, "_latest_category", lambda rows, origin:
                        "last_event_implied_removed")
    with pytest.raises(d03.MachineOracleDisagreement):
        d03.independent_snapshot_oracles(events, 100)


def test_independent_text_core_oracle_rejects_duplicate_nested_keys():
    duplicate = b'{"time":"10","machine_id":"5","type":"1","time":"11"}\n'
    with pytest.raises(d03.MachineOracleDisagreement):
        d03.parse_machine_events(duplicate)


def test_empty_last_line_invalid_json_and_nan_rejected():
    for invalid in (
        b"", b'{"time":"10","machine_id":"5","type":"1"}',
        b"not-json\n",
        b'{"time":"10","machine_id":"5","type":"1","capacity":NaN}\n',
        b"\xff\n",
    ):
        with pytest.raises(d03.MachineFormatFailure):
            d03.parse_machine_events(invalid)


def test_expansion_bomb_is_rejected_before_expanding_unbounded():
    compressed = gzip.compress(b"x" * (d03.MAX_EXPANDED + 1), mtime=0)
    with pytest.raises(d03.MachineFormatFailure):
        d03.decompress_full_gzip(compressed)


def test_row_budget_and_source_bound_are_strict():
    original = d03.MAX_RECORDS
    d03.MAX_RECORDS = 3
    try:
        raw = b"".join((json.dumps(row(k, k, 1))+"\n").encode()
                       for k in range(4))
        with pytest.raises(d03.MachineFormatFailure):
            d03.parse_machine_events(raw)
    finally:
        d03.MAX_RECORDS = original


def test_original_negative_download_is_permanently_readable(monkeypatch, tmp_path):
    def blocked(table):
        raise d03.SourceAccess("original provider unavailable")
    monkeypatch.setattr(d03, "fetch_inventory_page", blocked)
    result = d03.audit_original()
    assert result["original_decision"] == "SOURCE_ACCESS_BLOCKED"
    assert result["joint_causal_history"] == "JOINT_CAUSAL_HISTORY_NOT_CERTIFIED"
    assert result["errors"]
    assert result["collection_and_instance_raw_event_rows_downloaded"] == 0


def test_no_forecast_no_actual_online_release_semantics():
    data = d03.parse_machine_events((
        json.dumps(row(10, 3, 1))+"\n").encode())
    report = d03.summarize_all_original_machine_events(data)
    assert report["event_implied_state_not_full_live_capacity"] is True
    assert report["timestamp_is_not_proven_online_release_time"] is True
    assert report["no_observed_machine_ids_or_event_rows_persisted"] is True
