"""
Research Agent.

In a full adversarial debate the Research Agent defends ONE position.
It does not attempt to present both sides — that is the Consensus Agent's job.

Stages handled
--------------
INITIAL_RESEARCH  — Opening statement defending the assigned position.
RESEARCH_REBUTTAL — Rebuttal after reading the Opponent's opening.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.debate.debate_state import DebateMessage, ResponseType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent(BaseAgent):
    """
    Concrete research / proponent agent.

    Context keys consumed
    ---------------------
    ``question``          : str  — the debate question
    ``position``          : str  — the position to defend (optional)
    ``opponent_response`` : str  — opponent's opening or rebuttal (for rebuttals)
    ``response_type``     : str  — "opening" or "rebuttal"
    """

    async def respond(self, context: Dict[str, Any]) -> str:
        """Generate an opening statement or rebuttal and return the text."""
        t0 = time.monotonic()

        question: str = context["question"]
        position: str = context.get("position", "")
        opponent_response: str = context.get("opponent_response", "")
        response_type: str = context.get("response_type", "opening")

        system = self._prompt_manager.get_system(key=self._config.system_prompt_key)

        if response_type == "rebuttal" and opponent_response:
            user = self._prompt_manager.render_strategy(
                key=self._config.system_prompt_key + "_rebuttal",
                question=question,
                position=position,
                opponent_response=opponent_response,
            )
            msg_type = ResponseType.REBUTTAL
            logger.info(f"ResearchAgent generating rebuttal")
        else:
            user = self._prompt_manager.render_strategy(
                key=self._config.system_prompt_key,
                question=question,
                position=position,
            )
            msg_type = ResponseType.OPENING
            logger.info(f"ResearchAgent generating opening statement")

        content = await self._call_provider(system=system, user=user)
        latency_ms = (time.monotonic() - t0) * 1000

        # Store structured message on context for engine to pick up.
        context["_message"] = DebateMessage(
            role=self._config.role,
            agent_name=self._config.name,
            provider=self._provider.provider_name,
            model=self._config.model,
            round=context.get("round", 1),
            response_type=msg_type,
            content=content,
            latency_ms=latency_ms,
        )

        logger.info(f"ResearchAgent complete | latency={latency_ms:.0f}ms")
        return content
