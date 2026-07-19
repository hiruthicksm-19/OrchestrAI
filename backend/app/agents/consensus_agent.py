"""
Consensus Agent.

Synthesises all debate contributions into the highest-quality final answer.
It evaluates both sides, merges the strongest reasoning, and produces
a balanced conclusion — not a recap of the debate.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from backend.app.agents.base_agent import BaseAgent
from backend.app.debate.debate_state import DebateMessage, ResponseType
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class ConsensusAgent(BaseAgent):
    """
    Concrete consensus / synthesis agent.

    Context keys consumed
    ---------------------
    ``question``           : str — the debate question
    ``research_opening``   : str — Research Agent's opening
    ``opponent_opening``   : str — Opponent Agent's opening
    ``research_rebuttal``  : str — Research Agent's rebuttal (may be empty)
    ``opponent_rebuttal``  : str — Opponent Agent's rebuttal (may be empty)
    ``question_type``      : str — detected question category
    """

    async def respond(self, context: Dict[str, Any]) -> str:
        """Synthesise the debate and produce the final answer."""
        t0 = time.monotonic()

        question: str = context["question"]
        research_opening: str = context.get("research_opening", "")
        opponent_opening: str = context.get("opponent_opening", "")
        research_rebuttal: str = context.get("research_rebuttal", "")
        opponent_rebuttal: str = context.get("opponent_rebuttal", "")
        question_type: str = context.get("question_type", "explanation")

        system = self._prompt_manager.get_system(key=self._config.system_prompt_key)

        user = self._prompt_manager.render_strategy(
            key=self._config.system_prompt_key,
            question=question,
            research_opening=research_opening,
            opponent_opening=opponent_opening,
            research_rebuttal=research_rebuttal,
            opponent_rebuttal=opponent_rebuttal,
            question_type=question_type,
        )

        logger.info("ConsensusAgent synthesising final answer")
        content = await self._call_provider(system=system, user=user)
        latency_ms = (time.monotonic() - t0) * 1000

        context["_message"] = DebateMessage(
            role=self._config.role,
            agent_name=self._config.name,
            provider=self._provider.provider_name,
            model=self._config.model,
            round=context.get("round", 1),
            response_type=ResponseType.CONSENSUS,
            content=content,
            latency_ms=latency_ms,
        )

        logger.info(f"ConsensusAgent complete | latency={latency_ms:.0f}ms")
        return content
