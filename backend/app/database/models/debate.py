"""
Debate Model

Central entity representing a complete debate orchestration session.

A Debate orchestrates multiple AI agents debating a question and recording
the entire execution lifecycle.

Fields:
- id: UUID primary key
- user_id: Reference to user who created the debate
- title: Optional custom title for the debate
- question: The question being debated
- question_type: Classification of the question
- strategy: Debate strategy used
- status: Current state of the debate
- provider: Primary provider used
- model: Primary model used
- started_at: When debate execution started
- completed_at: When debate execution completed
- created_at: When record was created
- updated_at: When record was last updated

Relationships:
- user: User who created this debate
- messages: All agent executions (messages)
- feedback: User feedback on this debate

Indexes:
- status (for filtering by state)
- created_at (for sorting/range queries)
- user_id (for user's debate history)
- provider (for provider analytics)
- question_type (for question type analysis)
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Enum,
    DateTime,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base_model import BaseModel
from app.database.models.enums import DebateStatus, QuestionType

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.message import Message
    from app.database.models.feedback import Feedback


class Debate(BaseModel):
    """Central debate orchestration record."""

    __tablename__ = "debates"

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who created this debate",
    )

    # Core fields
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional custom title for the debate",
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="The question being debated",
    )

    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType),
        nullable=False,
        index=True,
        doc="Classification of the question",
    )

    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Debate strategy used (e.g., 'simple', 'adversarial')",
    )

    # Status tracking
    status: Mapped[DebateStatus] = mapped_column(
        Enum(DebateStatus),
        default=DebateStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current status of the debate",
    )

    # Provider and model tracking
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Primary provider used",
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Primary model used",
    )

    # Execution timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When debate execution started",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When debate execution completed",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="debates",
        lazy="select",
        doc="User who created this debate",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="debate",
        cascade="all, delete-orphan",
        lazy="select",
        doc="All agent executions (messages) in this debate",
    )

    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="debate",
        cascade="all, delete-orphan",
        lazy="select",
        doc="User feedback on this debate",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_debate_status", "status"),
        Index("idx_debate_created_at", "created_at"),
        Index("idx_debate_user_id", "user_id"),
        Index("idx_debate_provider", "provider"),
        Index("idx_debate_question_type", "question_type"),
        Index("idx_debate_user_created", "user_id", "created_at"),
        CheckConstraint("started_at <= completed_at OR completed_at IS NULL"),
    )

    def __repr__(self) -> str:
        return f"<Debate(question={self.question[:50]}, status={self.status})>"
