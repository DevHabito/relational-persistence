"""Independent executable RP-E009 TCP service, not the legacy HTTP queue.

Single asyncio event loop, explicit asyncio.Queue, one measured worker,
and JSON-lines commands over localhost TCP. This is software timing, not
physical instrument independence or a formal model of OS scheduling.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

BASE_DURATIONS_MS = (8, 12, 16)


class MeasuredQueue:
    def __init__(self, events_path: Path) -> None:
        self.events_path = events_path
        self.waiting: asyncio.Queue[tuple[int, str, int]] = asyncio.Queue()
        self.phase = "calibration"
        self.speed = 1
        self.accepted = 0
        self.completed = 0
        self.active: int | None = None

    def record(self, kind: str, **details: object) -> int:
        timestamp = time.monotonic_ns()
        event = {"event": kind, "time_ns": timestamp,
                 "phase": self.phase, **details}
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        return timestamp

    async def worker(self) -> None:
        while True:
            ident, phase, duration = await self.waiting.get()
            if self.active is not None:
                raise RuntimeError("More than one worker active")
            self.active = ident
            self.record("start", job=ident)
            await asyncio.sleep(duration / (self.speed * 1000))
            self.record("complete", job=ident)
            self.completed += 1
            self.active = None
            self.waiting.task_done()

    async def respond(self, message: dict) -> dict:
        operation = message.get("op")
        if operation == "health":
            stamp = time.monotonic_ns()
            return {
                "server_snapshot_ns": stamp,
                "queued": self.waiting.qsize(),
                "active": int(self.active is not None),
                "accepted": self.accepted,
                "completed": self.completed,
                "phase": self.phase,
            }
        if operation == "enqueue":
            ident = self.accepted + 1
            self.accepted = ident
            nominal = BASE_DURATIONS_MS[(ident - 1) % len(BASE_DURATIONS_MS)]
            timestamp = self.record("accept", job=ident,
                                    nominal_prechange_ms=nominal)
            self.waiting.put_nowait((ident, self.phase, nominal))
            return {"accepted": True, "job": ident, "service_accepted_ns": timestamp}
        if operation == "reset":
            if self.phase != "calibration" or self.active is not None or (
                self.waiting.qsize() or self.accepted != self.completed
            ):
                raise ValueError("Cannot reset a nonidle calibration")
            stamp = self.record("reset", calibrated_tasks=self.completed)
            self.phase = "experiment"
            self.accepted = self.completed = 0
            return {"reset": True, "server_reset_ns": stamp}
        if operation == "accelerate":
            if self.phase != "experiment" or self.speed != 1 or (
                self.active is not None or self.waiting.qsize()
            ):
                raise ValueError("Action cannot be repeated or applied to busy worker")
            self.speed = 2
            stamp = self.record("accelerate", speed_factor=2)
            return {"changed": True, "service_applied_ns": stamp}
        if operation == "ping":
            return {"ready": True}
        raise ValueError("Unregistered TCP operation")


async def serve(port: int, event_path: Path) -> None:
    state = MeasuredQueue(event_path)

    async def handle(reader: asyncio.StreamReader,
                     writer: asyncio.StreamWriter) -> None:
        try:
            raw = await asyncio.wait_for(reader.readline(), 2.0)
            message = json.loads(raw)
            if not isinstance(message, dict):
                raise ValueError("Command must be an object")
            response = await state.respond(message)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError,
                asyncio.TimeoutError) as exc:
            response = {"error": f"{type(exc).__name__}: {exc}"}
        writer.write(json.dumps(response, sort_keys=True).encode() + b"\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    worker_task = asyncio.create_task(state.worker())
    try:
        server = await asyncio.start_server(handle, host="127.0.0.1", port=port)
        async with server:
            await server.serve_forever()
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


def run_server(port: int, log_path: str) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError("Original event log already exists")
    path.touch()
    asyncio.run(serve(port, path))
