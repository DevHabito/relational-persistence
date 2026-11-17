"""RP-U006 offline negative controls and timing gates; no original service trials."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from experiments import rp_u006_forecast_core as c
from experiments import rp_u006_gated_tcp_service as svc


def make_events(n: int, *, enabled_before_batch: bool = False) -> list[dict]:
    enable = {"event": "enable", "server_time_ns": 1 if enabled_before_batch else 1000}
    before = [{"event": "accept", "job": i, "server_time_ns": i * 10}
              for i in range(1, n+1)]
    after = [
        z for i in range(1, n+1) for z in (
            {"event": "start", "job": i, "server_time_ns": 2000+i*20},
            {"event": "complete", "job": i, "server_time_ns": 2001+i*20}
        )
    ]
    return ([enable] + before + after if enabled_before_batch
            else before + [enable] + after)


def test_declared_trial_order_monitor_and_outcome_gates():
    assert c.CALIBRATION_TASKS == 12
    assert c.DIAGNOSTIC_LOADS == (8,16,24,8,16,24)
    assert c.HOLDOUT_LOADS == (7,11,15,19,23,9,21,13)
    assert c.MIN_PAIR_GAP_NS == 15_000_000
    assert c.MAX_PAIR_GAP_NS == 120_000_000
    assert c.MONITOR_LATENCY_ALLOWANCE_SECONDS == .040
    assert c.PROTOCOL_ONLY_SHA == "b99e505d99d25bed57e2308029947407b2668777"


def test_calibration_uses_nine_intervals_for_jobs_three_through_twelve():
    events = make_events(12)
    interval = c.calibration_interval(events)
    assert interval == 20 / 1e9
    with pytest.raises(c.InvalidObservation, match="CALIBRATION_INCOMPLETE"):
        c.calibration_interval(events[:-1])


def test_independent_service_event_count_and_identity_safety():
    accepted = c.validate_service_events(make_events(8), 8, calibration=False)
    assert accepted["accepted"] == accepted["completed"] == 8
    events = make_events(8)
    events[-1]["job"] = 1
    with pytest.raises(c.InvalidObservation, match="IDENTITY"):
        c.validate_service_events(events, 8, calibration=False)


def test_unallowed_arrival_after_worker_enable_rejected():
    records = make_events(8)
    records[7]["server_time_ns"] = 1100
    with pytest.raises(c.InvalidObservation, match="LATE_ARRIVALS|NONMONOTONIC"):
        c.validate_service_events(records, 8, calibration=False)


def test_monitor_two_zeros_after_enable_require_time_and_conservation():
    enable_ns = 1_000_000_000
    pairs = []
    for i, pending in enumerate((3,2,1,0,0,0,0)):
        stamp = enable_ns + (i + 1)*20_000_000
        pairs.append({
            "observed_ns": stamp + 1_000_000,
            "server_snapshot_ns": stamp,
            "queued": pending, "active": 0,
            "accepted": 3, "completed": 3-pending,
        })
    assert c.recovery_elapsed(pairs, enable_ns, 3) == pytest.approx(.101)
    invalid = [x.copy() for x in pairs]
    invalid[4]["server_snapshot_ns"] = invalid[4]["observed_ns"] + 1
    with pytest.raises(c.InvalidObservation, match="CLOCK"):
        c.recovery_elapsed(invalid, enable_ns, 3)
    missing = [x.copy() for x in pairs]
    missing[4]["queued"] = 99
    with pytest.raises(c.InvalidObservation, match="CONSERVATION"):
        c.recovery_elapsed(missing, enable_ns, 3)
    long_gap = [x.copy() for x in pairs]
    for x in long_gap[2:]:
        x["observed_ns"] += 200_000_000
        x["server_snapshot_ns"] += 200_000_000
    with pytest.raises(c.InvalidObservation, match="GAP"):
        c.recovery_elapsed(long_gap, enable_ns, 3)


def test_forecasts_use_only_training_targets_and_measured_snapshot():
    f = c.frozen_forecasts([.14,.22,.32,.15,.23,.34], .012, 19)
    assert f["availability_only_seconds"] == pytest.approx(.225)
    assert f["outstanding_aware_seconds"] == pytest.approx(.268)
    with pytest.raises(c.InvalidObservation, match="SIX"):
        c.frozen_forecasts([.2], .012, 10)


def test_negative_original_outcome_when_fixed_forecast_hurts():
    original = {
        "original_trials_valid": True,
        "heldout": [{
            "requested_jobs": n, "recovery_seconds": .2,
            "predictions": {
                "availability_only_seconds": .2,
                "outstanding_aware_seconds": .04 + n*.012,
            },
        } for n in c.HOLDOUT_LOADS],
    }
    result = c.evaluate_original(original)
    assert result["status"] == "RP_U006_COMPLETE_NO_REGISTERED_GAIN"
    assert result["state_forecast_strict_wins_of_eight"] == 0


def test_positive_synthetic_gate_is_possible_but_not_automatically_assumed():
    original = {
        "original_trials_valid": True,
        "heldout": [{
            "requested_jobs": n, "recovery_seconds": .04 + .012*n,
            "predictions": {
                "availability_only_seconds": .25,
                "outstanding_aware_seconds": .04 + .012*n,
            },
        } for n in c.HOLDOUT_LOADS],
    }
    result = c.evaluate_original(original)
    assert result["status"] == "RP_U006_EXECUTABLE_STATE_FORECAST_GAIN_WITHIN_HOST"
    assert result["state_forecast_strict_wins_of_eight"] == 8


def test_cohort_order_invalidation_and_missing_source():
    original = {
        "original_trials_valid": True,
        "heldout": [{"requested_jobs": 7, "recovery_seconds": .1,
                     "predictions": {"availability_only_seconds": .2,
                                     "outstanding_aware_seconds": .2}}],
    }
    with pytest.raises(c.InvalidObservation, match="EIGHT"):
        c.evaluate_original(original)
    original["heldout"] *= 8
    with pytest.raises(c.InvalidObservation, match="ORDER"):
        c.evaluate_original(original)


def test_zero_job_sham_and_repeated_batch_prevented(tmp_path: Path):
    async def demonstrate():
        state = svc.GatedService(tmp_path / "events.jsonl")
        assert (await state.command({"op": "batch", "count": 0}))["accepted"] == 0
        enabled = await state.command({"op": "enable"})
        assert enabled["enabled"] is True
        assert (await state.command({"op": "health"}))["queued"] == 0
        with pytest.raises(svc.ServiceProtocolError, match="GATE_ALREADY"):
            await state.command({"op": "enable"})
        with pytest.raises(svc.ServiceProtocolError, match="INVALID_OR_REPEATED"):
            await state.command({"op": "batch", "count": -1)
    asyncio.run(demonstrate())


def test_service_never_completes_work_before_gate_is_enabled(tmp_path: Path):
    async def demonstrate():
        state = svc.GatedService(tmp_path / "events.jsonl")
        worker = asyncio.create_task(state.worker())
        try:
            await state.command({"op": "batch", "count": 2})
            await asyncio.sleep(.04)
            health = state.snapshot()
            assert health["accepted"] == 2
            assert health["completed"] == 0 and health["queued"] == 2
            await state.command({"op": "enable"})
            await asyncio.wait_for(state.queue.join(), timeout=1.0)
            assert state.snapshot()["completed"] == 2
        finally:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
    asyncio.run(demonstrate())
