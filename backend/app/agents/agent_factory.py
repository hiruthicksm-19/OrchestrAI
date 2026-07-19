"""
Agent Factory.

Creates the correct concrete agent class from an AgentConfig.
No other layer needs to know which class maps to which role.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.core.agent_registry import AgentConfig
from app.providers.base_provider import BaseProvider
from app.prompts.prompt_manager import PromptManager
from app.utils.exceptions import RegistryError


def create_agent(
    config: AgentConfig,
    provider: BaseProvider,
    prompt_manager: PromptManager,
) -> BaseAgent:
    """
    Instantiate the correct BaseAgent subclass for *config.role*.

    Parameters
    ----------
    config:
        Agent configuration from the AgentRegistry.
    provider:
        Pre-built provider instance.
    prompt_manager:
        Shared PromptManager.

    Returns
    -------
    BaseAgent

    Raises
    ------
    RegistryError
        If the role has no corresponding class.
    """
    from app.agents.research_agent import ResearchAgent
    from app.agents.opponent_agent import OpponentAgent
    from app.agents.critical_agent import CriticalAgent
    from app.agents.consensus_agent import ConsensusAgent

    _ROLE_MAP = {
        "research": ResearchAgent,
        "opponent": OpponentAgent,
        "critical": CriticalAgent,   # backward compat alias → OpponentAgent
        "consensus": ConsensusAgent,
    }

    cls = _ROLE_MAP.get(config.role)
    if cls is None:
        raise RegistryError(
            f"No agent class registered for role '{config.role}'. "
            f"Known roles: {list(_ROLE_MAP.keys())}"
        )

    return cls(config=config, provider=provider, prompt_manager=prompt_manager)
