"""
User Model

Represents users of the DebateAI platform.

Fields:
- id: UUID primary key
- username: Unique username
- email: Unique email address
- is_active: Whether the user account is active
- created_at: Account creation timestamp
- updated_at: Last profile update timestamp

Relationships:
- debates: All debates created by this user

Future Extensions:
- password_hash (authentication in Phase 3)
- api_keys (API access)
- settings (user preferences)
- organization (team support)
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.database.models.debate import Debate


class User(BaseModel):
    """User account in the DebateAI system."""

    __tablename__ = "users"

    # Unique fields
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for login",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address",
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the account is active",
    )

    # Relationships
    debates: Mapped[list["Debate"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        doc="All debates created by this user",
    )

    # Constraints
    __table_args__ = (
        Index("idx_user_created_at", "created_at"),
        Index("idx_user_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email})>"
