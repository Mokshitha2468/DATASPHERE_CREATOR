"""API routes for inspecting SharedState."""

from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from app.api.deps import get_current_state, reset_state

router = APIRouter(prefix="/state", tags=["state"])


@router.get("")
async def get_state() -> dict[str, Any]:
    """Returns the complete current SharedState including llm_mode."""
    state = get_current_state()
    return state.model_dump()


@router.post("/reset")
async def reset_workspace_state() -> dict[str, Any]:
    """Resets the active workspace session."""
    state = reset_state()
    return state.model_dump()
