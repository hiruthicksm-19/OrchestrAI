"""
Database Models

This package contains all SQLAlchemy ORM models.

Models are organized by entity:
- base_model.py - Abstract base with UUID and timestamps
- enums.py - Enumerated types
- user.py - User accounts
- debate.py - Central debate records
- message.py - Agent execution records
- feedback.py - User feedback
- api_usage.py - API usage tracking

Model Relationships:
    User (1) ──────── (∞) Debate
             ├──────── (∞) Message
             └──────── (∞) Feedback

All models use:
- UUID primary keys
- Automatic timestamps (created_at, updated_at)
- Type-safe Enum fields
- Comprehensive indexes
- Check constraints
- Foreign keys with cascade delete

For Alembic auto-migrations:
    alembic revision --autogenerate -m "Description"
    alembic upgrade head
"""

from app.database.models.enums import (
    DebateStatus,
    QuestionType,
    AgentRole,
    ResponseType,
)
from app.database.models.base_model import BaseModel
from app.database.models.user import User
from app.database.models.debate import Debate
from app.database.models.message import Message
from app.database.models.feedback import Feedback
from app.database.models.api_usage import APIUsage

__all__ = [
    # Base
    "BaseModel",
    # Enums
    "DebateStatus",
    "QuestionType",
    "AgentRole",
    "ResponseType",
    # Models
    "User",
    "Debate",
    "Message",
    "Feedback",
    "APIUsage",
]

