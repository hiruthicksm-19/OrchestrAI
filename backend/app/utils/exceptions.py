"""
Custom exception hierarchy for DebateAI.
All domain-specific errors extend DebateAIError so callers can catch
at any level of granularity.
"""


class DebateAIError(Exception):
    """Base exception for all DebateAI errors."""


class ProviderError(DebateAIError):
    """Raised when an AI provider call fails."""


class ProviderAuthError(ProviderError):
    """Raised on authentication / API key issues."""


class ProviderRateLimitError(ProviderError):
    """Raised when the provider returns a rate-limit response."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider call exceeds the configured timeout."""


class AgentError(DebateAIError):
    """Raised when an agent cannot complete its task."""


class DebateEngineError(DebateAIError):
    """Raised for errors in the Debate Engine orchestration layer."""


class PromptError(DebateAIError):
    """Raised when a prompt template cannot be loaded or rendered."""


class ConfigError(DebateAIError):
    """Raised for missing or invalid configuration values."""


class RegistryError(DebateAIError):
    """Raised when an agent or provider is not found in the registry."""
