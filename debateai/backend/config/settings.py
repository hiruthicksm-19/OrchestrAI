"""
Application-level settings loaded from environment variables / .env file.

Every configurable value lives here.  The rest of the codebase imports
from this module — never from os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from backend.utils.exceptions import ConfigError

# Resolve .env relative to the project root (two levels above this file).
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _require(key: str) -> str:
    """Return the value of *key* or raise ConfigError if it is missing."""
    value = os.getenv(key)
    if not value:
        raise ConfigError(
            f"Required environment variable '{key}' is not set. "
            f"Add it to your .env file or export it before running."
        )
    return value


class DebateSettings(BaseModel):
    """Tunable parameters for the Debate Engine."""

    rounds: int = Field(default=1, ge=1, le=10, description="Number of debate rounds")
    timeout_seconds: int = Field(default=60, ge=5, description="Per-call provider timeout")
    retry_count: int = Field(default=2, ge=0, description="Retry attempts on transient errors")


class Settings(BaseModel):
    """Top-level application settings."""

    # Provider API keys — loaded lazily so tests can patch env vars.
    groq_api_key: str = Field(default_factory=lambda: _require("GROQ_API_KEY"))
    mistral_api_key: str = Field(default_factory=lambda: _require("MISTRAL_API_KEY"))
    cerebras_api_key: str = Field(default_factory=lambda: _require("CEREBRAS_API_KEY"))
    openai_api_key: str = Field(default_factory=lambda: _require("OPENAI_API_KEY"))

    debate: DebateSettings = Field(default_factory=DebateSettings)

    # Prompt templates directory (relative to this file's package root).
    prompts_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "prompts"
    )

    model_config = {"arbitrary_types_allowed": True}


# Module-level singleton — import this everywhere.
settings = Settings()
