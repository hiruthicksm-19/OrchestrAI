"""
Opponent Agent.

The Opponent Agent is a genuine adversarial debater — not a reviewer.
It takes the opposing position, defends it with evidence, and challenges
the Research Agent's arguments directly.

It does NOT:
  - Review grammar or writing quality.
  - Say "partially correct" as a verdict.
  - Simply list what the Research Agent said.

It DOES:
  - Take the opposing viewpoint from the Research Agent.
  - Challenge assumptions with counter-evidence.
  - Expose logical weaknesses in the opponent's position.
  - Defend its own position even under pressure.

Stages handled
--------------
INITIAL_OPPONENT  — Opening statement for the opposing position.
OPPONENT_REBUTTAL — Rebuttal after reading the Research Agent's rebuttal.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.debate.debate_state import DebateMessage, ResponseType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OpponentAgent(BaseAgent):
    """
    Concrete adversarial opponent agent.

    Context keys consumed
    ---------------------
    ``question``            : str  — the debate question
    ``position``            : str  — the opposing position to defend
    ``opponent_response``   : str  — Research Agent's opening or rebuttal
    ``response_type``       : str  — "opening" or "rebuttal"
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
            logger.info("OpponentAgent generating rebuttal")
        else:
            user = self._prompt_manager.render_strategy(
                key=self._config.system_prompt_key,
                question=question,
                position=position,
                research_opening=opponent_response,
            )
            msg_type = ResponseType.OPENING
            logger.info("OpponentAgent generating opening statement")

        content = await self._call_provider(system=system, user=user)
        latency_ms = (time.monotonic() - t0) * 1000

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

        logger.info(f"OpponentAgent complete | latency={latency_ms:.0f}ms")
        return content
