"""RP-U007 fresh TCP service with a gated FIFO worker and variable durations.

The mode is disclosed to both forecasters, but individual per-job durations
are selected independently inside this service after acceptance. OS timing
and random draws are not assumed reproducible, only the original source log.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import secrets
import time

from experiments.rp_u007_forecast_core import REGIMES

MAX_TOTAL_TASKS = 28


class ServiceFailure(ValueError):
    pass


class GatedVariableService:
    def __init__(self, events: Path, regime: str) -> None:
        if regime not in REGIMES:
            raise ServiceFailure("UNREGISTERED_DURATION_REGIME")
        if events.exists():
            raise ServiceFailure("ORIGINAL_SERVICE_EVENTS_EXIST")
        events.parent.mkdir(parents=True, exist_ok=True)
        events.touch(exist_ok=False)
        self.path=events
        self.regime=regime
        self.available=asyncio.Event()
        self.stop=asyncio.Event()
        self.waiting:asyncio.Queue[int]=asyncio.Queue()
        self.active:int|None=None
        self.accepted=0
        self.completed=0
        self.enable_count=0

    def record(self, event: str, **data: object) -> int:
        stamp=time.monotonic_ns()
        with self.path.open("a",encoding="utf-8") as out:
            out.write(json.dumps({"event":event,"server_time_ns":stamp,**data},
                                 sort_keys=True)+"\n")
        return stamp

    def health(self) -> dict:
        return {"server_snapshot_ns":time.monotonic_ns(),
                "accepted":self.accepted,
                "completed":self.completed,
                "queued":self.waiting.qsize(),
                "active":int(self.active is not None),
                "available":self.available.is_set()}

    async def worker(self) -> None:
        while True:
            await self.available.wait()
            job=await self.waiting.get()
            if self.active is not None:
                raise ServiceFailure("CONCURRENT_SINGLE_WORKER_VIOLATION")
            self.active=job
            nominal_ms=secrets.choice(REGIMES[self.regime])
            self.record("start",job=job,requested_ms=nominal_ms)
            await asyncio.sleep(nominal_ms/1000)
            self.completed+=1
            self.record("complete",job=job)
            self.active=None
            self.waiting.task_done()

    async def command(self, request: dict) -> dict:
        operation=request.get("op")
        if operation=="ping":
            return {"ready":True}
        if operation=="health":
            return self.health()
        if operation=="enable":
            if self.enable_count:
                raise ServiceFailure("SERVICE_ALREADY_ENABLED")
            self.enable_count+=1
            stamp=self.record("enable",available=True,regime=self.regime)
            self.available.set()
            return {"enabled":True,"server_enable_ns":stamp}
        if operation=="batch":
            count=request.get("count")
            if (type(count) is not int or not 1 <= count <= MAX_TOTAL_TASKS
                    or self.accepted+count > MAX_TOTAL_TASKS):
                raise ServiceFailure("INVALID_BATCH_COUNT_OR_TOTAL_LIMIT")
            first=self.accepted+1
            for j in range(first,first+count):
                self.accepted+=1
                self.record("accept",job=j)
                self.waiting.put_nowait(j)
            return {"accepted_this_batch":count,
                    "accepted_total":self.accepted,
                    "first_job_id":first,
                    "last_job_id":self.accepted,
                    "server_last_accept_ns":time.monotonic_ns()}
        if operation=="shutdown":
            if (not self.available.is_set() or self.waiting.qsize()
                    or self.active is not None or self.accepted!=self.completed):
                raise ServiceFailure("SHUTDOWN_REQUIRES_COMPLETED_SOURCE")
            self.record("shutdown",completed=self.completed)
            self.stop.set()
            return {"shutdown":True}
        raise ServiceFailure("UNREGISTERED_OPERATION")


async def serve(port: int, event_path: Path, regime: str) -> None:
    state=GatedVariableService(event_path,regime)

    async def handler(reader:asyncio.StreamReader,
                      writer:asyncio.StreamWriter) -> None:
        try:
            raw=await asyncio.wait_for(reader.readline(),timeout=3)
            if not raw or len(raw)>4096:
                raise ServiceFailure("INVALID_TCP_MESSAGE_LENGTH")
            request=json.loads(raw)
            if not isinstance(request,dict):
                raise ServiceFailure("TCP_COMMAND_MUST_BE_OBJECT")
            response=await state.command(request)
        except (ValueError,TypeError,asyncio.TimeoutError) as exc:
            response={"error":f"{type(exc).__name__}:{str(exc)[:125]}"}
        writer.write((json.dumps(response,sort_keys=True)+"\n").encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    task=asyncio.create_task(state.worker())
    try:
        server=await asyncio.start_server(handler,host="127.0.0.1",port=port)
        async with server:
            await state.stop.wait()
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def run_service(port:int,path:str,regime:str) -> None:
    asyncio.run(serve(port,Path(path),regime))
