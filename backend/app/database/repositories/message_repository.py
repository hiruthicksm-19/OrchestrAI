"""
Message Repository

Specialized repository for Message model operations.

Treats Message as an Agent Execution Log (not chat history).
Each Message record = one AI agent execution.

Implements queries for:
- Execution history
- Performance analysis
- Provider analytics
- Cost tracking

All operations use the injected AsyncSession.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Message, AgentRole, ResponseType
from app.database.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message (Agent Execution) operations.

    Messages represent individual AI agent executions, not user chat messages.

    Example:
        repo = MessageRepository(session)
        executions = await repo.get_by_debate(debate_id)
        performance = await repo.get_average_latency_by_provider()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize MessageRepository with AsyncSession.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        super().__init__(Message, session)

    # ==================== GET EXECUTIONS BY DEBATE ====================

    async def get_by_debate(self, debate_id: UUID) -> List[Message]:
        """
        Get all executions for a debate (execution history).

        Args:
            debate_id: Debate UUID

        Returns:
            List of Message instances ordered by created_at

        Example:
            history = await message_repo.get_by_debate(debate_id)
        """
        query = (
            select(Message)
            .where(Message.debate_id == debate_id)
            .order_by(Message.created_at)
        )
        return await self.get_all(query)

    async def get_by_debate_and_round(
        self, 
        debate_id: UUID, 
        round_number: int
    ) -> List[Message]:
        """
        Get all executions in a specific round of a debate.

        Args:
            debate_id: Debate UUID
            round_number: Debate round number

        Returns:
            List of Message instances for that round

        Example:
            round_1 = await message_repo.get_by_debate_and_round(debate_id, 1)
        """
        query = (
            select(Message)
            .where(
                and_(
                    Message.debate_id == debate_id,
                    Message.round_number == round_number
                )
            )
            .order_by(Message.created_at)
        )
        return await self.get_all(query)

    async def get_by_debate_ordered_recent(self, debate_id: UUID) -> List[Message]:
        """
        Get executions for a debate (most recent first).

        Args:
            debate_id: Debate UUID

        Returns:
            List of Message instances ordered by created_at DESC

        Example:
            recent = await message_repo.get_by_debate_ordered_recent(debate_id)
        """
        query = (
            select(Message)
            .where(Message.debate_id == debate_id)
            .order_by(desc(Message.created_at))
        )
        return await self.get_all(query)

    # ==================== GET EXECUTIONS BY AGENT ====================

    async def get_by_agent(self, agent_name: str) -> List[Message]:
        """
        Get all executions by a specific agent.

        Args:
            agent_name: Agent name (e.g., 'research_agent')

        Returns:
            List of Message instances

        Example:
            research = await message_repo.get_by_agent("research_agent")
        """
        query = select(Message).where(Message.agent_name == agent_name)
        return await self.get_all(query)

    async def get_by_agent_role(self, role: AgentRole) -> List[Message]:
        """
        Get all executions by agents with a specific role.

        Args:
            role: AgentRole enum (research, opponent, consensus)

        Returns:
            List of Message instances

        Example:
            research = await message_repo.get_by_agent_role(AgentRole.RESEARCH)
        """
        query = select(Message).where(Message.agent_role == role)
        return await self.get_all(query)

    # ==================== GET EXECUTIONS BY PROVIDER ====================

    async def get_by_provider(self, provider: str) -> List[Message]:
        """
        Get all executions using a specific provider.

        Args:
            provider: Provider name (groq, mistral, openai, cerebras)

        Returns:
            List of Message instances

        Example:
            groq = await message_repo.get_by_provider("groq")
        """
        query = select(Message).where(Message.provider == provider)
        return await self.get_all(query)

    async def get_by_model(self, model: str) -> List[Message]:
        """
        Get all executions using a specific model.

        Args:
            model: Model identifier

        Returns:
            List of Message instances

        Example:
            llama = await message_repo.get_by_model("llama-3.3-70b")
        """
        query = select(Message).where(Message.model == model)
        return await self.get_all(query)

    async def get_by_provider_and_model(
        self, 
        provider: str, 
        model: str
    ) -> List[Message]:
        """
        Get executions for a specific provider and model combination.

        Args:
            provider: Provider name
            model: Model identifier

        Returns:
            List of Message instances

        Example:
            executions = await message_repo.get_by_provider_and_model(
                "groq", 
                "llama-3.3-70b"
            )
        """
        query = select(Message).where(
            and_(
                Message.provider == provider,
                Message.model == model
            )
        )
        return await self.get_all(query)

    # ==================== GET FAILED EXECUTIONS ====================

    async def get_failed(self) -> List[Message]:
        """
        Get all failed executions.

        Returns:
            List of failed Message instances

        Example:
            failures = await message_repo.get_failed()
        """
        query = select(Message).where(Message.success == False)
        return await self.get_all(query)

    async def get_failed_by_debate(self, debate_id: UUID) -> List[Message]:
        """
        Get failed executions for a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            List of failed Message instances

        Example:
            failures = await message_repo.get_failed_by_debate(debate_id)
        """
        query = select(Message).where(
            and_(
                Message.debate_id == debate_id,
                Message.success == False
            )
        )
        return await self.get_all(query)

    # ==================== ANALYTICS ====================

    async def get_average_latency(self) -> float:
        """
        Get average execution latency across all executions.

        Returns:
            Average latency in milliseconds

        Example:
            avg = await message_repo.get_average_latency()
        """
        query = select(func.avg(Message.latency_ms))
        result = await self.session.execute(query)
        return result.scalar() or 0.0

    async def get_average_latency_by_provider(self) -> dict[str, float]:
        """
        Get average latency for each provider.

        Returns:
            Dict mapping provider name to average latency

        Example:
            latencies = await message_repo.get_average_latency_by_provider()
            # {'groq': 245.5, 'mistral': 312.3}
        """
        query = select(
            Message.provider,
            func.avg(Message.latency_ms).label('avg_latency')
        ).group_by(Message.provider)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) for row in result.all()}

    async def get_total_tokens_by_provider(self) -> dict[str, int]:
        """
        Get total tokens used by each provider.

        Returns:
            Dict mapping provider name to total tokens

        Example:
            tokens = await message_repo.get_total_tokens_by_provider()
            # {'groq': 45000, 'mistral': 32000}
        """
        query = select(
            Message.provider,
            func.sum(Message.total_tokens).label('total')
        ).group_by(Message.provider)
        result = await self.session.execute(query)
        return {row[0]: int(row[1]) if row[1] else 0 for row in result.all()}

    async def get_total_cost_by_provider(self) -> dict[str, float]:
        """
        Get total cost for each provider.

        Returns:
            Dict mapping provider name to total cost

        Example:
            costs = await message_repo.get_total_cost_by_provider()
            # {'groq': 1.23, 'mistral': 0.95}
        """
        query = select(
            Message.provider,
            func.sum(Message.cost).label('total')
        ).group_by(Message.provider)
        result = await self.session.execute(query)
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in result.all()}

    async def get_success_rate(self) -> float:
        """
        Get overall execution success rate (0-1).

        Returns:
            Success rate as percentage (0.0 to 1.0)

        Example:
            rate = await message_repo.get_success_rate()
            # 0.95 = 95% success rate
        """
        total = await self.count()
        if total == 0:
            return 0.0

        query = select(Message).where(Message.success == True)
        successful = await self.count(query)
        return successful / total

    async def get_success_rate_by_provider(self) -> dict[str, float]:
        """
        Get success rate for each provider.

        Returns:
            Dict mapping provider name to success rate

        Example:
            rates = await message_repo.get_success_rate_by_provider()
            # {'groq': 0.98, 'mistral': 0.92}
        """
        # Get total count per provider
        total_query = select(
            Message.provider,
            func.count(Message.id).label('total')
        ).group_by(Message.provider)
        total_result = await self.session.execute(total_query)
        totals = {row[0]: int(row[1]) for row in total_result.all()}

        # Get successful count per provider
        success_query = select(
            Message.provider,
            func.count(Message.id).label('success')
        ).where(Message.success == True).group_by(Message.provider)
        success_result = await self.session.execute(success_query)
        successes = {row[0]: int(row[1]) for row in success_result.all()}

        # Calculate rates
        return {
            provider: successes.get(provider, 0) / total
            for provider, total in totals.items()
        }

    # ==================== COUNT & STATISTICS ====================

    async def count_by_debate(self, debate_id: UUID) -> int:
        """
        Count executions in a debate.

        Args:
            debate_id: Debate UUID

        Returns:
            Number of executions

        Example:
            count = await message_repo.count_by_debate(debate_id)
        """
        query = select(Message).where(Message.debate_id == debate_id)
        return await self.count(query)

    async def count_by_agent_role(self, role: AgentRole) -> int:
        """
        Count executions by agent role.

        Args:
            role: AgentRole enum

        Returns:
            Number of executions by that role

        Example:
            count = await message_repo.count_by_agent_role(AgentRole.RESEARCH)
        """
        query = select(Message).where(Message.agent_role == role)
        return await self.count(query)

    async def count_by_provider(self, provider: str) -> int:
        """
        Count executions by provider.

        Args:
            provider: Provider name

        Returns:
            Number of executions by that provider

        Example:
            count = await message_repo.count_by_provider("groq")
        """
        query = select(Message).where(Message.provider == provider)
        return await self.count(query)

    async def count_failed(self) -> int:
        """
        Count failed executions.

        Returns:
            Number of failed executions

        Example:
            count = await message_repo.count_failed()
        """
        query = select(Message).where(Message.success == False)
        return await self.count(query)
