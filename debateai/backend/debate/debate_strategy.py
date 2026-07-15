"""
Debate Strategy definitions and selector.

A DebateStrategy describes the workflow the Debate Engine should follow
for a given question type.  The selector maps QuestionType → DebateStrategy.

This is configuration only — no execution logic lives here.

Workflow stages
---------------
RESEARCH_ONLY       Research → Consensus
FULL_DEBATE         Research ║ Opponent (parallel) → Rebuttals (parallel) → Consensus
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from backend.debate.question_classifier import QuestionType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowStage(str, Enum):
    """Named stages the Debate Engine can execute."""

    INITIAL_RESEARCH = "initial_research"       # Research Agent opens
    INITIAL_OPPONENT = "initial_opponent"       # Opponent Agent opens (parallel w/ research)
    RESEARCH_REBUTTAL = "research_rebuttal"     # Research Agent rebuts opponent
    OPPONENT_REBUTTAL = "opponent_rebuttal"     # Opponent Agent rebuts research
    CONSENSUS = "consensus"                     # Consensus Agent synthesises


@dataclass(frozen=True)
class DebateStrategy:
    """
    Describes the workflow for a specific question category.

    Attributes
    ----------
    name:
        Human-readable label (e.g. ``"Full Adversarial Debate"``).
    question_type:
        The QuestionType this strategy handles.
    stages:
        Ordered list of WorkflowStages to execute.
    parallel_opening:
        If True, INITIAL_RESEARCH and INITIAL_OPPONENT run concurrently.
    parallel_rebuttal:
        If True, RESEARCH_REBUTTAL and OPPONENT_REBUTTAL run concurrently.
    description:
        Human-readable explanation shown in the terminal.
    """

    name: str
    question_type: QuestionType
    stages: List[WorkflowStage]
    parallel_opening: bool = False
    parallel_rebuttal: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# Strategy catalogue
# ---------------------------------------------------------------------------

# Factual: single correct answer — one agent is enough.
STRATEGY_FACTUAL = DebateStrategy(
    name="Direct Answer",
    question_type=QuestionType.FACTUAL,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Factual question — direct answer via Research + Consensus.",
)

# Explanation: one authoritative explanation is better than an adversarial fight.
STRATEGY_EXPLANATION = DebateStrategy(
    name="Expert Explanation",
    question_type=QuestionType.EXPLANATION,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Explanation question — Research Agent explains, Consensus refines.",
)

# Comparison: both agents take one side each and argue it.
STRATEGY_COMPARISON = DebateStrategy(
    name="Comparative Debate",
    question_type=QuestionType.COMPARISON,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.INITIAL_OPPONENT,
        WorkflowStage.CONSENSUS,
    ],
    parallel_opening=True,
    description="Comparison — two agents argue opposing sides, Consensus synthesises.",
)

# Full adversarial debate: both agents open, both rebutt.
STRATEGY_DEBATE = DebateStrategy(
    name="Full Adversarial Debate",
    question_type=QuestionType.DEBATE,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.INITIAL_OPPONENT,
        WorkflowStage.RESEARCH_REBUTTAL,
        WorkflowStage.OPPONENT_REBUTTAL,
        WorkflowStage.CONSENSUS,
    ],
    parallel_opening=True,
    parallel_rebuttal=True,
    description="Normative debate — adversarial positions, full rebuttal exchange.",
)

# Coding: single best implementation, consensus polishes.
STRATEGY_CODING = DebateStrategy(
    name="Code Generation",
    question_type=QuestionType.CODING,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Coding question — Research generates, Consensus reviews.",
)

# Architecture: explanation-style, no adversarial positions needed.
STRATEGY_ARCHITECTURE = DebateStrategy(
    name="Architecture Review",
    question_type=QuestionType.ARCHITECTURE,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Architecture question — Research proposes, Consensus refines.",
)

# Reasoning: single logical chain.
STRATEGY_REASONING = DebateStrategy(
    name="Logical Reasoning",
    question_type=QuestionType.REASONING,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Reasoning question — step-by-step analysis.",
)

# Creative: free-form, no adversarial positions.
STRATEGY_CREATIVE = DebateStrategy(
    name="Creative Response",
    question_type=QuestionType.CREATIVE,
    stages=[
        WorkflowStage.INITIAL_RESEARCH,
        WorkflowStage.CONSENSUS,
    ],
    description="Creative prompt — Research generates, Consensus refines.",
)

# ---------------------------------------------------------------------------
# Strategy Selector
# ---------------------------------------------------------------------------

_STRATEGY_MAP: dict[QuestionType, DebateStrategy] = {
    QuestionType.FACTUAL: STRATEGY_FACTUAL,
    QuestionType.EXPLANATION: STRATEGY_EXPLANATION,
    QuestionType.COMPARISON: STRATEGY_COMPARISON,
    QuestionType.DEBATE: STRATEGY_DEBATE,
    QuestionType.CODING: STRATEGY_CODING,
    QuestionType.ARCHITECTURE: STRATEGY_ARCHITECTURE,
    QuestionType.REASONING: STRATEGY_REASONING,
    QuestionType.CREATIVE: STRATEGY_CREATIVE,
}


class StrategySelector:
    """
    Selects the appropriate DebateStrategy for a given QuestionType.

    Usage
    -----
        selector = StrategySelector()
        strategy = selector.select(QuestionType.DEBATE)
    """

    def select(self, question_type: QuestionType) -> DebateStrategy:
        """
        Return the DebateStrategy for *question_type*.

        Falls back to STRATEGY_EXPLANATION if the type is not mapped.

        Parameters
        ----------
        question_type:
            The detected question category.

        Returns
        -------
        DebateStrategy
        """
        strategy = _STRATEGY_MAP.get(question_type, STRATEGY_EXPLANATION)
        logger.info(
            f"StrategySelector: {question_type.value} → '{strategy.name}' | "
            f"stages={[s.value for s in strategy.stages]} | "
            f"parallel_opening={strategy.parallel_opening}"
        )
        return strategy
