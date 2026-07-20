"""
Feedback Repository

Specialized repository for Feedback model operations.

Implements user feedback queries:
- Get feedback by debate
- Rating analysis
- Average ratings

All operations use the injected AsyncSession.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Feedback
from app.database.repositories.base_repository import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    """
    Repository for Feedback entity operations.

    Provides Feedback-specific queries for ratings and comments.

    Example:
        repo = FeedbackRepository(session)
        feedback_list = await repo.get_by_debate(debate_id)
        avg_rating = await repo.get_average_rating()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize FeedbackRepository with AsyncSession.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        super().__init__(Feedback, session)

    # ==================== GET FEEDBACK ====================

    async def get_by_debate(self, debate_id: UUID) -> List[Feedback]:
        """
        Get all feedback for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            List of Feedback instances

        Example:
            feedback = await feedback_repo.get_by_debate(debate_id)
        """
        query = select(Feedback).where(Feedback.debate_id == debate_id)
        return await self.get_all(query)

    async def get_by_rating(self, rating: int) -> List[Feedback]:
        """
        Get all feedback with a specific rating.

        Args:
            rating: Rating value (1-5)

        Returns:
            List of Feedback instances

        Raises:
            ValueError: If rating not in 1-5 range

        Example:
            five_stars = await feedback_repo.get_by_rating(5)
        """
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        query = select(Feedback).where(Feedback.rating == rating)
        return await self.get_all(query)

    async def get_high_rated(self, min_rating: int = 4) -> List[Feedback]:
        """
        Get feedback with rating >= min_rating.

        Args:
            min_rating: Minimum rating to include (default: 4)

        Returns:
            List of Feedback instances

        Example:
            positive = await feedback_repo.get_high_rated(min_rating=4)
        """
        query = select(Feedback).where(Feedback.rating >= min_rating)
        return await self.get_all(query)

    async def get_low_rated(self, max_rating: int = 2) -> List[Feedback]:
        """
        Get feedback with rating <= max_rating.

        Args:
            max_rating: Maximum rating to include (default: 2)

        Returns:
            List of Feedback instances

        Example:
            negative = await feedback_repo.get_low_rated(max_rating=2)
        """
        query = select(Feedback).where(Feedback.rating <= max_rating)
        return await self.get_all(query)

    async def get_with_comments(self) -> List[Feedback]:
        """
        Get feedback that has comments (non-null).

        Returns:
            List of Feedback instances with comments

        Example:
            with_comments = await feedback_repo.get_with_comments()
        """
        query = select(Feedback).where(Feedback.comment.isnot(None))
        return await self.get_all(query)

    async def get_with_comments_by_debate(self, debate_id: UUID) -> List[Feedback]:
        """
        Get feedback with comments for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            List of Feedback instances with comments

        Example:
            comments = await feedback_repo.get_with_comments_by_debate(debate_id)
        """
        query = select(Feedback).where(
            Feedback.debate_id == debate_id,
            Feedback.comment.isnot(None)
        )
        return await self.get_all(query)

    # ==================== RATING ANALYSIS ====================

    async def get_average_rating(self) -> float:
        """
        Get average rating across all feedback.

        Returns:
            Average rating (0.0 if no feedback)

        Example:
            avg = await feedback_repo.get_average_rating()
        """
        query = select(func.avg(Feedback.rating))
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    async def get_average_rating_by_debate(self, debate_id: UUID) -> float:
        """
        Get average rating for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            Average rating (0.0 if no feedback)

        Example:
            avg = await feedback_repo.get_average_rating_by_debate(debate_id)
        """
        query = select(func.avg(Feedback.rating)).where(
            Feedback.debate_id == debate_id
        )
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    async def get_rating_distribution(self) -> dict[int, int]:
        """
        Get count of feedback for each rating (1-5).

        Returns:
            Dict mapping rating to count

        Example:
            dist = await feedback_repo.get_rating_distribution()
            # {1: 10, 2: 5, 3: 20, 4: 50, 5: 100}
        """
        query = select(
            Feedback.rating,
            func.count(Feedback.id).label('count')
        ).group_by(Feedback.rating)
        result = await self.session.execute(query)
        
        # Initialize with zeros for all ratings 1-5
        distribution = {i: 0 for i in range(1, 6)}
        for row in result.all():
            distribution[row[0]] = int(row[1])
        
        return distribution

    async def get_rating_distribution_by_debate(
        self, 
        debate_id: UUID
    ) -> dict[int, int]:
        """
        Get rating distribution for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            Dict mapping rating to count

        Example:
            dist = await feedback_repo.get_rating_distribution_by_debate(debate_id)
        """
        query = select(
            Feedback.rating,
            func.count(Feedback.id).label('count')
        ).where(
            Feedback.debate_id == debate_id
        ).group_by(Feedback.rating)
        result = await self.session.execute(query)
        
        # Initialize with zeros for all ratings 1-5
        distribution = {i: 0 for i in range(1, 6)}
        for row in result.all():
            distribution[row[0]] = int(row[1])
        
        return distribution

    # ==================== COUNT & STATISTICS ====================

    async def count_by_debate(self, debate_id: UUID) -> int:
        """
        Count feedback for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            Number of feedback entries

        Example:
            count = await feedback_repo.count_by_debate(debate_id)
        """
        query = select(Feedback).where(Feedback.debate_id == debate_id)
        return await self.count(query)

    async def count_by_rating(self, rating: int) -> int:
        """
        Count feedback with a specific rating.

        Args:
            rating: Rating value (1-5)

        Returns:
            Number of feedback entries with that rating

        Example:
            count = await feedback_repo.count_by_rating(5)
        """
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        query = select(Feedback).where(Feedback.rating == rating)
        return await self.count(query)

    async def count_high_rated(self, min_rating: int = 4) -> int:
        """
        Count high-rated feedback.

        Args:
            min_rating: Minimum rating (default: 4)

        Returns:
            Number of feedback with rating >= min_rating

        Example:
            count = await feedback_repo.count_high_rated()
        """
        query = select(Feedback).where(Feedback.rating >= min_rating)
        return await self.count(query)

    async def count_low_rated(self, max_rating: int = 2) -> int:
        """
        Count low-rated feedback.

        Args:
            max_rating: Maximum rating (default: 2)

        Returns:
            Number of feedback with rating <= max_rating

        Example:
            count = await feedback_repo.count_low_rated()
        """
        query = select(Feedback).where(Feedback.rating <= max_rating)
        return await self.count(query)

    async def count_with_comments(self) -> int:
        """
        Count feedback with comments.

        Returns:
            Number of feedback entries with comments

        Example:
            count = await feedback_repo.count_with_comments()
        """
        query = select(Feedback).where(Feedback.comment.isnot(None))
        return await self.count(query)

    # ==================== EXISTENCE CHECKS ====================

    async def has_feedback(self, debate_id: UUID) -> bool:
        """
        Check if a debate has any feedback.

        Args:
            debate_id: Debate UUID

        Returns:
            True if debate has feedback

        Example:
            has = await feedback_repo.has_feedback(debate_id)
        """
        query = select(Feedback).where(Feedback.debate_id == debate_id)
        return await self.exists(query)

    async def has_rated(self, debate_id: UUID, rating: int) -> bool:
        """
        Check if a debate has feedback with a specific rating.

        Args:
            debate_id: Debate UUID
            rating: Rating to check

        Returns:
            True if debate has feedback with that rating

        Example:
            has_five = await feedback_repo.has_rated(debate_id, 5)
        """
        query = select(Feedback).where(
            Feedback.debate_id == debate_id,
            Feedback.rating == rating
        )
        return await self.exists(query)
