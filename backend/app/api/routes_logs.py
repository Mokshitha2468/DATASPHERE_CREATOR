"""API routes for live log querying and SSE streaming."""

from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_state
from app.observability.events import event_bus

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs() -> dict[str, Any]:
    """Returns the current trace logs and agent events history."""
    state = get_current_state()
    return {
        "logs": state.logs,
        "errors": state.errors,
        "events": event_bus.get_history(),
    }


@router.get("/stream")
async def stream_logs():
    """SSE streaming endpoint for real-time agent lifecycle and trace events."""
    return StreamingResponse(
        event_bus.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
