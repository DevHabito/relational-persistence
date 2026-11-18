"""U007 source-independent falsification gates; no original hosted trials."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from experiments import rp_u007_forecast_core as c
from experiments import rp_u007_gated_service as s


def test_three_mode_frozen_registration_and_twelve_ordered_holdouts():
    assert c.CALIBRATION_ORDER == ("fast","standard","slow")
    assert c.REGIMES == {
        "fast":(6,9,12),"standard":(8,12,16),"slow":(12,18,24)
    }
    assert c.CALIBRATION_TASKS == 18
    assert len(c.HOLDOUTS) == 12
    assert [p.initial_jobs for p in c.HOLDOUTS] == [
        14,10,18,22,10,22,10,22,18,18,14,14
    ]
    assert c.LANDMARK_NS == 100_000_000
    assert c.FORECAST_DEADLINE_NS == 125_000_000
    assert c.FUTURE_BATCH_OFFSET_NS == 160_000_000
    assert c.MIN_WINS == 9 and c.MIN_MAE_REDUCTION == .20


def test_calibration_has_thirteen_consecutive_gaps_for_ids_five_to_eighteen():
    events=[
        {"event":"complete","job":i,"server_time_ns":i*10_000_000}
        for i in range(1,19)
    ]
    assert c.calibrated_interval(events) == .01
    with pytest.raises(c.InvalidEvidence,match="COMPLETION_SEQUENCE"):
        c.calibrated_interval(events[:-1])
    events[10]["server_time_ns"]=events[9]["server_time_ns"]
    with pytest.raises(c.InvalidEvidence,match="THIRTEEN_POSITIVE"):
        c.calibrated_interval(events)


def make_source(initial:int,regime:str,calibration:bool=False):
    total=initial if calibration else initial+6
    events=[{"event":"enable","server_time_ns":10}]
    if calibration:
        events += [{"event":"accept","job":j,"server_time_ns":20+j}
                   for j in range(1,total+1)]
    else:
        events=[{"event":"accept","job":j,"server_time_ns":j}
                for j in range(1,initial+1)]+events
        events += [{"event":"accept","job":j,"server_time_ns":20+j}
                   for j in range(initial+1,total+1)]
    events += [e for j in range(1,total+1) for e in (
        {"event":"start","job":j,"server_time_ns":200+j*5},
        {"event":"complete","job":j,"server_time_ns":201+j*5})]
    events.append({"event":"shutdown","server_time_ns":300+total*5,
                   "completed":total})
    return events


def test_accept_start_complete_identity_is_exhaustively_verified():
    events=make_source(10,"fast")
    v=c.validate_events(events,initial=10,calibration=False)
    assert v["accepted_count"]==v["completed_count"]==16
    events[-2]["job"]=1
    with pytest.raises(c.InvalidEvidence,match="IDENTITY_OR_FIFO"):
        c.validate_events(events,initial=10,calibration=False)


def test_input_aware_baseline_and_state_formula_share_exact_calibration():
    x=c.original_forecasts(.012,accepted_at_landmark=18,observed_outstanding=14)
    assert x["input_inferred_backlog"]==10
    assert x["observed_landmark_backlog"]==14
    assert x["input_capacity_prediction_seconds"]==pytest.approx(.168)
    assert x["observed_state_prediction_seconds"]==pytest.approx(.216)
    assert x["sham_replacing_measured_with_inferred_seconds"]==x[
        "input_capacity_prediction_seconds"]
    with pytest.raises(c.InvalidEvidence,match="LANDMARK_FEATURE"):
        c.original_forecasts(float("nan"),accepted_at_landmark=20,
                             observed_outstanding=10)


def monitor_samples(enable:int=1_000_000_000,accepted:int=18):
    out=[]
    for i in range(16):
        observed=enable+(i+1)*12_000_000
        complete=min(accepted,i)
        out.append({"observed_ns":observed,"server_snapshot_ns":observed-400_000,
                    "accepted":accepted,"completed":complete,
                    "queued":accepted-complete,"active":0,
                    "available":True})
    return out


def test_latest_monitored_prelandmark_value_not_optimized_or_stale():
    enable=1_000_000_000
    samples=monitor_samples(enable)
    valid=c.select_landmark_sample(samples,enable_ns=enable,expected_accepted=18)
    assert valid["observed_ns"]==enable+96_000_000
    with pytest.raises(c.InvalidEvidence,match="STATE_OR_ACCEPTED"):
        c.select_landmark_sample(samples,enable_ns=enable,expected_accepted=19)
    old=[s for s in samples if s["observed_ns"]<=enable+60_000_000]
    with pytest.raises(c.InvalidEvidence,match="STALE"):
        c.select_landmark_sample(old,enable_ns=enable,expected_accepted=18)


def test_monitor_conservation_and_two_late_zero_samples():
    enable=1_000_000_000
    sample=monitor_samples(enable,accepted=6)
    sample.append({
        "observed_ns":enable+204_000_000,
        "server_snapshot_ns":enable+203_600_000,
        "accepted":6,"completed":6,"queued":0,"active":0,"available":True
    })
    # A post-final pair after 160ms is allowed only if there is followup.
    c.validate_samples(sample,total=6,enable_ns=enable)
    with pytest.raises(c.InvalidEvidence,match="FOLLOWUP"):
        c.measured_recovery(sample,landmark_ns=enable+100_000_000,
                            final_batch_accept_ns=enable+160_000_000)
    bad=[x.copy() for x in sample]
    bad[2]["queued"]+=1
    with pytest.raises(c.InvalidEvidence,match="CONSERVATION"):
        c.validate_samples(bad,total=6,enable_ns=enable)


def test_complete_negative_result_when_state_fails_to_add_information():
    trials=[]
    for p in c.HOLDOUTS:
        trials.append({"regime":p.regime,"initial_jobs":p.initial_jobs,
            "valid_original_trial":True,
            "measured_recovery_from_landmark_seconds":.3,
            "predictions":{"input_capacity_prediction_seconds":.3,
                           "observed_state_prediction_seconds":.5,
                           "sham_replacing_measured_with_inferred_seconds":.3}})
    source={"status":"RP_U007_SOURCE_READY_FOR_EVALUATION",
            "original_sources_all_valid":True,
            "calibration":[{"regime":r} for r in c.CALIBRATION_ORDER],
            "holdouts":trials}
    outcome=c.evaluate_original(source)
    assert outcome["status"]=="RP_U007_COMPLETE_NO_CONFIRMED_INCREMENT"
    assert outcome["strict_state_wins"]==0
    bad=source.copy()
    bad["holdouts"]=trials[:-1]
    with pytest.raises(c.InvalidEvidence,match="TWELVE"):
        c.evaluate_original(bad)


def test_positive_synthetic_gate_does_not_fix_source_results():
    trials=[]
    for p in c.HOLDOUTS:
        trials.append({"regime":p.regime,"initial_jobs":p.initial_jobs,
            "valid_original_trial":True,
            "measured_recovery_from_landmark_seconds":.25,
            "predictions":{"input_capacity_prediction_seconds":.4,
                           "observed_state_prediction_seconds":.25,
                           "sham_replacing_measured_with_inferred_seconds":.4}})
    source={"status":"RP_U007_SOURCE_READY_FOR_EVALUATION",
            "original_sources_all_valid":True,
            "calibration":[{"regime":r} for r in c.CALIBRATION_ORDER],
            "holdouts":trials}
    assert c.evaluate_original(source)["status"]==(
        "RP_U007_INCREMENTAL_LIVE_STATE_GAIN_WITHIN_HOST")


def test_service_refuses_repeated_enable_and_wrong_batches(tmp_path:Path):
    async def check():
        state=s.GatedVariableService(tmp_path/"service.jsonl","fast")
        await state.command({"op":"batch","count":10})
        assert state.health()["queued"]==10
        assert state.health()["completed"]==0
        await state.command({"op":"enable"})
        with pytest.raises(s.ServiceFailure,match="ALREADY"):
            await state.command({"op":"enable"})
        with pytest.raises(s.ServiceFailure,match="INVALID_BATCH"):
            await state.command({"op":"batch","count":40})
        with pytest.raises(s.ServiceFailure,match="SHUTDOWN_REQUIRES"):
            await state.command({"op":"shutdown"})
    asyncio.run(check())
