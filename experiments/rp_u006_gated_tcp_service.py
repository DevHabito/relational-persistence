"""RP-U006: a fresh single-host TCP worker with an explicit availability gate.

This is a software measurement appliance. A TCP socket/worker gate is not an
observed network-link restoration or an independent physical instrument.
The module performs no I/O at import and is not the existing RP-E009 server.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import time

DURATION_SECONDS = 0.012
MAX_BATCH = 24


class ServiceProtocolError(ValueError):
    pass


class GatedService:
    def __init__(self, events: Path) -> None:
        if events.exists():
            raise ServiceProtocolError("ORIGINAL_SERVICE_LOG_MUST_NOT_EXIST")
        events.parent.mkdir(parents=True, exist_ok=True)
        self.events = events
        self.events.touch(exist_ok=False)
        self.queue: asyncio.Queue[int] = asyncio.Queue()
        self.enabled = asyncio.Event()
        self.shutdown_event = asyncio.Event()
        self.accepted = 0
        self.completed = 0
        self.active: int | None = None
        self.enable_count = 0

    def record(self, kind: str, **fields: object) -> int:
        stamp = time.monotonic_ns()
        record = {"event": kind, "server_time_ns": stamp, **fields}
        with self.events.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        return stamp

    def snapshot(self) -> dict:
        return {
            "server_snapshot_ns": time.monotonic_ns(),
            "queued": self.queue.qsize(),
            "active": int(self.active is not None),
            "accepted": self.accepted,
            "completed": self.completed,
            "available": self.enabled.is_set(),
        }

    async def worker(self) -> None:
        while True:
            await self.enabled.wait()
            job = await self.queue.get()
            if self.active is not None:
                raise ServiceProtocolError("SECOND_WORKER_ACTIVE")
            self.active = job
            self.record("start", job=job)
            await asyncio.sleep(DURATION_SECONDS)
            self.completed += 1
            self.record("complete", job=job)
            self.active = None
            self.queue.task_done()

    async def command(self, message: dict) -> dict:
        op = message.get("op")
        if op == "ping":
            return {"ready": True}
        if op == "health":
            return self.snapshot()
        if op == "batch":
            n = message.get("count")
            if (type(n) is not int or not 0 <= n <= MAX_BATCH
                    or self.accepted or self.queue.qsize() or self.active is not None):
                raise ServiceProtocolError("INVALID_OR_REPEATED_FROZEN_BATCH")
            for j in range(1, n + 1):
                self.accepted += 1
                self.record("accept", job=j)
                self.queue.put_nowait(j)
            return {"accepted": n, "first_id": 1 if n else None,
                    "last_id": n if n else None}
        if op == "enable":
            if self.enable_count or self.shutdown_event.is_set():
                raise ServiceProtocolError("GATE_ALREADY_ENABLED_OR_SHUTDOWN")
            self.enable_count += 1
            stamp = self.record("enable", available=True)
            self.enabled.set()
            return {"enabled": True, "server_enable_ns": stamp}
        if op == "shutdown":
            if (not self.enabled.is_set() or self.queue.qsize()
                    or self.active is not None or self.accepted != self.completed):
                raise ServiceProtocolError("UNFINISHED_WORK_AT_SHUTDOWN")
            stamp = self.record("shutdown", accepted=self.accepted,
                                completed=self.completed)
            self.shutdown_event.set()
            return {"shutdown": True, "server_shutdown_ns": stamp}
        raise ServiceProtocolError("UNREGISTERED_TCP_OPERATION")


async def serve(port: int, events: Path) -> None:
    state = GatedService(events)

    async def handler(reader: asyncio.StreamReader,
                      writer: asyncio.StreamWriter) -> None:
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=3)
            if not data or len(data) > 4096:
                raise ServiceProtocolError("INVALID_OR_EXCESSIVE_TCP_FRAME")
            command = json.loads(data)
            if not isinstance(command, dict):
                raise ServiceProtocolError("TCP_MESSAGE_NOT_OBJECT")
            result = await state.command(command)
        except (ValueError, TypeError, asyncio.TimeoutError,
                UnicodeDecodeError) as exc:
            result = {"error": f"{type(exc).__name__}:{exc}"}
        writer.write((json.dumps(result, sort_keys=True) + "\n").encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    worker = asyncio.create_task(state.worker())
    try:
        server = await asyncio.start_server(handler, "127.0.0.1", port)
        async with server:
            await state.shutdown_event.wait()
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


def run_service(port: int, events_filename: str) -> None:
    asyncio.run(serve(port, Path(events_filename)))
