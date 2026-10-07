"""Fact Agent stub for Phase 2.

NOTE: Fact View generation will be implemented in Phase 3+.
This agent acts as a stub returning a placeholder message upon plan approval.
"""

from __future__ import annotations
from app.agents.base import BaseAgent


class FactAgentStub(BaseAgent):
    """Stub agent called upon Plan approval."""

    def __init__(self):
        super().__init__(name="FactAgent")

    async def execute_stub(self, fact_view_name: str) -> dict[str, str]:
        """Returns placeholder response indicating Fact View generation is Phase 3+."""
        safe_input = {"fact_view_name": fact_view_name}

        def _action():
            return {
                "status": "not_implemented",
                "message": f"Fact View generation for '{fact_view_name}' is scheduled for Phase 3. Plan has been approved and locked."
            }

        return await self.execute("FactViewStub", _action, safe_input)
