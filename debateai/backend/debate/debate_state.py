"""
Debate State — the authoritative data model for a running and completed debate.

DebateState is the single object passed between all stages of the Debate Engine.
Agents receive it (read-only) and the engine appends messages to it.

DebateResult is retained for backward compatibility with the terminal UI
but is now derived from DebateState at the end of a debate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------

class ResponseType(str, Enum):
    """Classifies what role a message plays in the debate."""
    OPENING = "opening"           # First statement by an agent
    REBUTTAL = "rebuttal"         # Response to the opponent's opening / rebuttal
    CONSENSUS = "consensus"       # Final synthesised answer


@dataclass
class DebateMessage:
    """
    A single structured message produced by one agent during a debate.

    Attributes
    ----------
    role:
        Logical agent role (``"research"``, ``"opponent"``, ``"consensus"``).
    agent_name:
        Registry name of the agent that produced this message.
    provider:
        Provider that served the response (e.g. ``"groq"``).
    model:
        Model identifier (e.g. ``"llama-3.3-70b-versatile"``).
    round:
        Debate round number (1-based).
    response_type:
        Whether this is an opening statement, rebuttal, or consensus.
    content:
        The text content of the message.
    latency_ms:
        Wall-clock milliseconds taken to generate the response.
    token_usage:
        Optional token count metadata from the provider.
    created_at:
        UTC timestamp when the message was created.
    """

    role: str
    agent_name: str
    provider: str
    model: str
    round: int
    response_type: ResponseType
    content: str
    latency_ms: float = 0.0
    token_usage: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Debate State
# ---------------------------------------------------------------------------

@dataclass
class DebateState:
    """
    Mutable state object that lives for the duration of one debate.

    The Debate Engine populates this as it progresses through stages.
    Agents read from it; only the engine writes to it.

    Attributes
    ----------
    question:
        The user's original question.
    question_type:
        Detected category (e.g. ``"debate"``, ``"factual"``).
    debate_strategy:
        Name of the selected workflow strategy.
    participants:
        List of agent role names participating in this debate.
    messages:
        Ordered list of all DebateMessage objects produced.
    current_round:
        The round currently being executed (1-based).
    metadata:
        Arbitrary context (positions, question classification details, etc.).
    final_answer:
        The Consensus Agent's synthesised output.
    started_at:
        UTC timestamp when the debate began.
    completed_at:
        UTC timestamp when the debate finished.
    """

    question: str
    question_type: str = "unknown"
    debate_strategy: str = "unknown"
    participants: List[str] = field(default_factory=list)
    messages: List[DebateMessage] = field(default_factory=list)
    current_round: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    final_answer: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def add_message(self, message: DebateMessage) -> None:
        """Append a message to the debate transcript."""
        self.messages.append(message)

    def get_messages_by_role(self, role: str) -> List[DebateMessage]:
        """Return all messages produced by *role*, in order."""
        return [m for m in self.messages if m.role == role]

    def get_last_message_by_role(self, role: str) -> Optional[DebateMessage]:
        """Return the most recent message from *role*, or None."""
        msgs = self.get_messages_by_role(role)
        return msgs[-1] if msgs else None

    def get_opening(self, role: str) -> Optional[DebateMessage]:
        """Return the opening statement from *role*, or None."""
        for m in self.messages:
            if m.role == role and m.response_type == ResponseType.OPENING:
                return m
        return None

    def get_rebuttal(self, role: str) -> Optional[DebateMessage]:
        """Return the rebuttal from *role*, or None."""
        for m in self.messages:
            if m.role == role and m.response_type == ResponseType.REBUTTAL:
                return m
        return None

    def duration_seconds(self) -> float:
        """Return elapsed seconds, or 0 if not completed."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def finalise(self) -> None:
        """Mark the debate as complete."""
        self.completed_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Legacy DebateResult — kept for backward compatibility with main.py
# ---------------------------------------------------------------------------

@dataclass
class DebateRound:
    """One exchange between the Research and Opponent agents."""

    round_number: int
    research_response: str
    critical_response: str  # kept as "critical_response" for UI compatibility


@dataclass
class DebateResult:
    """
    Terminal-display-friendly view of a completed debate.
    Derived from DebateState at the end of engine execution.
    """

    question: str
    question_type: str = "unknown"
    debate_strategy: str = "unknown"
    rounds: List[DebateRound] = field(default_factory=list)
    research_rebuttal: str = ""
    critical_rebuttal: str = ""
    consensus: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    state: Optional[DebateState] = None  # full state for advanced consumers

    def finalise(self) -> None:
        """Mark the debate as complete and record timing."""
        self.completed_at = datetime.now(timezone.utc)
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    @classmethod
    def from_state(cls, state: DebateState) -> "DebateResult":
        """
        Build a DebateResult from a completed DebateState.

        Maps the structured message log back to the flat fields
        the terminal UI expects.
        """
        research_opening = state.get_opening("research")
        opponent_opening = state.get_opening("opponent")
        research_rebuttal = state.get_rebuttal("research")
        opponent_rebuttal = state.get_rebuttal("opponent")

        rounds = []
        if research_opening or opponent_opening:
            rounds.append(DebateRound(
                round_number=1,
                research_response=research_opening.content if research_opening else "",
                critical_response=opponent_opening.content if opponent_opening else "",
            ))

        result = cls(
            question=state.question,
            question_type=state.question_type,
            debate_strategy=state.debate_strategy,
            rounds=rounds,
            research_rebuttal=research_rebuttal.content if research_rebuttal else "",
            critical_rebuttal=opponent_rebuttal.content if opponent_rebuttal else "",
            consensus=state.final_answer,
            started_at=state.started_at,
            state=state,
        )
        result.finalise()
        return result
