"""RP-U008 synthetic-only outage and application recovery adversarial controls.

None of these tests loads any original LocalNet-Dynamics CSV records.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

import pytest

from experiments import rp_u008_external_recovery_core as core


def make_rows(*, positions=(6,7,8,9), http_restarts=10,
              gateway_restarts=10, samples=28):
    begin=datetime(2026,1,1,tzinfo=timezone.utc)
    rows=[]
    for i in range(samples):
        stamp=begin+timedelta(seconds=30*i)
        is_down=i in positions
        gw_ok=(i < positions[0]) or (i >= gateway_restarts)
        http_ok=(i < positions[0]) or (i >= http_restarts)
        rows.append({
            "utc":stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "epoch":int(stamp.timestamp()),"sent":10,
            "received":0 if is_down else 10,
            "loss_pct":100.0 if is_down else 0.0,
            "gateway_loss_pct":100.0 if not gw_ok else 0.0,
            "gateway_rtt_ms":None if not gw_ok else .2,
            "http_status":200 if http_ok else None,
            "http_ms":90.0 if http_ok else None,
            "tcp_ms":14.0 if http_ok else None,
            "dns_ms":40.0 if http_ok else None,
        })
    return rows


def text_csv(rows):
    import csv
    from io import StringIO
    fd=StringIO()
    writer=csv.DictWriter(fd,fieldnames=(
        "timestamp_utc","epoch_s","run_id","packets_sent","packets_received",
        "packet_loss_pct","gateway_packet_loss_pct","gateway_rtt_avg_ms",
        "http_status","http_ms","tcp_connect_median_ms","dns_resolve_ms"
    ))
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "timestamp_utc":row["utc"],"epoch_s":row["epoch"],
            "run_id":core.EXPECTED_RUN_ID,"packets_sent":row["sent"],
            "packets_received":row["received"],"packet_loss_pct":row["loss_pct"],
            "gateway_packet_loss_pct":row["gateway_loss_pct"],
            "gateway_rtt_avg_ms":row["gateway_rtt_ms"],
            "http_status":row["http_status"],"http_ms":row["http_ms"],
            "tcp_connect_median_ms":row["tcp_ms"],"dns_resolve_ms":row["dns_ms"]
        })
    return fd.getvalue()


def test_exact_external_source_identity_and_register_before_rows():
    assert core.SOURCE_COMMIT=="d57ca705bfd2b0340b6476a2d01553d2c967636e"
    assert core.SOURCE_BLOB_SHA1=="d3a5a90f1a21125e06f2dbc1047a082f748dac1c"
    assert core.SOURCE_SIZE==15_143_900
    assert core.SOURCE_ROWS==54_617
    assert core.EXPECTED_OUTAGES==4
    assert core.POST_ROWS==10 and core.PRE_ROWS==5
    assert core.HTTP_LAG_REPETITION_THRESHOLD==2


def test_raw_parsing_and_fidelity_to_gateway_packet_counts():
    rows=make_rows()
    parsed=core.parse_original(text_csv(rows),enforce_publisher_census=False)
    assert len(parsed)==len(rows)
    assert parsed[6]["received"]==0
    assert parsed[6]["http_status"] is None
    assert core.find_down_runs(parsed)==[(6,9)]
    assert core.independent_down_runs(parsed)==[(6,9)]


def test_one_valid_event_with_gateway_and_http_same_epoch():
    rows=make_rows()
    r=core.event_outcome(rows,(6,9))
    assert r["eligible"] is True
    assert r["recovery_gateway_index"]==2
    assert r["recovery_http_index"]==2
    assert r["lag_http_bins"]==0
    assert len(r["samples_pre"])==5 and len(r["samples_post"])==10


def test_http_can_lag_and_no_clamping_negative_values():
    later=core.event_outcome(make_rows(http_restarts=12),(6,9))
    assert later["lag_http_bins"]==2
    early=core.event_outcome(make_rows(http_restarts=10,gateway_restarts=12),(6,9))
    assert early["lag_http_bins"]==-2


def test_missing_http_or_gateway_is_censored_without_imputation():
    delayed=core.event_outcome(make_rows(http_restarts=25),(6,9))
    assert delayed["eligible"] is True
    assert delayed["http_right_censored"] is True
    assert delayed["lag_http_bins"] is None
    assert delayed["recovery_gateway_index"]==2
    rows=make_rows()
    rows[12]["epoch"]+=100
    assert core.event_outcome(rows,(6,9))["eligible"] is False


def test_missing_or_invalid_http_status_cannot_become_success():
    row=make_rows()[0]
    row["http_status"]=None
    assert core.http_success(row) is False
    row["http_status"]=503
    assert core.http_success(row) is False
    row["http_status"]=200
    row["http_ms"]=None
    assert core.http_success(row) is False
    row["http_ms"]=float("nan")
    assert core.http_success(row) is False
    row["http_ms"]=-7
    assert core.http_usable(row) is False
    row["http_ms"]=1001
    assert core.http_success(row) is True and core.http_usable(row) is False


def test_source_malformed_loss_or_epoch_or_timestamp_fails_closed():
    base=text_csv(make_rows())
    with pytest.raises(core.InvalidSource,match="PACKET_LOSS_CONFLICTS"):
        core.parse_original(base.replace("100.0,100.0","10.0,100.0",1),
                            enforce_publisher_census=False)
    with pytest.raises(core.InvalidSource,match="RAW_SOURCE_TIMESTAMP"):
        core.parse_original(base.replace("2026-01-01T00:00:30Z",
                             "2026-01-01T00:00:00Z",1),enforce_publisher_census=False)
    with pytest.raises(core.InvalidSource,match="RAW_PUBLISHER_RECORD_CENSUS"):
        core.parse_original(base,enforce_publisher_census=True)


def test_one_outage_does_not_pretend_to_be_all_four_events():
    a=core.evaluate(make_rows())
    assert a["four_original_events_required"] is False
    assert a["status"]=="RP_U008_SOURCE_OR_EVENT_CENSUS_INCOMPLETE"
    assert a["three_plus_row_eligible_events"]==1


def test_two_of_four_threshold_applies_to_all_not_one_selected_outage():
    starts=(6,35,64,93)
    size=125
    base=make_rows(samples=size,positions=tuple(
        z for start in starts for z in range(start,start+4)
    ))
    # Rebuild four outages as independent max runs, each with its own HTTP
    # postsource recovery, and exactly one delayed service recovery.
    for row in base:
        row["received"]=10
        row["loss_pct"]=0
        row["gateway_loss_pct"]=0
        row["gateway_rtt_ms"]=.2
        row["http_status"]=200
        row["http_ms"]=90.0
    for start in starts:
        for z in range(start,start+4):
            base[z]["received"]=0
            base[z]["loss_pct"]=100.0
            base[z]["gateway_loss_pct"]=100.0
            base[z]["gateway_rtt_ms"]=None
            base[z]["http_status"]=None
            base[z]["http_ms"]=None
    for z in (10,11):
        base[z]["http_status"]=None
        base[z]["http_ms"]=None
    one=core.evaluate(base)
    assert one["three_plus_row_eligible_events"]==4
    assert one["complete_first_hop_http_recovery_census"] is True
    assert one["gateway_and_http_positive_lag_count"]==1
    assert one["status"]=="RP_U008_NO_REPEATED_POSITIVE_HTTP_LAG_AT_SOURCE_RESOLUTION"
    for z in (39,40):
        base[z]["http_status"]=None
        base[z]["http_ms"]=None
    two=core.evaluate(base)
    assert two["gateway_and_http_positive_lag_count"]==2
    assert two["status"]=="RP_U008_TWO_OR_MORE_POSITIVE_HTTP_LAGS_OBSERVED"


def test_short_outages_are_reported_not_silently_selected():
    a=make_rows(positions=(6,7),samples=28)
    outcome=core.evaluate(a,require_four=False)
    assert outcome["three_plus_row_eligible_events"]==0
    assert outcome["excluded_short_runs"][0]["down_rows"]==2
