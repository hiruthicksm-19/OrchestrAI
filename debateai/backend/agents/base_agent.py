"""
Abstract base class that every agent must implement.

Agents are aware of their role and prompt templates but are completely
unaware of which provider or model backs them.  That detail lives in the
AgentConfig and is resolved by the Debate Engine via the provider factory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.config.agent_registry import AgentConfig
from backend.providers.base_provider import BaseProvider
from backend.prompts.prompt_manager import PromptManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract agent interface.

    Parameters
    ----------
    config:
        The agent's configuration record from the AgentRegistry.
    provider:
        A concrete BaseProvider instance (injected by the Debate Engine).
    prompt_manager:
        Shared PromptManager instance for loading templates.
    """

    def __init__(
        self,
        config: AgentConfig,
        provider: BaseProvider,
        prompt_manager: PromptManager,
    ) -> None:
        self._config = config
        self._provider = provider
        self._prompt_manager = prompt_manager
        logger.info(
            f"{self.__class__.__name__} initialised | "
            f"name={config.name} | role={config.role} | "
            f"provider={provider.provider_name} | model={config.model}"
        )

    @property
    def role(self) -> str:
        """The agent's logical role name."""
        return self._config.role

    @abstractmethod
    async def respond(self, context: Dict[str, Any]) -> str:
        """
        Generate a response given the debate *context*.

        Parameters
        ----------
        context:
            A dictionary of named values the agent needs to compose its
            prompt (e.g. ``{"question": "…", "research_response": "…"}``).

        Returns
        -------
        str
            The agent's response text.
        """

    # ------------------------------------------------------------------
    # Protected helpers available to all concrete agents
    # ------------------------------------------------------------------

    async def _call_provider(self, system: str, user: str) -> str:
        """
        Build a standard [system, user] message list and call the provider.

        Parameters
        ----------
        system:
            The system prompt string.
        user:
            The user turn prompt string.
        """
        from backend.providers.base_provider import Message

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        logger.debug(
            f"{self.__class__.__name__}._call_provider | "
            f"model={self._config.model} | temperature={self._config.temperature}"
        )

        return await self._provider.complete(
            messages=messages,
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )
