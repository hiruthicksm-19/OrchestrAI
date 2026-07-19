"""
Debate Engine — redesigned for genuine adversarial debate.

Workflow
--------
1.  Classify the question (heuristic, no LLM).
2.  Select the debate strategy (workflow stages + parallelism flags).
3.  Assign positions to Research and Opponent agents.
4.  Execute stages — opening statements in parallel when the strategy allows.
5.  Execute rebuttals — in parallel when the strategy allows.
6.  Synthesise via the Consensus Agent.
7.  Return a DebateResult (backward-compatible) backed by a DebateState.

The engine knows nothing about:
  - Which provider or model is behind each agent.
  - How prompts are stored or rendered.
  - How results are persisted (future).
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Tuple

from backend.app.agents.agent_factory import create_agent
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.agent_registry import AgentRegistry
from backend.app.core.settings import Settings
from backend.app.debate.debate_state import (
    DebateResult,
    DebateState,
    ResponseType,
)
from backend.app.debate.debate_strategy import (
    StrategySelector,
    WorkflowStage,
)
from backend.app.debate.question_classifier import QuestionClassifier, QuestionType
from backend.app.prompts.prompt_manager import PromptManager
from backend.app.providers.provider_factory import create_provider
from backend.app.utils.exceptions import DebateEngineError
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Position assignment for adversarial debates
# ---------------------------------------------------------------------------

_POSITION_MAP: dict[QuestionType, Tuple[str, str]] = {
    # (research_position, opponent_position)
    QuestionType.DEBATE: ("in favour", "against"),
    QuestionType.COMPARISON: ("advocating the first option", "advocating the second option"),
    QuestionType.FACTUAL: ("providing the correct answer", "providing additional context or nuance"),
    QuestionType.EXPLANATION: ("explaining the concept", "offering an alternative perspective"),
}

_DEFAULT_POSITIONS: Tuple[str, str] = ("supporting the primary view", "challenging the primary view")


def _assign_positions(question: str, q_type: QuestionType) -> Tuple[str, str]:
    """
    Return (research_position, opponent_position) for a given question type.

    For debate questions involving specific topics, we attempt to infer
    clearer positional labels from keywords in the question.
    """
    if q_type == QuestionType.DEBATE:
        q_lower = question.lower()
        # Look for "should X replace Y" or "will X replace Y" patterns.
        if "replace" in q_lower or "take over" in q_lower:
            subject = _extract_subject(q_lower)
            return (f"arguing that {subject} WILL/SHOULD happen", f"arguing that {subject} WILL NOT/SHOULD NOT happen")
        if "better" in q_lower or "best" in q_lower:
            return ("arguing FOR the position implied by the question", "arguing AGAINST the position implied by the question")

    return _POSITION_MAP.get(q_type, _DEFAULT_POSITIONS)


def _extract_subject(q_lower: str) -> str:
    """Extract a short subject phrase for position labelling."""
    # Very simple extraction — just return a trimmed version.
    q_lower = q_lower.strip().rstrip("?")
    if len(q_lower) > 60:
        return q_lower[:60] + "..."
    return q_lower


# ---------------------------------------------------------------------------
# Debate Engine
# ---------------------------------------------------------------------------

class DebateEngine:
    """
    Orchestrates an adaptive, adversarial multi-agent debate.

    Parameters
    ----------
    settings:
        Application settings (API keys, round count, timeouts).
    registry:
        AgentRegistry that maps role names to AgentConfig.
    prompt_manager:
        PromptManager for loading prompt templates.
    """

    def __init__(
        self,
        settings: Settings,
        registry: Optional[AgentRegistry] = None,
        prompt_manager: Optional[PromptManager] = None,
    ) -> None:
        self._settings = settings
        self._registry = registry or AgentRegistry()
        self._prompt_manager = prompt_manager or PromptManager(settings.prompts_dir)
        self._classifier = QuestionClassifier()
        self._selector = StrategySelector()

        self._api_keys: dict[str, str] = {
            "groq": settings.groq_api_key,
            "mistral": settings.mistral_api_key,
            "cerebras": settings.cerebras_api_key,
            "openai": settings.openai_api_key,
        }

        logger.info(
            f"DebateEngine initialised | rounds={settings.debate.rounds} | "
            f"timeout={settings.debate.timeout_seconds}s"
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self, question: str) -> DebateResult:
        """
        Execute a full adaptive debate on *question*.

        Parameters
        ----------
        question:
            The user's question / debate topic.

        Returns
        -------
        DebateResult
            Backward-compatible result with full DebateState attached.

        Raises
        ------
        DebateEngineError
        """
        if not question or not question.strip():
            raise DebateEngineError("Question must not be empty.")

        question = question.strip()
        t_start = time.monotonic()

        # ------------------------------------------------------------------
        # Step 1: Classify + select strategy
        # ------------------------------------------------------------------
        q_type = self._classifier.classify(question)
        strategy = self._selector.select(q_type)

        state = DebateState(
            question=question,
            question_type=q_type.value,
            debate_strategy=strategy.name,
        )

        logger.info(
            f"Debate started | question='{question[:80]}' | "
            f"type={q_type.value} | strategy='{strategy.name}'"
        )

        try:
            # ------------------------------------------------------------------
            # Step 2: Build agents
            # ------------------------------------------------------------------
            research_agent = self._build_agent("research")
            consensus_agent = self._build_agent("consensus")

            # Opponent is only needed for multi-agent strategies.
            needs_opponent = any(
                s in strategy.stages
                for s in (WorkflowStage.INITIAL_OPPONENT,
                          WorkflowStage.OPPONENT_REBUTTAL)
            )
            opponent_agent: Optional[BaseAgent] = (
                self._build_agent("opponent") if needs_opponent else None
            )

            # Assign debate positions.
            research_pos, opponent_pos = _assign_positions(question, q_type)
            state.metadata["research_position"] = research_pos
            state.metadata["opponent_position"] = opponent_pos
            state.participants = ["research"] + (["opponent"] if needs_opponent else []) + ["consensus"]

            # ------------------------------------------------------------------
            # Step 3: Execute workflow stages
            # ------------------------------------------------------------------
            research_opening = ""
            opponent_opening = ""
            research_rebuttal = ""
            opponent_rebuttal = ""

            # Opening statements -------------------------------------------
            if WorkflowStage.INITIAL_RESEARCH in strategy.stages:
                if strategy.parallel_opening and WorkflowStage.INITIAL_OPPONENT in strategy.stages:
                    # Run both opening statements concurrently.
                    logger.info("Executing parallel opening statements")
                    t_par = time.monotonic()

                    res_ctx = {"question": question, "position": research_pos,
                               "opponent_response": "", "response_type": "opening", "round": 1}
                    opp_ctx = {"question": question, "position": opponent_pos,
                               "opponent_response": "", "response_type": "opening", "round": 1}

                    research_opening, opponent_opening = await asyncio.gather(
                        research_agent.respond(res_ctx),
                        opponent_agent.respond(opp_ctx),
                    )

                    par_ms = (time.monotonic() - t_par) * 1000
                    logger.info(f"Parallel openings complete | {par_ms:.0f}ms")

                    # Collect structured messages.
                    if "_message" in res_ctx:
                        state.add_message(res_ctx["_message"])
                    if "_message" in opp_ctx:
                        state.add_message(opp_ctx["_message"])

                else:
                    # Sequential — research only (simple strategies).
                    res_ctx = {"question": question, "position": research_pos,
                               "opponent_response": "", "response_type": "opening", "round": 1}
                    research_opening = await research_agent.respond(res_ctx)
                    if "_message" in res_ctx:
                        state.add_message(res_ctx["_message"])

                    if WorkflowStage.INITIAL_OPPONENT in strategy.stages and opponent_agent:
                        opp_ctx = {"question": question, "position": opponent_pos,
                                   "opponent_response": research_opening,
                                   "response_type": "opening", "round": 1}
                        opponent_opening = await opponent_agent.respond(opp_ctx)
                        if "_message" in opp_ctx:
                            state.add_message(opp_ctx["_message"])

            # Rebuttals --------------------------------------------------------
            if WorkflowStage.RESEARCH_REBUTTAL in strategy.stages:
                if strategy.parallel_rebuttal and WorkflowStage.OPPONENT_REBUTTAL in strategy.stages:
                    # Run both rebuttals concurrently.
                    logger.info("Executing parallel rebuttals")
                    t_par = time.monotonic()

                    res_reb_ctx = {"question": question, "position": research_pos,
                                   "opponent_response": opponent_opening,
                                   "response_type": "rebuttal", "round": 2}
                    opp_reb_ctx = {"question": question, "position": opponent_pos,
                                   "opponent_response": research_opening,
                                   "response_type": "rebuttal", "round": 2}

                    research_rebuttal, opponent_rebuttal = await asyncio.gather(
                        research_agent.respond(res_reb_ctx),
                        opponent_agent.respond(opp_reb_ctx),
                    )

                    par_ms = (time.monotonic() - t_par) * 1000
                    logger.info(f"Parallel rebuttals complete | {par_ms:.0f}ms")

                    if "_message" in res_reb_ctx:
                        state.add_message(res_reb_ctx["_message"])
                    if "_message" in opp_reb_ctx:
                        state.add_message(opp_reb_ctx["_message"])

                else:
                    res_reb_ctx = {"question": question, "position": research_pos,
                                   "opponent_response": opponent_opening,
                                   "response_type": "rebuttal", "round": 2}
                    research_rebuttal = await research_agent.respond(res_reb_ctx)
                    if "_message" in res_reb_ctx:
                        state.add_message(res_reb_ctx["_message"])

                    if WorkflowStage.OPPONENT_REBUTTAL in strategy.stages and opponent_agent:
                        opp_reb_ctx = {"question": question, "position": opponent_pos,
                                       "opponent_response": research_rebuttal,
                                       "response_type": "rebuttal", "round": 2}
                        opponent_rebuttal = await opponent_agent.respond(opp_reb_ctx)
                        if "_message" in opp_reb_ctx:
                            state.add_message(opp_reb_ctx["_message"])

            # Consensus --------------------------------------------------------
            logger.info("Generating consensus")
            con_ctx = {
                "question": question,
                "research_opening": research_opening,
                "opponent_opening": opponent_opening,
                "research_rebuttal": research_rebuttal,
                "opponent_rebuttal": opponent_rebuttal,
                "question_type": q_type.value,
                "round": 3,
            }
            final_answer = await consensus_agent.respond(con_ctx)
            if "_message" in con_ctx:
                state.add_message(con_ctx["_message"])

            state.final_answer = final_answer
            state.finalise()

            total_ms = (time.monotonic() - t_start) * 1000
            logger.info(
                f"Debate complete | strategy='{strategy.name}' | "
                f"total={total_ms:.0f}ms | messages={len(state.messages)}"
            )

            return DebateResult.from_state(state)

        except DebateEngineError:
            raise
        except Exception as exc:
            raise DebateEngineError(
                f"Debate failed: {type(exc).__name__}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_agent(self, role: str) -> BaseAgent:
        """Assemble a ready-to-use agent from registry config + factory."""
        config = self._registry.get(role)
        api_key = self._api_keys.get(config.provider)
        if not api_key:
            raise DebateEngineError(
                f"No API key configured for provider '{config.provider}' "
                f"(required by the '{role}' agent)."
            )
        provider = create_provider(
            provider_name=config.provider,
            api_key=api_key,
            timeout=config.timeout,
        )
        return create_agent(
            config=config,
            provider=provider,
            prompt_manager=self._prompt_manager,
        )
