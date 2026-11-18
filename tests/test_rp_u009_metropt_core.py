"""RP-U009 original-source-free integrity, maintenance and falsification gates."""
from __future__ import annotations

from io import StringIO
from datetime import datetime,timedelta

import pytest

from experiments import rp_u009_metropt_core as c


def build_csv(*, offset_current=0, reverse=False, missing=False):
    lines=["timestamp,Reservoirs,Motor_current,LPS"]
    for maintenance,_ in c.EXPECTED_EVENTS:
        m=c.date_from_source(maintenance)
        for side in (-1,1):
            start=(m-timedelta(hours=12) if side==-1
                   else m+timedelta(hours=3))
            for k in range(35):
                t=start+timedelta(minutes=10*k)
                pressure=6.0 if side==-1 else (
                    6.0 if offset_current==0 else 8.0)
                lines.append(
                    f"{t:%Y-%m-%d %H:%M:%S},{pressure},7,{int(pressure<7)}"
                )
    if reverse:
        lines[2]=lines[1]
    if missing:
        lines[3]=lines[3].replace(",6.0,", ",,")
    return "\n".join([lines[0],*sorted(lines[1:])])+"\n" if not reverse else "\n".join(lines)+"\n"


def test_original_uci_url_exact_and_two_dates_unchanged():
    assert c.PROTOCOL_ONLY_COMMIT=="2c36bd9b84ac664798e544f24b3617c1f7b5a258"
    assert c.OFFICIAL_UCI_URL==(
        "https://archive.ics.uci.edu/static/public/791/"
        "metropt%2B3%2Bdataset.zip"
    )
    assert c.ORIGINAL_EXPECTED_ROWS==1_516_948
    assert c.MIN_WINDOW_ROWS==30
    assert c.MIN_WINDOW_HOUR_BUCKETS==6
    assert len(c.EXPECTED_EVENTS)==2
    assert [x[0] for x in c.EXPECTED_EVENTS]==[
        "2020-06-08 16:00:00","2020-07-16 00:00:00"
    ]


def test_input_source_order_and_event_window_mapping():
    w=c.fixed_windows()
    assert len(w)==4
    assert [x["side"] for x in w]==["before","after","before","after"]
    assert [(x["end_clock"]-x["begin_clock"]).total_seconds()/3600
            for x in w]==[22]*4
    assert c.NON_ELIGIBLE_PUBLIC_REPORTS[1].startswith("2020-05-29")


def test_toy_pressure_before_and_after_source_falsifies_positive():
    r=c.original_csv_audit(StringIO(build_csv(offset_current=0)),
                           expected_census=None)
    decision=c.evaluate_summary(r)
    assert decision["status"]=="RP_U009_NO_TWO_EVENT_CONCORDANT_PRESSURE_IMPROVEMENT"
    assert decision["improved_strict_event_count_of_two"]==0
    assert len(r["all_four_fixed_windows"])==4


def test_toy_pressure_opposite_direction_is_not_improvement():
    source=c.original_csv_audit(StringIO(build_csv(offset_current=1)),
                                expected_census=None)
    assert c.evaluate_summary(source)[
        "status"]=="RP_U009_BOTH_REPAIRS_SHOW_LOWER_LOW_PRESSURE_OCCUPANCY"
    for x in source["all_four_fixed_windows"]:
        x["fraction_reservoir_pressure_below_7bar"] = (
            0.0 if x["window_side"]=="before" else 1.0
        )
    assert c.evaluate_summary(source)[
        "status"]=="RP_U009_NO_TWO_EVENT_CONCORDANT_PRESSURE_IMPROVEMENT"


def test_missing_pressure_or_wrong_lps_is_rejected_without_imputation():
    with pytest.raises(c.InvalidEvidence,match="MISSING_OR_NOT_NUMERIC"):
        c.original_csv_audit(StringIO(build_csv(missing=True)),expected_census=None)
    a=build_csv().replace(",6.0,7,1",",6.0,7,3",1)
    with pytest.raises(c.InvalidEvidence,match="MUST_BE_BINARY"):
        c.original_csv_audit(StringIO(a),expected_census=None)


def test_malformed_clock_duplicates_are_rejected():
    rows=build_csv().splitlines()
    rows[2]=rows[1]
    with pytest.raises(c.InvalidEvidence,match="CLOCK_NOT_STRICTLY_INCREASING"):
        c.original_csv_audit(StringIO("\n".join(rows)+"\n"),expected_census=None)


def test_source_census_and_missing_hour_bucket_are_not_relabelled():
    with pytest.raises(c.InvalidEvidence,match="ROW_COUNT_CHANGED"):
        c.original_csv_audit(StringIO(build_csv()),expected_census=500)
    raw=build_csv().splitlines()
    filtered=[raw[0]]+[x for x in raw[1:] if not x.startswith("2020-06-09")]
    with pytest.raises(c.InvalidEvidence,match="FEWER_THAN_30|TOO_FEW_HOUR"):
        c.original_csv_audit(StringIO("\n".join(filtered)+"\n"),
                             expected_census=None)


def test_incomplete_or_relabelled_window_cannot_be_evaluated():
    source=c.original_csv_audit(StringIO(build_csv()),expected_census=None)
    bad={**source,"all_four_fixed_windows":source["all_four_fixed_windows"][:3]}
    with pytest.raises(c.InvalidEvidence,match="INCOMPLETE_PREDECLARED"):
        c.evaluate_summary(bad)
    wrong={**source,"all_four_fixed_windows":[dict(x) for x in source["all_four_fixed_windows"]]}
    wrong["all_four_fixed_windows"][0]["window_side"]="after"
    with pytest.raises(c.InvalidEvidence,match="PREPOST_WINDOW_CLOCK"):
        c.evaluate_summary(wrong)


def test_no_preregistered_maintenance_timestamp_before_reported_failure():
    for repair,end in c.EXPECTED_EVENTS:
        assert c.date_from_source(repair)>c.date_from_source(end)
