"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google Cloud / Vertex AI
    google_cloud_project: str = ""
    google_genai_use_vertexai: bool = True
    vertexai_location: str = "us-central1"
    google_api_key: str = ""  # For direct Gemini API (alternative to Vertex)

    # LLM Configuration
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 1.0  # Gemini 3.0+ requires 1.0

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # LangSmith Tracing (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "servicedesk-agent"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def use_vertex_ai(self) -> bool:
        """Check if should use Vertex AI instead of direct API."""
        return self.google_genai_use_vertexai and bool(self.google_cloud_project)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
