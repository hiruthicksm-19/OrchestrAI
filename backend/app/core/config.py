"""
Production-Grade Configuration Management

This module provides centralized configuration for the entire DebateAI application.
It loads configuration from environment variables using Pydantic Settings.

Design Principles:
- Single source of truth for all configuration
- No hardcoded values outside this module
- Validation at startup, not runtime
- Sensible defaults where appropriate
- Fail fast on missing required values
- Support multiple environments (dev, staging, prod)

Usage:
    from app.core.config import settings
    
    # Access configuration
    print(settings.app.name)
    print(settings.database.url)
    print(settings.ai.default_provider)
    
    # All configuration is validated at import time
"""

from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file before initializing settings
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_ENV_FILE)


class ApplicationSettings(BaseSettings):
    """Application metadata and environment settings."""

    name: str = Field(default="DebateAI", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=True, description="Debug mode flag")


class ServerSettings(BaseSettings):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    url: Optional[str] = Field(
        default=None,
        validation_alias="DATABASE_URL",
        description="Database URL (postgresql+asyncpg://...)",
    )


class AIProviderSettings(BaseSettings):
    """AI Provider API keys."""

    groq_api_key: Optional[str] = Field(
        default=None, description="Groq API key"
    )
    mistral_api_key: Optional[str] = Field(
        default=None, description="Mistral API key"
    )
    cerebras_api_key: Optional[str] = Field(
        default=None, description="Cerebras API key"
    )
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Validate that at least one provider API key is configured
        api_keys = [
            self.groq_api_key,
            self.mistral_api_key,
            self.cerebras_api_key,
            self.openai_api_key,
        ]
        if not any(api_keys):
            raise ValueError(
                "At least one AI provider API key must be configured. "
                "Set GROQ_API_KEY, MISTRAL_API_KEY, CEREBRAS_API_KEY, or OPENAI_API_KEY."
            )


class DefaultAISettings(BaseSettings):
    """Default AI model and behavior settings."""

    provider: str = Field(default="groq", description="Default AI provider")
    model: str = Field(
        default="llama-3.3-70b-versatile", description="Default AI model"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=2048, ge=1, description="Default max tokens in response"
    )
    timeout: int = Field(
        default=60, ge=1, description="Default request timeout in seconds"
    )
    max_retries: int = Field(
        default=2, ge=0, le=10, description="Default max retry attempts"
    )


class DebateEngineSettings(BaseSettings):
    """Debate engine configuration."""

    max_rounds: int = Field(
        default=1, ge=1, le=10, description="Maximum debate rounds"
    )
    enable_parallel_execution: bool = Field(
        default=True,
        description="Enable parallel execution of agents where possible",
    )
    enable_streaming: bool = Field(
        default=False, description="Enable streaming responses (future feature)"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    format: str = Field(
        default="json", description="Log format (json or text)"
    )


class Settings(BaseSettings):
    """
    Master settings object combining all configuration categories.

    This is the single source of truth for all application configuration.
    All modules should import this and access configuration from here.

    Example:
        from app.core.config import settings
        
        settings.app.name           # "DebateAI"
        settings.app.version        # "2.0.0"
        settings.app.debug          # True
        settings.server.host        # "0.0.0.0"
        settings.server.port        # 8000
        settings.database.url       # None (optional)
        settings.ai_providers.groq_api_key  # API key
        settings.ai.default_provider        # "groq"
        settings.ai.default_model           # "llama-3.3-70b-versatile"
        settings.debate.max_rounds          # 1
        settings.logging.level              # "INFO"
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Nested settings
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ai_providers: AIProviderSettings = Field(default_factory=AIProviderSettings)
    ai: DefaultAISettings = Field(default_factory=DefaultAISettings)
    debate: DebateEngineSettings = Field(default_factory=DebateEngineSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def prompts_dir(self) -> Path:
        """Path to prompt templates directory."""
        return Path(__file__).resolve().parents[1] / "prompts"

    def __init__(self, **data):
        """Initialize settings with validation."""
        super().__init__(**data)
        self._validate_environment()

    def _validate_environment(self) -> None:
        """Validate configuration for current environment."""
        if self.app.environment == "production":
            if self.app.debug:
                raise ValueError(
                    "DEBUG must be False in production environment"
                )
            if self.server.host == "0.0.0.0":
                raise ValueError(
                    "SERVER_HOST should not be 0.0.0.0 in production"
                )
            if not self.database.url:
                raise ValueError(
                    "DATABASE_URL is required in production environment"
                )


# Singleton instance - import this everywhere
try:
    settings = Settings()
except ValidationError as e:
    print("❌ Configuration Error:")
    for error in e.errors():
        print(f"  • {error['loc'][0]}: {error['msg']}")
    raise SystemExit("Failed to load configuration. See errors above.")
