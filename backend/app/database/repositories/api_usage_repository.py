"""
API Usage Repository

Specialized repository for APIUsage model operations.

Implements provider analytics queries:
- Usage by provider/model
- Cost tracking
- Token usage
- Performance metrics

All operations use the injected AsyncSession.
"""

from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import APIUsage
from app.database.repositories.base_repository import BaseRepository


class APIUsageRepository(BaseRepository[APIUsage]):
    """
    Repository for APIUsage (provider analytics) operations.

    Provides provider tracking, cost analysis, and performance metrics.

    Example:
        repo = APIUsageRepository(session)
        total_cost = await repo.get_total_cost()
        by_provider = await repo.get_usage_by_provider()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize APIUsageRepository with AsyncSession.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        super().__init__(APIUsage, session)

    # ==================== GET USAGE ====================

    async def get_by_provider(self, provider: str) -> List[APIUsage]:
        """
        Get all usage records for a provider.

        Args:
            provider: Provider name (groq, mistral, openai, cerebras)

        Returns:
            List of APIUsage instances

        Example:
            groq_usage = await usage_repo.get_by_provider("groq")
        """
        query = select(APIUsage).where(APIUsage.provider == provider)
        return await self.get_all(query)

    async def get_by_model(self, model: str) -> List[APIUsage]:
        """
        Get all usage records for a model.

        Args:
            model: Model identifier

        Returns:
            List of APIUsage instances

        Example:
            llama_usage = await usage_repo.get_by_model("llama-3.3-70b")
        """
        query = select(APIUsage).where(APIUsage.model == model)
        return await self.get_all(query)

    async def get_by_provider_and_model(
        self, 
        provider: str, 
        model: str
    ) -> List[APIUsage]:
        """
        Get usage records for a specific provider-model combination.

        Args:
            provider: Provider name
            model: Model identifier

        Returns:
            List of APIUsage instances

        Example:
            usage = await usage_repo.get_by_provider_and_model(
                "groq",
                "llama-3.3-70b"
            )
        """
        query = select(APIUsage).where(
            APIUsage.provider == provider,
            APIUsage.model == model
        )
        return await self.get_all(query)

    async def get_failed(self) -> List[APIUsage]:
        """
        Get all failed API calls.

        Returns:
            List of APIUsage instances with success=False

        Example:
            failures = await usage_repo.get_failed()
        """
        query = select(APIUsage).where(APIUsage.success == False)
        return await self.get_all(query)

    async def get_successful(self) -> List[APIUsage]:
        """
        Get all successful API calls.

        Returns:
            List of APIUsage instances with success=True

        Example:
            successful = await usage_repo.get_successful()
        """
        query = select(APIUsage).where(APIUsage.success == True)
        return await self.get_all(query)

    # ==================== COST ANALYSIS ====================

    async def get_total_cost(self) -> float:
        """
        Get total cost across all API calls.

        Returns:
            Total cost in dollars

        Example:
            total = await usage_repo.get_total_cost()
        """
        query = select(func.sum(APIUsage.cost))
        result = await self.session.execute(query)
        total = result.scalar()
        return float(total) if total else 0.0

    async def get_total_cost_by_provider(self) -> dict[str, float]:
        """
        Get total cost for each provider.

        Returns:
            Dict mapping provider name to total cost

        Example:
            costs = await usage_repo.get_total_cost_by_provider()
            # {'groq': 10.50, 'mistral': 5.25}
        """
        query = select(
            APIUsage.provider,
            func.sum(APIUsage.cost).label('total')
        ).group_by(APIUsage.provider)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in result.all()}

    async def get_total_cost_by_model(self) -> dict[str, float]:
        """
        Get total cost for each model.

        Returns:
            Dict mapping model name to total cost

        Example:
            costs = await usage_repo.get_total_cost_by_model()
            # {'llama-3.3-70b': 8.75, 'mistral-large': 3.50}
        """
        query = select(
            APIUsage.model,
            func.sum(APIUsage.cost).label('total')
        ).group_by(APIUsage.model)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in result.all()}

    async def get_average_cost(self) -> float:
        """
        Get average cost per API call.

        Returns:
            Average cost in dollars

        Example:
            avg = await usage_repo.get_average_cost()
        """
        query = select(func.avg(APIUsage.cost))
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    async def get_average_cost_by_provider(self) -> dict[str, float]:
        """
        Get average cost per call for each provider.

        Returns:
            Dict mapping provider to average cost

        Example:
            avg = await usage_repo.get_average_cost_by_provider()
        """
        query = select(
            APIUsage.provider,
            func.avg(APIUsage.cost).label('avg')
        ).group_by(APIUsage.provider)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in result.all()}

    # ==================== TOKEN ANALYSIS ====================

    async def get_total_tokens(self) -> int:
        """
        Get total tokens used across all API calls.

        Returns:
            Total token count

        Example:
            total = await usage_repo.get_total_tokens()
        """
        query = select(func.sum(APIUsage.tokens))
        result = await self.session.execute(query)
        total = result.scalar()
        return int(total) if total else 0

    async def get_total_tokens_by_provider(self) -> dict[str, int]:
        """
        Get total tokens used by each provider.

        Returns:
            Dict mapping provider to total tokens

        Example:
            tokens = await usage_repo.get_total_tokens_by_provider()
            # {'groq': 45000, 'mistral': 32000}
        """
        query = select(
            APIUsage.provider,
            func.sum(APIUsage.tokens).label('total')
        ).group_by(APIUsage.provider)
        result = await self.session.execute(query)
        return {row[0]: int(row[1]) if row[1] else 0 for row in result.all()}

    async def get_total_tokens_by_model(self) -> dict[str, int]:
        """
        Get total tokens used by each model.

        Returns:
            Dict mapping model to total tokens

        Example:
            tokens = await usage_repo.get_total_tokens_by_model()
        """
        query = select(
            APIUsage.model,
            func.sum(APIUsage.tokens).label('total')
        ).group_by(APIUsage.model)
        result = await self.session.execute(query)
        return {row[0]: int(row[1]) if row[1] else 0 for row in result.all()}

    async def get_average_tokens(self) -> float:
        """
        Get average tokens per API call.

        Returns:
            Average token count

        Example:
            avg = await usage_repo.get_average_tokens()
        """
        query = select(func.avg(APIUsage.tokens))
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    # ==================== PERFORMANCE ANALYSIS ====================

    async def get_average_latency(self) -> float:
        """
        Get average API call latency.

        Returns:
            Average latency in milliseconds

        Example:
            avg = await usage_repo.get_average_latency()
        """
        query = select(func.avg(APIUsage.latency_ms))
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0

    async def get_average_latency_by_provider(self) -> dict[str, float]:
        """
        Get average latency for each provider.

        Returns:
            Dict mapping provider to average latency

        Example:
            latency = await usage_repo.get_average_latency_by_provider()
            # {'groq': 245.5, 'mistral': 312.3}
        """
        query = select(
            APIUsage.provider,
            func.avg(APIUsage.latency_ms).label('avg')
        ).group_by(APIUsage.provider)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in result.all()}

    async def get_success_rate(self) -> float:
        """
        Get overall API success rate (0-1).

        Returns:
            Success rate as decimal (0.0 to 1.0)

        Example:
            rate = await usage_repo.get_success_rate()
            # 0.98 = 98% success rate
        """
        total = await self.count()
        if total == 0:
            return 0.0

        query = select(APIUsage).where(APIUsage.success == True)
        successful = await self.count(query)
        return successful / total

    async def get_success_rate_by_provider(self) -> dict[str, float]:
        """
        Get success rate for each provider.

        Returns:
            Dict mapping provider to success rate

        Example:
            rates = await usage_repo.get_success_rate_by_provider()
            # {'groq': 0.99, 'mistral': 0.95}
        """
        # Get total count per provider
        total_query = select(
            APIUsage.provider,
            func.count(APIUsage.id).label('total')
        ).group_by(APIUsage.provider)
        total_result = await self.session.execute(total_query)
        totals = {row[0]: int(row[1]) for row in total_result.all()}

        # Get successful count per provider
        success_query = select(
            APIUsage.provider,
            func.count(APIUsage.id).label('success')
        ).where(APIUsage.success == True).group_by(APIUsage.provider)
        success_result = await self.session.execute(success_query)
        successes = {row[0]: int(row[1]) for row in success_result.all()}

        # Calculate rates
        return {
            provider: successes.get(provider, 0) / total
            for provider, total in totals.items()
        }

    # ==================== COUNT & STATISTICS ====================

    async def count_by_provider(self, provider: str) -> int:
        """
        Count API calls for a provider.

        Args:
            provider: Provider name

        Returns:
            Number of calls

        Example:
            count = await usage_repo.count_by_provider("groq")
        """
        query = select(APIUsage).where(APIUsage.provider == provider)
        return await self.count(query)

    async def count_by_model(self, model: str) -> int:
        """
        Count API calls for a model.

        Args:
            model: Model identifier

        Returns:
            Number of calls

        Example:
            count = await usage_repo.count_by_model("llama-3.3-70b")
        """
        query = select(APIUsage).where(APIUsage.model == model)
        return await self.count(query)

    async def count_failed(self) -> int:
        """
        Count failed API calls.

        Returns:
            Number of failed calls

        Example:
            count = await usage_repo.count_failed()
        """
        query = select(APIUsage).where(APIUsage.success == False)
        return await self.count(query)

    async def count_successful(self) -> int:
        """
        Count successful API calls.

        Returns:
            Number of successful calls

        Example:
            count = await usage_repo.count_successful()
        """
        query = select(APIUsage).where(APIUsage.success == True)
        return await self.count(query)
