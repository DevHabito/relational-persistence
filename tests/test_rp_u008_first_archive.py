"""Immutable first RP-U008 external original source and endpoint recovery replay."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from experiments import rp_u008_external_recovery_core as core
from experiments import rp_u008_external_source as source

PATH = Path("docs/results/RP-U008-P01-first-run/audit.json")
BYTES = 30225
DIGEST = "8daf823275e8d55bee29f5cb68458449f5a14005f7b7cc279e3c42d77d9d2d38"


def original() -> dict:
    b = PATH.read_bytes()
    assert len(b) == BYTES
    assert sha256(b).hexdigest() == DIGEST
    return json.loads(b)


def test_original_external_publisher_census_and_strict_data_identity():
    j = original()
    assert j["study"] == core.STUDY
    assert j["status"] == "RP_U008_TWO_OR_MORE_POSITIVE_HTTP_LAGS_OBSERVED"
    assert j["protocol_only_commit"] == source.PROTOCOL_ONLY_COMMIT
    assert j["source"]["publisher_commit"] == core.SOURCE_COMMIT
    assert j["source"]["publisher_original_git_blob_sha1"] == core.SOURCE_BLOB_SHA1
    assert j["source"]["original_bytes"] == core.SOURCE_SIZE
    assert j["source"]["original_sha256"] == (
        "5a3d86be7127e27ebac8bf7071c4ee1991b2a2cb00f93fab8967310ca116b977"
    )
    assert j["raw_record_count"] == core.SOURCE_ROWS == 54_617
    assert j["publisher_card_outages_previously_known"] is True
    assert j["original_outage_identification_not_claimed"] is True
    assert j["no_proven_physical_repair_or_independent_hardware_measurement"] is True


def test_exact_registered_four_events_and_all_prepost_windows():
    j = original()
    assert j["all_candidate_down_runs"] == 4
    assert j["three_plus_row_eligible_events"] == 4
    assert j["excluded_short_runs"] == []
    assert j["complete_first_hop_http_recovery_census"] is True
    assert j["gateway_and_http_positive_lag_count"] == 2
    assert len(j["events"]) == 4
    assert [e["down_sample_count"] for e in j["events"]] == [4,5,5,4]
    assert [e["lag_http_bins"] for e in j["events"]] == [0,0,1,1]
    assert [e["lag_http_quality_bins"] for e in j["events"]] == [0,1,1,1]
    assert [e["lag_http_timestamp_seconds"] for e in j["events"]] == [0,0,25,32]
    for e in j["events"]:
        assert e["eligible"] is True
        assert e["gateway_right_censored"] is False
        assert e["http_right_censored"] is False
        assert e["http_quality_right_censored"] is False
        assert len(e["samples_pre"]) == 5 and len(e["samples_post"]) == 10


def test_independent_endpoint_replay_uses_only_archived_first_original_window():
    j = original()
    for e in j["events"]:
        post = e["samples_post"]
        times = [
            int(datetime.strptime(x["utc"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc).timestamp())
            for x in post
        ]
        def second_row(feature):
            for i in range(1, len(post)):
                if (post[i-1][feature] and post[i][feature]
                        and 0 < times[i]-times[i-1] <= 75):
                    return i+1
            return None
        gw = second_row("gateway_icmp_reachable")
        http = second_row("http_success")
        quality = second_row("http_usable_le_1000ms")
        assert gw == e["recovery_gateway_index"]
        assert http == e["recovery_http_index"]
        assert quality == e["recovery_http_quality_index"]
        assert http - gw == e["lag_http_bins"]
        assert quality - gw == e["lag_http_quality_bins"]
        assert times[http-1] - times[gw-1] == e["lag_http_timestamp_seconds"]


def test_first_source_artifact_index_identifies_only_original_run():
    d = json.loads(Path(
        "docs/results/RP-U008-P01-first-run/archive-index.json"
    ).read_text(encoding="utf-8"))
    assert d["original_audit_bytes"] == BYTES
    assert d["original_audit_sha256"] == DIGEST
    assert d["artifact_id"] == 14385845936
    assert d["first_original_workflow_job"] == 134484275437
    assert d["original_source_records"] == 54617
    assert d["all_eligible"] == 4
    assert d["basic_http_lag_positive"] == 2
    assert d["http_quality_lag_positive"] == 3
    assert d["original_first_status"] == original()["status"]
