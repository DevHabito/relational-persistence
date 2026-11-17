"""Offline source-role tests for RP-U006; no 15-trial original run."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from experiments import rp_u006_observed_recovery as runner
from experiments import rp_u006_forecast_core as core
from experiments import rp_u006_gated_tcp_service as svc


def test_original_frozen_sources_are_declared_and_first_output_never_replaced(tmp_path):
    assert runner.PROTOCOL_PATH.as_posix() == "docs/preregistration/RP-U006-P01.md"
    assert core.CALIBRATION_CORRECTION_SHA == (
        "376eb4de39990d22112f80606a2fbe1d765e1163"
    )
    data = tmp_path / "once.json"
    runner.write_new(data, {"x": 2})
    with pytest.raises(core.InvalidObservation, match="MUST_NOT_BE_REPLACED"):
        runner.write_new(data, {"x": 3})
    assert runner.sha(data) != ""


def test_no_source_without_hosted_run_identifiers(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.delenv("GITHUB_RUN_ID", raising=False)
    with pytest.raises(core.InvalidObservation, match="HOSTED_WORKFLOW"):
        runner.run_original(tmp_path / "fresh")
    assert not (tmp_path / "fresh" / "summary.json").exists()


def test_future_monitor_unfinished_job_state_not_falsely_recovered():
    base = 1_000_000_000
    sample = []
    for i in range(6):
        t = base + (i+1)*20_000_000
        sample.append({"observed_ns": t+1_000_000,
                       "server_snapshot_ns": t,
                       "queued": 1, "active": 0,
                       "accepted": 4, "completed": 3})
    with pytest.raises(core.InvalidObservation, match="NOT_OBSERVED"):
        core.recovery_elapsed(sample, base, 4)


def test_no_original_experiment_during_import_or_unit_testing():
    assert svc.MAX_BATCH == 24
    assert svc.DURATION_SECONDS == 0.012
    assert runner.DRAIN_DEADLINE_SECONDS == 6
    assert runner.FOLLOWUP_SECONDS == .15
    assert runner.POST_BATCH_MONITOR_SECONDS >= .06


def test_service_rejects_duplicate_submission_and_shutdown_with_work(tmp_path):
    async def scenario():
        state = svc.GatedService(tmp_path / "events.jsonl")
        assert (await state.command({"op": "batch", "count": 4}))["accepted"] == 4
        with pytest.raises(svc.ServiceProtocolError, match="REPEATED"):
            await state.command({"op": "batch", "count": 1})
        with pytest.raises(svc.ServiceProtocolError, match="UNFINISHED"):
            await state.command({"op": "shutdown"})
        assert state.snapshot()["queued"] == 4
        with pytest.raises(svc.ServiceProtocolError, match="UNREGISTERED"):
            await state.command({"op": "forged"})
    asyncio.run(scenario())
