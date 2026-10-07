"""LLM client factory supporting Real LLM providers and Offline Mock mode."""

from __future__ import annotations
import os
from typing import Any
from app.core.config import settings
from app.observability.logger import logger


def get_llm_mode() -> str:
    """Returns 'REAL' if a valid provider key is set, else 'MOCK'."""
    return "MOCK" if settings.is_mock_mode else "REAL"


def get_llm() -> Any:
    """Returns initialized LangChain LLM instance or None in Mock mode."""
    if settings.is_mock_mode:
        logger.info("Using offline MOCK LLM mode.")
        return None

    api_key = settings.effective_api_key
    provider = settings.LLM_PROVIDER.lower()
    model_name = settings.LLM_MODEL

    try:
        if "gemini" in provider or "google" in provider:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.1)
        elif "openai" in provider:
            # If langchain_openai available
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.1)
            except ImportError:
                pass
    except Exception as e:
        logger.warning(f"Failed to initialize real LLM provider '{provider}': {e}. Falling back to MOCK mode.")
        return None

    return None
