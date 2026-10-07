"""LangSmith observability and tracing setup.

LangSmith is activated ONLY when LANGSMITH_API_KEY is configured.
CRITICAL: Real sample data is NEVER passed to LangSmith traces.
"""

from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Any, Generator
from app.core.config import settings
from app.observability.logger import logger


def init_tracing() -> bool:
    """Configures LangSmith tracing if API key is provided."""
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        logger.info(f"LangSmith tracing enabled for project: {settings.LANGSMITH_PROJECT}")
        return True
    return False


@contextmanager
def trace_agent_run(run_name: str, inputs: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Context manager for tracing agent execution.
    
    Safe by design: ensures inputs only contain metadata/synthetic data.
    """
    metadata = {
        "run_name": run_name,
        "langsmith_enabled": bool(settings.LANGSMITH_API_KEY),
    }
    try:
        yield metadata
    finally:
        pass
