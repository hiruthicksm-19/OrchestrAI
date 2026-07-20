"""
Agent Registry — the single source of truth for agent configurations.

Design principles:
  - The Debate Engine requests an agent by role only.
  - The registry hides all provider, model, and parameter details.
  - Configuration is immutable (frozen dataclasses).
  - All fields are validated at construction time.
  - Adding a new provider or model requires only a change here.

Lookup behaviour:
  - registry.get(role)          → returns the highest-priority enabled agent
                                  for that role (primary public API).
  - registry.get_by_name(name)  → returns a specific named configuration.
  - registry.all_roles()        → returns all unique role names.
  - registry.all_configs()      → returns every registered AgentConfig.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.utils.exceptions import ConfigError, RegistryError
from app.utils.logger import get_logger
from app.core.config import settings
from app.core import constants

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Provider Capabilities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderCapabilities:
    """
    Declares what a provider supports.

    These are configuration flags only — no logic is implemented here.
    Higher layers (future streaming handler, tool-call dispatcher) will
    read these to decide what they can do with a given provider.

    Attributes
    ----------
    supports_streaming:
        Provider can stream tokens incrementally.
    supports_tools:
        Provider supports function / tool calling.
    supports_vision:
        Provider accepts image inputs.
    supports_reasoning:
        Provider has a dedicated reasoning / thinking mode.
    """

    supports_streaming: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    supports_reasoning: bool = False


# ---------------------------------------------------------------------------
# AgentConfig
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AgentConfig:
    """
    Immutable configuration record for a single agent instance.

    Every value that the Debate Engine, providers, or agents need to know
    about an agent lives here.  Nothing is hardcoded elsewhere.

    Attributes
    ----------
    name:
        Unique identifier for this configuration entry.
        Allows multiple implementations of the same role.
        Examples: ``"research_agent"``, ``"research_agent_v2"``.
    role:
        Logical role name used for agent class dispatch and
        debate-engine lookups.
        Examples: ``"research"``, ``"critical"``, ``"consensus"``.
    provider:
        Provider identifier string.
        Examples: ``"groq"``, ``"mistral"``, ``"cerebras"``, ``"openai"``.
    model:
        Model identifier understood by the chosen provider.
        Examples: ``"llama-3.3-70b-versatile"``, ``"mistral-large-latest"``.
    system_prompt_key:
        Key passed to PromptManager.get_system() and
        PromptManager.render_strategy().
    temperature:
        Sampling temperature. Must be in [0.0, 2.0].
    max_tokens:
        Maximum tokens in the provider response. Must be >= 1.
    top_p:
        Nucleus sampling probability. Must be in (0.0, 1.0].
        Set to 1.0 to disable.
    timeout:
        Per-request timeout in seconds for this agent's provider calls.
        Overrides the global settings timeout when provided.
        Must be >= 1.
    retry_count:
        Number of retry attempts on transient provider errors.
        Must be in [0, 10].
    enabled:
        When False the agent remains in the registry but is never
        returned by get().  Use to stage new agents without activating them.
    priority:
        Lower number = higher priority.  When multiple agents share the
        same role, get() returns the one with the lowest priority number.
        Must be >= 1.
    fallback_provider:
        Provider name to use if the primary provider fails.
        Configuration only — fallback execution is not yet implemented.
    fallback_model:
        Model name to use with the fallback provider.
        Configuration only — fallback execution is not yet implemented.
    capabilities:
        Declares what the backing provider supports.
        Read by future streaming / tool-call layers.
    metadata:
        Arbitrary key-value store for annotations.
        Examples: version, owner, description, experiment tags.
    """

    # --- Identity (required) ---
    name: str
    role: str
    provider: str
    model: str
    system_prompt_key: str

    # --- Sampling parameters ---
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0

    # --- Reliability parameters ---
    timeout: int = 60
    retry_count: int = 2

    # --- Registry management ---
    enabled: bool = True
    priority: int = 1

    # --- Fallback configuration (future use) ---
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None

    # --- Provider capability flags ---
    capabilities: ProviderCapabilities = field(
        default_factory=ProviderCapabilities
    )

    # --- Arbitrary annotations ---
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Validate all fields at construction time."""
        errors: List[str] = []

        if not self.name or not self.name.strip():
            errors.append("'name' must be a non-empty string.")

        if not self.role or not self.role.strip():
            errors.append("'role' must be a non-empty string.")

        if not self.provider or not self.provider.strip():
            errors.append("'provider' must be a non-empty string.")

        if not self.model or not self.model.strip():
            errors.append("'model' must be a non-empty string.")

        if not (0.0 <= self.temperature <= 2.0):
            errors.append(
                f"'temperature' must be in [0.0, 2.0], got {self.temperature}."
            )

        if self.max_tokens < 1:
            errors.append(
                f"'max_tokens' must be >= 1, got {self.max_tokens}."
            )

        if not (0.0 < self.top_p <= 1.0):
            errors.append(
                f"'top_p' must be in (0.0, 1.0], got {self.top_p}."
            )

        if self.timeout < 1:
            errors.append(
                f"'timeout' must be >= 1 second, got {self.timeout}."
            )

        if not (0 <= self.retry_count <= 10):
            errors.append(
                f"'retry_count' must be in [0, 10], got {self.retry_count}."
            )

        if self.priority < 1:
            errors.append(
                f"'priority' must be >= 1, got {self.priority}."
            )

        if self.fallback_provider is not None and not self.fallback_provider.strip():
            errors.append(
                "'fallback_provider' must be a non-empty string when set."
            )

        if self.fallback_model is not None and not self.fallback_model.strip():
            errors.append(
                "'fallback_model' must be a non-empty string when set."
            )

        if errors:
            raise ConfigError(
                f"Invalid AgentConfig '{self.name}':\n"
                + "\n".join(f"  • {e}" for e in errors)
            )


# ---------------------------------------------------------------------------
# Default registry entries
# ---------------------------------------------------------------------------

_DEFAULT_REGISTRY: Dict[str, AgentConfig] = {
    "research_agent": AgentConfig(
        name="research_agent",
        role="research",
        provider=settings.ai.provider,
        model=settings.ai.model,
        system_prompt_key="research_agent",
        temperature=settings.ai.temperature,
        max_tokens=constants.DEFAULT_TOKEN_LIMITS["research_agent"],
        top_p=1.0,
        timeout=settings.ai.timeout,
        retry_count=settings.ai.max_retries,
        enabled=True,
        priority=1,
        fallback_provider="mistral",
        fallback_model="mistral-large-latest",
        capabilities=ProviderCapabilities(
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            supports_reasoning=False,
        ),
        metadata={
            "version": "1.0",
            "owner": "core",
            "description": f"Primary research agent — {settings.ai.provider.upper()} / {settings.ai.model}",
        },
    ),
    "critical_agent": AgentConfig(
        name="critical_agent",
        role="opponent",
        provider="openai",
        model="gpt-4o-mini",
        system_prompt_key="opponent_agent",
        temperature=constants.DEFAULT_TEMPERATURES.get("opponent_agent", 0.6),
        max_tokens=constants.DEFAULT_TOKEN_LIMITS["opponent_agent"],
        top_p=1.0,
        timeout=settings.ai.timeout,
        retry_count=settings.ai.max_retries,
        enabled=True,
        priority=1,
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
        capabilities=ProviderCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_reasoning=False,
        ),
        metadata={
            "version": "2.0",
            "owner": "core",
            "description": "Adversarial opponent agent — OpenAI / gpt-4o-mini",
        },
    ),
    "consensus_agent": AgentConfig(
        name="consensus_agent",
        role="consensus",
        provider="mistral",
        model="mistral-large-latest",
        system_prompt_key="consensus_agent",
        temperature=constants.DEFAULT_TEMPERATURES.get("consensus_agent", 0.5),
        max_tokens=constants.DEFAULT_TOKEN_LIMITS["consensus_agent"],
        top_p=1.0,
        timeout=settings.ai.timeout,
        retry_count=settings.ai.max_retries,
        enabled=True,
        priority=1,
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
        capabilities=ProviderCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            supports_reasoning=False,
        ),
        metadata={
            "version": "1.0",
            "owner": "core",
            "description": "Primary consensus agent — Mistral Large",
        },
    ),
}


# ---------------------------------------------------------------------------
# AgentRegistry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """
    Registry that maps role names to their AgentConfig objects.

    Primary lookup is by role via :meth:`get`, which always returns the
    highest-priority enabled agent for that role.  Secondary lookup by
    unique name is available via :meth:`get_by_name`.

    Parameters
    ----------
    registry:
        Optional seed dictionary (name → AgentConfig).
        Defaults to the built-in production registry.
    """

    def __init__(
        self,
        registry: Optional[Dict[str, AgentConfig]] = None,
    ) -> None:
        self._registry: Dict[str, AgentConfig] = (
            registry if registry is not None else dict(_DEFAULT_REGISTRY)
        )
        self._log_startup()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, role: str) -> AgentConfig:
        """
        Return the highest-priority enabled AgentConfig for *role*.

        This is the method the Debate Engine calls.  It never needs to
        know the agent's name, provider, or model.

        Parameters
        ----------
        role:
            Logical role name (e.g. ``"research"``, ``"critical"``).

        Returns
        -------
        AgentConfig
            The active configuration for that role.

        Raises
        ------
        RegistryError
            If no enabled agent exists for the requested role.
        """
        candidates = [
            cfg for cfg in self._registry.values()
            if cfg.role == role and cfg.enabled
        ]

        if not candidates:
            all_roles = self.all_roles()
            raise RegistryError(
                f"No enabled agent found for role '{role}'. "
                f"Registered roles: {all_roles}"
            )

        # Return lowest priority number = highest priority.
        return min(candidates, key=lambda c: c.priority)

    def get_by_name(self, name: str) -> AgentConfig:
        """
        Return the AgentConfig with the exact *name*.

        Useful for targeting a specific variant (e.g. ``"research_agent_v2"``).

        Parameters
        ----------
        name:
            The unique agent name (``AgentConfig.name``).

        Raises
        ------
        RegistryError
            If the name is not found.
        """
        config = self._registry.get(name)
        if config is None:
            raise RegistryError(
                f"Agent '{name}' not found in registry. "
                f"Registered names: {list(self._registry.keys())}"
            )
        return config

    def register(self, config: AgentConfig) -> None:
        """
        Add or replace an agent configuration.

        Logs a warning if overwriting an existing entry.

        Parameters
        ----------
        config:
            A validated AgentConfig instance.
        """
        if config.name in self._registry:
            logger.warning(
                f"AgentRegistry: overwriting existing config '{config.name}'."
            )

        self._registry[config.name] = config
        logger.info(
            f"AgentRegistry: registered '{config.name}' | "
            f"role={config.role} | provider={config.provider} | "
            f"model={config.model} | enabled={config.enabled} | "
            f"priority={config.priority}"
        )

    def disable(self, name: str) -> None:
        """
        Disable the agent with *name* without removing it from the registry.

        Frozen dataclasses cannot be mutated, so this replaces the entry
        with a copy that has ``enabled=False``.

        Parameters
        ----------
        name:
            The unique agent name to disable.

        Raises
        ------
        RegistryError
            If the name is not found.
        """
        config = self.get_by_name(name)
        import dataclasses
        disabled = dataclasses.replace(config, enabled=False)
        self._registry[name] = disabled
        logger.info(f"AgentRegistry: disabled agent '{name}'.")

    def enable(self, name: str) -> None:
        """
        Re-enable a previously disabled agent.

        Parameters
        ----------
        name:
            The unique agent name to enable.

        Raises
        ------
        RegistryError
            If the name is not found.
        """
        config = self.get_by_name(name)
        import dataclasses
        enabled = dataclasses.replace(config, enabled=True)
        self._registry[name] = enabled
        logger.info(f"AgentRegistry: enabled agent '{name}'.")

    def all_roles(self) -> List[str]:
        """Return all unique role names (enabled and disabled)."""
        return sorted({cfg.role for cfg in self._registry.values()})

    def all_configs(self) -> List[AgentConfig]:
        """Return every registered AgentConfig, sorted by role then priority."""
        return sorted(
            self._registry.values(),
            key=lambda c: (c.role, c.priority),
        )

    def enabled_configs(self) -> List[AgentConfig]:
        """Return only enabled AgentConfig entries."""
        return [c for c in self.all_configs() if c.enabled]

    def disabled_configs(self) -> List[AgentConfig]:
        """Return only disabled AgentConfig entries."""
        return [c for c in self.all_configs() if not c.enabled]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_startup(self) -> None:
        """Emit a structured startup summary to the log."""
        total = len(self._registry)
        enabled = self.enabled_configs()
        disabled = self.disabled_configs()
        providers = sorted({c.provider for c in self._registry.values()})
        roles = self.all_roles()

        logger.info(
            f"AgentRegistry initialised | "
            f"total={total} | enabled={len(enabled)} | disabled={len(disabled)} | "
            f"roles={roles} | providers={providers}"
        )

        for cfg in self.all_configs():
            status = "✓" if cfg.enabled else "✗"
            logger.info(
                f"  [{status}] {cfg.name} | role={cfg.role} | "
                f"provider={cfg.provider} | model={cfg.model} | "
                f"priority={cfg.priority} | "
                f"tokens={cfg.max_tokens} | timeout={cfg.timeout}s"
            )
