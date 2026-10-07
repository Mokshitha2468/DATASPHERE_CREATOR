"""API dependencies and in-memory state management."""

from __future__ import annotations
from app.domain.state import SharedState
from app.llm.client import get_llm_mode

# Global in-memory state for the active workspace session
_active_state = SharedState(llm_mode=get_llm_mode())


def get_current_state() -> SharedState:
    """Returns the active SharedState instance."""
    global _active_state
    _active_state.llm_mode = get_llm_mode()
    return _active_state


def set_current_state(state: SharedState) -> SharedState:
    """Updates the active SharedState instance."""
    global _active_state
    _active_state = state
    _active_state.llm_mode = get_llm_mode()
    return _active_state


def reset_state() -> SharedState:
    """Resets to fresh empty state."""
    global _active_state
    _active_state = SharedState(llm_mode=get_llm_mode())
    return _active_state
