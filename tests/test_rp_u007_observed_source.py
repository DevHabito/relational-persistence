"""RP-U007 source runner: synthetic-only refusals, no original service executed."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from experiments import rp_u007_forecast_core as c
from experiments import rp_u007_gated_service as s
from experiments import rp_u007_observed_source as runner


def test_original_manifest_and_timing_are_declared_before_source():
    assert runner.PROTOCOL.as_posix()=="docs/preregistration/RP-U007-P01.md"
    assert runner.OUTPUT.as_posix()=="docs/results/RP-U007-P01-first-run"
    assert c.LANDMARK_NS==100_000_000
    assert c.FORECAST_DEADLINE_NS==125_000_000
    assert c.FUTURE_BATCH_OFFSET_NS==160_000_000
    assert runner.POLL_SECONDS==.012
    assert runner.DRAIN_DEADLINE==6.0


def test_file_writer_never_overwrites_original_source(tmp_path:Path):
    file=tmp_path/"a.json"
    runner.write_new(file,{"count":3})
    with pytest.raises(c.InvalidEvidence,match="SOURCE_FILE_EXISTS"):
        runner.write_new(file,{"count":4})
    assert runner.digest(file)!=""


def test_user_machine_cannot_claim_new_hosted_original_source(tmp_path,monkeypatch):
    monkeypatch.delenv("GITHUB_SHA",raising=False)
    monkeypatch.delenv("GITHUB_RUN_ID",raising=False)
    with pytest.raises(c.InvalidEvidence,match="HOSTED_SOURCE"):
        runner.run_first(tmp_path/"unperformed")
    assert not (tmp_path/"unperformed").exists()


def test_readonly_instrument_and_service_reject_bad_regime(tmp_path:Path):
    with pytest.raises(s.ServiceFailure,match="UNREGISTERED"):
        s.GatedVariableService(tmp_path/"events.jsonl","invalid")


def test_a_server_obeys_disable_and_streamed_batch_sequence(tmp_path:Path):
    async def scenario():
        state=s.GatedVariableService(tmp_path/"events.jsonl","standard")
        task=asyncio.create_task(state.worker())
        try:
            one=await state.command({"op":"batch","count":10})
            assert one["accepted_total"]==10
            await asyncio.sleep(.030)
            assert state.health()["completed"]==0
            assert state.health()["queued"]==10
            en=await state.command({"op":"enable"})
            assert en["enabled"]
            two=await state.command({"op":"batch","count":2})
            assert two["first_job_id"]==11 and two["last_job_id"]==12
            await asyncio.wait_for(state.waiting.join(),timeout=1.0)
            assert state.health()["completed"]==12
            closed=await state.command({"op":"shutdown"})
            assert closed["shutdown"] is True
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    asyncio.run(scenario())


def test_events_without_shutdown_are_not_an_original_measurement():
    rows=[{"event":"accept","server_time_ns":i,"job":i}
          for i in range(1,11)]
    with pytest.raises(c.InvalidEvidence,match="IDENTITY_OR_FIFO"):
        c.validate_events(rows,initial=10,calibration=False)
