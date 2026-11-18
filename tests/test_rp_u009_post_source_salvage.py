"""RP-U009 P02 negative/positive parser gates with P01 strictness preserved."""
from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest

from experiments import rp_u009_metropt_core as core
from experiments import rp_u009_post_source_salvage as runner


def synthetic_reading(*,lps:str="1.0",pre_pressure:float=6.0,
                      post_pressure:float=8.0)->str:
    rows=["timestamp,Reservoirs,Motor_current,LPS"]
    for repair,_ in core.EXPECTED_EVENTS:
        m=core.date_from_source(repair)
        for side in ("before","after"):
            first=m-timedelta(hours=12) if side=="before" else m+timedelta(hours=3)
            for k in range(35):
                stamp=first+timedelta(minutes=10*k)
                pressure=pre_pressure if side=="before" else post_pressure
                rows.append(
                    f"{stamp:%Y-%m-%d %H:%M:%S},{pressure},7,{lps}"
                )
    return "\n".join([rows[0],*sorted(rows[1:])])+"\n"


def test_strict_p01_continues_to_reject_original_decimal_text():
    with pytest.raises(core.InvalidEvidence,match="LOW_PRESSURE_SWITCH_MUST_BE_BINARY"):
        core.original_csv_audit(StringIO(synthetic_reading()),expected_census=None)
    assert core.original_csv_audit(
        StringIO(synthetic_reading()),
        expected_census=None,
        allow_decimal_lps=True,
    )["all_four_fixed_windows"][0]["original_observation_count"]==35


def test_p02_accepts_only_numeric_decimal_binary_strings():
    for token in ("2.0","0.5","1.00","-0.0","NaN",""):
        with pytest.raises(core.InvalidEvidence,match="LOW_PRESSURE_SWITCH_MUST_BE_BINARY"):
            core.original_csv_audit(
                StringIO(synthetic_reading(lps=token)),
                expected_census=None,
                allow_decimal_lps=True,
            )


def test_post_source_result_can_be_positive_or_negative_but_not_retuned():
    pos=core.original_csv_audit(
        StringIO(synthetic_reading()),expected_census=None,
        allow_decimal_lps=True)
    assert core.evaluate_summary(pos)["status"]==(
        "RP_U009_BOTH_REPAIRS_SHOW_LOWER_LOW_PRESSURE_OCCUPANCY")
    neg=core.original_csv_audit(
        StringIO(synthetic_reading(pre_pressure=8,post_pressure=6)),
        expected_census=None,allow_decimal_lps=True)
    assert core.evaluate_summary(neg)["status"]==(
        "RP_U009_NO_TWO_EVENT_CONCORDANT_PRESSURE_IMPROVEMENT")


def test_immutable_invalid_p01_and_d01_are_verified_before_any_new_source():
    audit=runner.verify_previous_source_history()
    assert audit["status"]=="RP_U009_D01_BINARY_TEXT_ENCODING_ONLY"
    assert audit["all_source_lps_literal_token_counts"]=={
        "0.0":1511760,"1.0":5188
    }
    assert runner.P02_ADDENDUM_COMMIT=="764a07a5f7489491e6da05d17d15d6ecb5695af5"
