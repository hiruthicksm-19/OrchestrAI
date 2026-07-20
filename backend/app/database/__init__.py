"""
Database Layer

Contains all database-related functionality:
- Connection management (session.py)
- ORM models (models/)
- Repository Layer (repositories/)

Exports:
- Base: Declarative base for models
- Models: All ORM models
- Repositories: All repository classes
- Session: Connection and dependency management

Key Components:

1. Connection Management (session.py)
   - Async SQLAlchemy engine with connection pooling
   - AsyncSession factory for session creation
   - FastAPI dependency injection (get_db)
   - Health check capabilities

2. ORM Models (models/)
   - BaseModel: Abstract base with UUID and timestamps
   - User: User accounts
   - Debate: Debate orchestration
   - Message: Agent execution records
   - Feedback: User ratings
   - APIUsage: Provider analytics

3. Repositories (repositories/)
   - BaseRepository: Generic CRUD base class
   - UserRepository: User data access
   - DebateRepository: Debate data access
   - MessageRepository: Agent execution data access
   - FeedbackRepository: Feedback data access
   - APIUsageRepository: API usage analytics

Typical Usage:

    from app.database import get_db
    from app.database.repositories import DebateRepository, MessageRepository

    async def get_debate_details(debate_id: UUID, session = Depends(get_db)):
        # Create repositories with injected session
        debate_repo = DebateRepository(session)
        message_repo = MessageRepository(session)

        # Use repositories for database access
        debate = await debate_repo.get_with_messages(debate_id)
        messages = await message_repo.get_by_debate(debate_id)

        return {"debate": debate, "messages": messages}

Architecture:

    FastAPI Routes
        ↓
    Services (future)
        ↓
    Repositories ← ← ← Only databases access
        ↓
    SQLAlchemy ORM
        ↓
    PostgreSQL
"""

from app.database.base import Base
from app.database.session import (
    get_db,
    initialize_db,
    close_db,
    get_db_health,
    get_session_factory,
)
from app.database.models import (
    BaseModel,
    DebateStatus,
    QuestionType,
    AgentRole,
    ResponseType,
    User,
    Debate,
    Message,
    Feedback,
    APIUsage,
)
from app.database.repositories import (
    BaseRepository,
    UserRepository,
    DebateRepository,
    MessageRepository,
    FeedbackRepository,
    APIUsageRepository,
)

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # Session management
    "get_db",
    "initialize_db",
    "close_db",
    "get_db_health",
    "get_session_factory",
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
    # Repositories
    "BaseRepository",
    "UserRepository",
    "DebateRepository",
    "MessageRepository",
    "FeedbackRepository",
    "APIUsageRepository",
]
