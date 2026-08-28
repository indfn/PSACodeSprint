"""SSE broadcaster with replay buffer (Phase 7.1, also used by Phase 6).

Singleton `broadcaster` is imported by agent nodes to publish events.
Buffers events even before GET /agent/stream/{run_id} connects, then replays
them on stream().

Event types: agent_thinking, tool_call, tool_result, hitl_card, escalation,
trace_entry, confidence_update, deviation, notification, heartbeat
"""
from __future__ import annotations

import asyncio
import collections
import json
import time
from typing import Any, AsyncIterator


class SSEBroadcaster:
    def __init__(self, max_buffer: int = 100):
        self.queues: dict[str, asyncio.Queue] = {}
        self.buffers: dict[str, collections.deque] = {}
        self.max_buffer = max_buffer
        self._event_counter: dict[str, int] = {}

    async def publish(self, run_id: str, event_type: str, data: Any) -> None:
        """Publish an event to run_id.

        Buffers even if no subscriber yet. If a queue exists, also pushes live.
        """
        if not run_id:
            return
        buf = self.buffers.setdefault(run_id, collections.deque(maxlen=self.max_buffer))
        idx = self._event_counter.get(run_id, 0) + 1
        self._event_counter[run_id] = idx
        envelope = {
            "id": str(idx),
            "event": event_type,
            "run_id": run_id,
            "timestamp": time.time(),
            "data": data,
        }
        buf.append(envelope)
        q = self.queues.get(run_id)
        if q is not None:
            try:
                await q.put(envelope)
            except Exception:
                pass

    def _format_sse(self, envelope: dict[str, Any]) -> str:
        data_json = json.dumps(envelope["data"], default=str)
        return f"id: {envelope['id']}\nevent: {envelope['event']}\ndata: {data_json}\n\n"

    async def stream(
        self,
        run_id: str,
        last_event_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield SSE-formatted strings: first replay buffered events, then live."""
        # Ensure structures exist
        buf = self.buffers.setdefault(run_id, collections.deque(maxlen=self.max_buffer))
        q = self.queues.setdefault(run_id, asyncio.Queue())

        # Replay buffered events (optionally from Last-Event-ID)
        start_idx = 0
        if last_event_id:
            try:
                start_idx = int(last_event_id)
            except Exception:
                start_idx = 0
        for env in list(buf):
            try:
                if int(env["id"]) > start_idx:
                    yield self._format_sse(env)
            except Exception:
                yield self._format_sse(env)

        # Live stream
        while True:
            try:
                env = await asyncio.wait_for(q.get(), timeout=15.0)
                yield self._format_sse(env)
            except asyncio.TimeoutError:
                # heartbeat
                yield ": heartbeat\n\n"
            except asyncio.CancelledError:
                break

    def get_buffered(self, run_id: str) -> list[dict[str, Any]]:
        return list(self.buffers.get(run_id, []))

    def clear(self, run_id: str) -> None:
        self.buffers.pop(run_id, None)
        self.queues.pop(run_id, None)
        self._event_counter.pop(run_id, None)


# Singleton — nodes import `from app.agent.sse import broadcaster`
broadcaster = SSEBroadcaster()
