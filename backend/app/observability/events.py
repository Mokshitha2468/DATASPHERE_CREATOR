"""Event bus and Server-Sent Events (SSE) streaming for live agent logs."""

from __future__ import annotations
import asyncio
import json
import time
from typing import Any, AsyncGenerator


class EventBus:
    """In-memory event bus broadcasting agent lifecycle and log events."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self._history: list[dict[str, Any]] = []

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publishes an event to all active SSE subscribers."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **data,
        }
        self._history.append(event)
        # Keep last 500 events in memory
        if len(self._history) > 500:
            self._history.pop(0)

        # Broadcast to all connected queues
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def get_history(self) -> list[dict[str, Any]]:
        """Returns the recent event history."""
        return list(self._history)

    async def stream(self) -> AsyncGenerator[str, None]:
        """Subscribes to live events yielding SSE formatted strings."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        
        # Send initial connected message
        yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE log stream established'})}\n\n"
        
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            if queue in self._subscribers:
                self._subscribers.remove(queue)


event_bus = EventBus()
