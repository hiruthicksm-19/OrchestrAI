"""
Feedback Model

User feedback on a completed debate.

Allows users to rate and comment on debate results for:
- Quality metrics
- User satisfaction tracking
- Model comparison
- Continuous improvement

Fields:
- id: UUID primary key
- debate_id: Reference to debate
- rating: User rating (1-5)
- comment: Optional detailed feedback
- created_at: When feedback was provided
- updated_at: When feedback was last updated

Relationships:
- debate: The debate being rated
"""

from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, ForeignKey, Integer, Text, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.database.models.debate import Debate


class Feedback(BaseModel):
    """User feedback on a debate."""

    __tablename__ = "feedback"

    # Foreign keys
    debate_id: Mapped[UUID] = mapped_column(
        ForeignKey("debates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The debate being rated",
    )

    # Rating
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="User rating (1-5 stars)",
    )

    # Optional comment
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional detailed feedback",
    )

    # Relationships
    debate: Mapped["Debate"] = relationship(
        back_populates="feedback",
        lazy="select",
        doc="The debate being rated",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_feedback_debate_id", "debate_id"),
        Index("idx_feedback_rating", "rating"),
        Index("idx_feedback_created_at", "created_at"),
        CheckConstraint("rating >= 1 AND rating <= 5"),
    )

    def __repr__(self) -> str:
        return f"<Feedback(debate={self.debate_id}, rating={self.rating})>"
