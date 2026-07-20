"""
Repository Layer

This module provides the complete Repository Pattern implementation for database access.

Repositories act as a data access abstraction layer between the application
and the database. All database queries should flow through repositories.

Architecture:
- BaseRepository: Generic base class with common CRUD operations
- UserRepository: User-specific queries
- DebateRepository: Debate orchestration queries
- MessageRepository: Agent execution log queries
- FeedbackRepository: User feedback queries
- APIUsageRepository: Provider analytics queries

Key Principles:
1. Single Responsibility: Each repository handles one entity
2. Dependency Injection: AsyncSession is injected (never created)
3. Clean Queries: SQLAlchemy 2.x select statements (no raw SQL)
4. Type Safety: Full type hints throughout
5. No Business Logic: Repositories only do database operations
6. No Session Management: Sessions handled by application

Usage Pattern:
    # Create repositories (typically in a service or route)
    debate_repo = DebateRepository(session)
    message_repo = MessageRepository(session)
    user_repo = UserRepository(session)

    # Use repositories for database operations
    debate = await debate_repo.get_by_id(debate_id)
    messages = await message_repo.get_by_debate(debate_id)
    await debate_repo.update_status(debate, DebateStatus.COMPLETED)

Future Enhancements:
- Pagination (offset/limit)
- Filtering (filter builder)
- Sorting (dynamic sort)
- Soft deletes (deleted_at field)
- Audit logging (who changed what)
- Caching layer
- Bulk operations
"""

from app.database.repositories.base_repository import BaseRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.debate_repository import DebateRepository
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.feedback_repository import FeedbackRepository
from app.database.repositories.api_usage_repository import APIUsageRepository

__all__ = [
    # Base
    "BaseRepository",
    # Implementations
    "UserRepository",
    "DebateRepository",
    "MessageRepository",
    "FeedbackRepository",
    "APIUsageRepository",
]
