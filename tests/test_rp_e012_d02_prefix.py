"""Synthetic adversarial tests for RP-E012-D02 GCS original-prefix audit.

No test downloads or opens any raw Google production event or metadata.
They prevent reclassification of false/source-incomplete evidence as PASS.
"""

from __future__ import annotations

import gzip
import io
import json

import pytest

from experiments import rp_e012_d02_prefix as d02


def gzip_rows(rows: list[dict]) -> bytes:
    return gzip.compress(b"".join(
        (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    ), mtime=0)


def example_machine(**changes):
    result = {"time": "100", "type": "1", "machine_id": "123",
              "switch_id": "obfuscated"}
    result.update(changes)
    return result


def example_instance(**changes):
    result = {"time": "101", "type": "3", "collection_id": "44",
              "instance_index": "0", "missing_type": "0",
              "priority": "2"}
    result.update(changes)
    return result


def fixture_listing(table):
    return {"items": [
        {"name": f"{table}-000000000003.json.gz",
         "generation": "103", "size": "2500", "crc32c": "later-shard"},
        {"name": f"{table}-000000000000.json.gzip",
         "generation": "100", "size": "999",
         "md5Hash": "metadata-only-original-full-hash"},
    ], "nextPageToken": "unvisited-and-not-allowed"}


def test_frozen_bucket_table_sampling_limits_and_no_cost():
    assert d02.PREREG == "e5efc72498fb3377aed4fd5302a288df95c57a23"
    assert d02.TABLES == ("machine_events", "instance_events")
    assert d02.BUCKET == "clusterdata_2019_a"
    assert d02.MAX_COMPRESSED == 2_097_152
    assert d02.MAX_UNCOMPRESSED == 4_194_304
    assert d02.MAX_ROWS == 500
    assert d02.synthetic_temporal_safety_gate()


def test_exact_first_lexical_gzip_shard_even_when_metadata_unsorted():
    first = d02.select_exact_first_shard("machine_events",
                                        fixture_listing("machine_events"))
    assert first["name"] == "machine_events-000000000000.json.gzip"
    assert first["generation"] == "100"
    assert first["first_100_listing_was_paginated"] is True
    assert first["provider_md5Hash_whole_object_unverified"]
    address = d02.media_url(first["name"], first["generation"])
    assert address.startswith("https://storage.googleapis.com/storage/v1/")
    assert "generation=100" in address
    assert "alt=media" in address


def test_unregistered_buckets_tables_and_object_names_rejected():
    with pytest.raises(d02.SourceAccess, match="Unregistered"):
        d02.metadata_url("collection_events")
    with pytest.raises(d02.SourceAccess, match="Unregistered"):
        d02.media_url("../../admin", "100")
    with pytest.raises(d02.SourceAccess, match="generation"):
        d02.media_url("machine_events-000000000000.json.gz", "not-a-number")


def test_missing_official_list_never_selects_mirror():
    with pytest.raises(d02.SourceAccess, match="No frozen-table"):
        d02.select_exact_first_shard("machine_events", {
            "items": [{"name": "random-other-name.parquet",
                       "generation": "100", "size": "2000"}]
        })
    with pytest.raises(d02.SourceAccess):
        d02.select_exact_first_shard("machine_events", {"items": []})


def test_machine_one_complete_line_and_not_guaranteed_capacity():
    compressed = gzip_rows([example_machine()])
    report = d02.parse_bounded_gzip_prefix([compressed], "machine_events")
    assert report["parsed_complete_prefix_rows"] == 1
    assert report["event_type_counts_prefix_only"] == {"1": 1}
    assert report["time_min_microseconds_from_trace_start"] == 100
    assert report["rows_with_nonzero_missing_event_flag"] == 0
    assert report["gzip_trailer_validated"] is True
    assert report["not_a_population_representative_sample"] is True
    assert "capacity" not in example_machine()


def test_instance_complete_source_has_distinct_event_and_flag_types():
    records = [
        example_instance(type="0", time="100", missing_type="0"),
        example_instance(type="3", time="101", missing_type="2"),
        example_instance(type="6", time="100", missing_type="5"),
    ]
    report = d02.parse_bounded_gzip_prefix(
        [gzip_rows(records)], "instance_events"
    )
    assert report["parsed_complete_prefix_rows"] == 3
    assert report["rows_with_declared_missing_flag"] == 3
    assert report["rows_with_nonzero_missing_event_flag"] == 2
    assert report["adjacent_event_time_inversions_in_prefix"] == 1
    assert report["event_type_counts_prefix_only"] == {
        "0": 1, "3": 1, "6": 1
    }


def test_prefix_truncation_never_promotes_incomplete_json_record():
    complete = (json.dumps(example_machine()) + "\n").encode()
    unfinished = b'{"time":"'
    compressed = gzip.compress(complete + unfinished, mtime=0)
    result = d02.parse_bounded_gzip_prefix([compressed], "machine_events")
    assert result["parsed_complete_prefix_rows"] == 1
    assert result["incomplete_trailing_line_not_parsed"] is True


def test_bounded_stream_stops_after_first_500_complete_rows():
    compressed = gzip_rows([example_machine(time=str(i+1))
                            for i in range(1000)])
    # Deliberately split to reveal whether second chunk was consumed.
    fragments = [compressed[:80], compressed[80:]]
    report = d02.parse_bounded_gzip_prefix(fragments, "machine_events")
    assert report["parsed_complete_prefix_rows"] == 500
    assert report["time_max_microseconds_from_trace_start"] == 500


@pytest.mark.parametrize("invalid", [
    {"time": 100}, # JSON number instead of original decimal string
    {"time": "-1"},
    {"time": "1.5"},
    {"time": "01"},
    {"type": "0"},
    {"type": "4"},
    {"machine_id": None},
])
def test_machine_bad_time_identity_type_invalid(invalid):
    obj = example_machine(**invalid)
    with pytest.raises(d02.PrefixInvalid):
        d02.parse_bounded_gzip_prefix([gzip_rows([obj])], "machine_events")


@pytest.mark.parametrize("invalid", [
    {"time": None},
    {"type": "11"},
    {"missing_type": "7"},
    {"collection_id": 44},
    {"instance_index": 0},
])
def test_instance_invalid_types_and_missing_event_flags_rejected(invalid):
    with pytest.raises(d02.PrefixInvalid):
        d02.parse_bounded_gzip_prefix(
            [gzip_rows([example_instance(**invalid)])], "instance_events"
        )


def test_missing_core_identity_must_fail_not_be_imputed():
    row = example_instance()
    row.pop("collection_id")
    with pytest.raises(d02.PrefixInvalid, match="Missing mandatory"):
        d02.parse_bounded_gzip_prefix(
            [gzip_rows([row])], "instance_events"
        )


def test_invalid_utf8_and_invalid_json_stop():
    with pytest.raises(d02.PrefixInvalid):
        d02.parse_bounded_gzip_prefix(
            [gzip.compress(b"\xff\n", mtime=0)], "machine_events")
    with pytest.raises(d02.PrefixInvalid):
        d02.parse_bounded_gzip_prefix(
            [gzip.compress(b"{bad!}\n", mtime=0)], "machine_events")


def test_explosive_gzip_expansion_aborts_without_storing_raw_data():
    large = b"X" * (d02.MAX_UNCOMPRESSED + 1)
    compressed = gzip.compress(large, compresslevel=9, mtime=0)
    with pytest.raises(d02.PrefixInvalid, match="expansion"):
        d02.parse_bounded_gzip_prefix([compressed], "machine_events")


def test_compressed_byte_limit_closes_source():
    with pytest.raises(d02.PrefixInvalid, match="Compressed prefix"):
        d02.parse_bounded_gzip_prefix(
            [b"Z" * (d02.MAX_COMPRESSED + 1)], "machine_events")


def test_an_empty_or_only_truncated_record_does_not_count_as_audit():
    with pytest.raises(d02.PrefixInvalid, match="No complete"):
        d02.parse_bounded_gzip_prefix(
            [gzip.compress(b'{"time":"100"', mtime=0)], "machine_events"
        )


def test_no_contemporary_event_or_future_window_leak():
    assert d02.strictly_available(99, 100)
    assert not d02.strictly_available(100, 100)
    assert not d02.strictly_available(101, 100)
    assert not d02.strictly_available(99, 100, reconstructed=True)
    assert d02.usage_window_available(0, 300, 301)
    assert not d02.usage_window_available(0, 300, 300)
    assert not d02.usage_window_available(0, 300, 150)


def test_access_failure_always_archived_as_blocked(monkeypatch, tmp_path):
    def blocked(_):
        raise d02.SourceAccess("public source requires requester billing")
    monkeypatch.setattr(d02, "list_official", blocked)
    source = tmp_path / "RP-E012-D02.json"
    report = d02.run_first(source)
    assert report["decision"] == "SOURCE_ACCESS_OR_LISTING_BLOCKED"
    assert report["table_evidence"] == {}
    assert report["bigquery_used"] is False
    assert report["user_auth_or_paid_query_used"] is False
    assert json.loads(source.read_text()) == report
    with pytest.raises(ValueError, match="overwrite"):
        d02.run_first(source)


def test_gzip_oracle_error_archived_as_rejection(monkeypatch, tmp_path):
    monkeypatch.setattr(d02, "list_official",
                        lambda table: d02.select_exact_first_shard(
                            table, fixture_listing(table)))
    def source_invalid(*_):
        raise d02.PrefixInvalid("fixture deliberately corrupt original")
    monkeypatch.setattr(d02, "read_exact_prefix", source_invalid)
    output = tmp_path / "bad.json"
    report = d02.run_first(output)
    assert report["decision"] == "SOURCE_PREFIX_FORMAT_REJECTED"
    assert len(report["errors"]) == 1
    assert report["errors"][0]["table"] == "machine_events"
    assert report["forecast_or_holdout_calculated"] is False


def test_fixed_success_needs_both_tables(monkeypatch, tmp_path):
    monkeypatch.setattr(d02, "list_official",
                        lambda table: d02.select_exact_first_shard(
                            table, fixture_listing(table)))
    monkeypatch.setattr(d02, "read_exact_prefix",
                        lambda table, metadata: {
                            "parsed_complete_prefix_rows": 1,
                            "event_type_counts_prefix_only": {
                                "1" if table == "machine_events" else "3": 1
                            },
                            "no_production_ids_or_raw_lines_retained": True,
                        })
    original = d02.run_first(tmp_path / "yes.json")
    assert original["decision"] == "SOURCE_PREFIX_AUDITED"
    assert list(original["table_evidence"]) == list(d02.TABLES)
    assert original["forecast_or_holdout_calculated"] is False
    assert original["production_rows_are_nonrepresentative_prefixes"] is True
