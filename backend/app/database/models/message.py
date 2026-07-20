"""
Message Model

IMPORTANT: This model represents an Agent Execution Record, not a chat message.

Each row represents one AI agent execution in a debate:
- Research Agent opening statement
- Opponent Agent opening statement
- Consensus Agent synthesis
- etc.

Every agent call generates one row with execution metadata.

Fields:
- id: UUID primary key
- debate_id: Reference to parent debate
- agent_name: Name of the agent (e.g., 'research_agent')
- agent_role: Role of the agent (research, opponent, consensus)
- provider: Which provider executed this agent
- model: Which model was used
- round_number: Debate round (1, 2, etc.)
- response_type: Type of response (initial, rebuttal, consensus, final)
- content: The actual response content
- latency_ms: Execution time in milliseconds
- prompt_tokens: Tokens used in prompt
- completion_tokens: Tokens generated in response
- total_tokens: prompt_tokens + completion_tokens
- cost: Cost of this execution
- success: Whether execution succeeded
- error_message: Error details if failed
- created_at: When this record was created

Relationships:
- debate: Parent debate

Use Cases:
- Performance monitoring (query by latency_ms)
- Provider analytics (group by provider)
- Cost analysis (sum cost by provider/model)
- Execution history (order by created_at)
- Failure tracking (where success=False)
- Token usage tracking (sum tokens by agent)

This is NOT a chat table. It is an execution log.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Enum,
    Integer,
    Float,
    Boolean,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base_model import BaseModel
from app.database.models.enums import AgentRole, ResponseType

if TYPE_CHECKING:
    from app.database.models.debate import Debate


class Message(BaseModel):
    """
    Agent Execution Record

    Each row represents one AI agent execution in a debate.
    """

    __tablename__ = "messages"

    # Foreign keys
    debate_id: Mapped[UUID] = mapped_column(
        ForeignKey("debates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent debate",
    )

    # Agent identification
    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Name of the agent (e.g., 'research_agent')",
    )

    agent_role: Mapped[AgentRole] = mapped_column(
        Enum(AgentRole),
        nullable=False,
        index=True,
        doc="Role of the agent",
    )

    # Execution context
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Which provider executed this agent",
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Which model was used",
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Debate round number",
    )

    response_type: Mapped[ResponseType] = mapped_column(
        Enum(ResponseType),
        nullable=False,
        doc="Type of response",
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="The actual response content",
    )

    # Performance metrics
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Execution time in milliseconds",
    )

    # Token tracking
    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Tokens used in prompt",
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Tokens generated in response",
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Total tokens (prompt + completion)",
    )

    # Cost tracking
    cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Cost of this execution",
    )

    # Execution result
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether execution succeeded",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error details if execution failed",
    )

    # Relationships
    debate: Mapped["Debate"] = relationship(
        back_populates="messages",
        lazy="select",
        doc="Parent debate",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_message_debate_id", "debate_id"),
        Index("idx_message_agent_role", "agent_role"),
        Index("idx_message_provider", "provider"),
        Index("idx_message_created_at", "created_at"),
        Index("idx_message_success", "success"),
        Index("idx_message_debate_round", "debate_id", "round_number"),
        CheckConstraint("latency_ms >= 0"),
        CheckConstraint("cost >= 0"),
        CheckConstraint("prompt_tokens >= 0"),
        CheckConstraint("completion_tokens >= 0"),
        CheckConstraint("total_tokens >= 0"),
        CheckConstraint("round_number >= 1"),
        CheckConstraint("total_tokens = prompt_tokens + completion_tokens"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message(agent={self.agent_name}, role={self.agent_role}, "
            f"latency={self.latency_ms}ms)>"
        )
