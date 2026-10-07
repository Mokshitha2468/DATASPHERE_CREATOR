"""Application configuration and environment settings."""

from __future__ import annotations
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    
    # App info
    PROJECT_NAME: str = "SAP Datasphere Creator"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8005
    
    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # mock, gemini, openai, anthropic
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    # LangSmith Tracing
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "datasphere-creator"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_TRACING_V2: str = "false"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SAMPLE_DIR: Path = BASE_DIR / "app" / "samples"
    FRONTEND_DIR: Path = BASE_DIR.parent / "frontend"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @property
    def effective_api_key(self) -> str | None:
        """Determines the active API key across provider variables."""
        return (
            self.LLM_API_KEY 
            or self.GEMINI_API_KEY 
            or self.OPENAI_API_KEY 
            or self.ANTHROPIC_API_KEY
            or os.getenv("GOOGLE_API_KEY")
        )

    @property
    def is_mock_mode(self) -> bool:
        """Returns True if no valid API key is configured or provider is explicitly 'mock'."""
        if self.LLM_PROVIDER.lower() == "mock":
            return True
        return not bool(self.effective_api_key)


settings = Settings()
