"""
Debate Repository

Specialized repository for Debate model operations.

Implements debate-specific queries:
- Get by user
- Get recent debates
- Get by status
- Update status/completion time
- Debate analytics

All operations use the injected AsyncSession.
"""

from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Debate, User, Message, DebateStatus
from app.database.repositories.base_repository import BaseRepository


class DebateRepository(BaseRepository[Debate]):
    """
    Repository for Debate entity operations.

    Provides Debate-specific queries in addition to generic CRUD.

    Example:
        repo = DebateRepository(session)
        debate = await repo.get_by_id(debate_id)
        user_debates = await repo.get_by_user(user_id)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize DebateRepository with AsyncSession.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        super().__init__(Debate, session)

    # ==================== GET DEBATES ====================

    async def get_by_user(self, user_id: UUID) -> List[Debate]:
        """
        Get all debates for a user.

        Args:
            user_id: User UUID

        Returns:
            List of Debate instances

        Example:
            debates = await debate_repo.get_by_user(user_id)
        """
        query = select(Debate).where(Debate.user_id == user_id)
        return await self.get_all(query)

    async def get_by_user_recent(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[Debate]:
        """
        Get recent debates for a user (ordered by created_at DESC).

        Args:
            user_id: User UUID
            limit: Maximum number of debates to return

        Returns:
            List of Debate instances (most recent first)

        Example:
            recent = await debate_repo.get_by_user_recent(user_id, limit=5)
        """
        query = (
            select(Debate)
            .where(Debate.user_id == user_id)
            .order_by(desc(Debate.created_at))
            .limit(limit)
        )
        return await self.get_all(query)

    async def get_by_status(self, status: DebateStatus) -> List[Debate]:
        """
        Get all debates with a specific status.

        Args:
            status: DebateStatus enum value

        Returns:
            List of Debate instances

        Example:
            running = await debate_repo.get_by_status(DebateStatus.RUNNING)
        """
        query = select(Debate).where(Debate.status == status)
        return await self.get_all(query)

    async def get_by_provider(self, provider: str) -> List[Debate]:
        """
        Get all debates that used a specific provider.

        Args:
            provider: Provider name (groq, mistral, etc.)

        Returns:
            List of Debate instances

        Example:
            groq_debates = await debate_repo.get_by_provider("groq")
        """
        query = select(Debate).where(Debate.provider == provider)
        return await self.get_all(query)

    async def get_by_question_type(self, question_type: str) -> List[Debate]:
        """
        Get all debates of a specific question type.

        Args:
            question_type: Question type (factual, reasoning, etc.)

        Returns:
            List of Debate instances

        Example:
            factual = await debate_repo.get_by_question_type("factual")
        """
        query = select(Debate).where(Debate.question_type == question_type)
        return await self.get_all(query)

    async def get_recent(self, limit: int = 10) -> List[Debate]:
        """
        Get most recent debates globally.

        Args:
            limit: Maximum number of debates to return

        Returns:
            List of Debate instances (most recent first)

        Example:
            recent = await debate_repo.get_recent(limit=20)
        """
        query = select(Debate).order_by(desc(Debate.created_at)).limit(limit)
        return await self.get_all(query)

    async def get_with_messages(self, debate_id: UUID) -> Optional[Debate]:
        """
        Get debate with eager-loaded messages to avoid N+1 queries.

        Args:
            debate_id: Debate UUID

        Returns:
            Debate instance with messages loaded, or None if not found

        Example:
            debate = await debate_repo.get_with_messages(debate_id)
            for msg in debate.messages:
                print(msg.agent_name)
        """
        query = (
            select(Debate)
            .where(Debate.id == debate_id)
            .options(selectinload(Debate.messages))
        )
        return await self.get_one(query)

    async def get_with_feedback(self, debate_id: UUID) -> Optional[Debate]:
        """
        Get debate with eager-loaded feedback.

        Args:
            debate_id: Debate UUID

        Returns:
            Debate instance with feedback loaded, or None if not found

        Example:
            debate = await debate_repo.get_with_feedback(debate_id)
            avg_rating = sum(f.rating for f in debate.feedback) / len(debate.feedback)
        """
        query = (
            select(Debate)
            .where(Debate.id == debate_id)
            .options(selectinload(Debate.feedback))
        )
        return await self.get_one(query)

    async def get_with_all_relations(self, debate_id: UUID) -> Optional[Debate]:
        """
        Get debate with all eager-loaded relationships.

        Args:
            debate_id: Debate UUID

        Returns:
            Debate instance with all relationships loaded

        Example:
            debate = await debate_repo.get_with_all_relations(debate_id)
        """
        query = (
            select(Debate)
            .where(Debate.id == debate_id)
            .options(
                selectinload(Debate.user),
                selectinload(Debate.messages),
                selectinload(Debate.feedback),
            )
        )
        return await self.get_one(query)

    # ==================== UPDATE DEBATE ====================

    async def update_status(
        self, 
        debate: Debate, 
        new_status: DebateStatus
    ) -> Debate:
        """
        Update debate status.

        Args:
            debate: Debate instance
            new_status: New DebateStatus

        Returns:
            Updated Debate instance

        Example:
            debate = await debate_repo.update_status(
                debate, 
                DebateStatus.COMPLETED
            )
        """
        return await self.update(debate, status=new_status)

    async def start_debate(self, debate: Debate) -> Debate:
        """
        Mark debate as started (set started_at and status to RUNNING).

        Args:
            debate: Debate instance

        Returns:
            Updated Debate instance

        Example:
            debate = await debate_repo.start_debate(debate)
        """
        return await self.update(
            debate,
            status=DebateStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )

    async def complete_debate(self, debate: Debate) -> Debate:
        """
        Mark debate as completed (set completed_at and status to COMPLETED).

        Args:
            debate: Debate instance

        Returns:
            Updated Debate instance

        Example:
            debate = await debate_repo.complete_debate(debate)
        """
        return await self.update(
            debate,
            status=DebateStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc)
        )

    async def fail_debate(self, debate: Debate) -> Debate:
        """
        Mark debate as failed (status to FAILED, completed_at to now).

        Args:
            debate: Debate instance

        Returns:
            Updated Debate instance

        Example:
            debate = await debate_repo.fail_debate(debate)
        """
        return await self.update(
            debate,
            status=DebateStatus.FAILED,
            completed_at=datetime.now(timezone.utc)
        )

    # ==================== COUNT & ANALYTICS ====================

    async def count_by_status(self, status: DebateStatus) -> int:
        """
        Count debates with a specific status.

        Args:
            status: DebateStatus enum value

        Returns:
            Number of debates with that status

        Example:
            running = await debate_repo.count_by_status(DebateStatus.RUNNING)
        """
        query = select(Debate).where(Debate.status == status)
        return await self.count(query)

    async def count_by_user(self, user_id: UUID) -> int:
        """
        Count debates for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of user's debates

        Example:
            count = await debate_repo.count_by_user(user_id)
        """
        query = select(Debate).where(Debate.user_id == user_id)
        return await self.count(query)

    async def count_by_provider(self, provider: str) -> int:
        """
        Count debates using a specific provider.

        Args:
            provider: Provider name

        Returns:
            Number of debates using that provider

        Example:
            count = await debate_repo.count_by_provider("groq")
        """
        query = select(Debate).where(Debate.provider == provider)
        return await self.count(query)

    # ==================== EXISTENCE CHECKS ====================

    async def has_user_debates(self, user_id: UUID) -> bool:
        """
        Check if user has any debates.

        Args:
            user_id: User UUID

        Returns:
            True if user has debates

        Example:
            has_debates = await debate_repo.has_user_debates(user_id)
        """
        query = select(Debate).where(Debate.user_id == user_id)
        return await self.exists(query)

    async def is_user_debate(self, debate_id: UUID, user_id: UUID) -> bool:
        """
        Check if debate belongs to user.

        Args:
            debate_id: Debate UUID
            user_id: User UUID

        Returns:
            True if debate belongs to user

        Example:
            is_owner = await debate_repo.is_user_debate(debate_id, user_id)
        """
        query = select(Debate).where(
            and_(
                Debate.id == debate_id,
                Debate.user_id == user_id
            )
        )
        return await self.exists(query)
