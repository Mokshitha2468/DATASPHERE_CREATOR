"""Base Agent wrapper providing structured logging, timing, and SSE event streaming."""

from __future__ import annotations
import time
from typing import Any, Callable
from app.observability.events import event_bus
from app.observability.logger import logger
from app.observability.tracing import trace_agent_run


class BaseAgent:
    """Base class for pipeline agents with integrated telemetry."""

    def __init__(self, name: str):
        self.name = name

    async def execute(
        self, 
        step: str, 
        action: Callable[[], Any], 
        safe_input_summary: dict[str, Any]
    ) -> Any:
        """Executes an agent action, measuring duration and publishing SSE events.
        
        CRITICAL: safe_input_summary must NEVER contain real sample rows.
        """
        start_time = time.time()
        logger.info(f"[{self.name}] Starting step '{step}'...")
        
        event_bus.publish("agent_start", {
            "agent": self.name,
            "step": step,
            "input": safe_input_summary,
            "status": "running",
        })

        with trace_agent_run(self.name, safe_input_summary):
            try:
                result = await action() if asyncio_is_coroutine_function(action) else action()
                duration_ms = round((time.time() - start_time) * 1000, 2)
                
                output_summary = result if isinstance(result, dict) else (
                    result.model_dump() if hasattr(result, "model_dump") else str(result)
                )

                logger.info(f"[{self.name}] Step '{step}' completed in {duration_ms}ms.")
                event_bus.publish("agent_output", {
                    "agent": self.name,
                    "step": step,
                    "output": output_summary,
                    "duration_ms": duration_ms,
                    "status": "completed",
                })
                return result
            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                err_msg = str(e)
                logger.error(f"[{self.name}] Step '{step}' failed: {err_msg}", exc_info=True)
                event_bus.publish("agent_error", {
                    "agent": self.name,
                    "step": step,
                    "error": err_msg,
                    "duration_ms": duration_ms,
                    "status": "failed",
                })
                raise


def asyncio_is_coroutine_function(func: Any) -> bool:
    import inspect
    return inspect.iscoroutinefunction(func)
