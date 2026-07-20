"""
Debate Service

Orchestration layer between API routes and business logic.

Responsibilities:
- Business rule validation
- Debate Engine orchestration
- Repository coordination
- Result formatting
- Error handling

Design:
- Thin routes delegate to services
- Services contain business logic
- No SQLAlchemy queries (uses repositories)
- No direct HTTP concerns
- Testable in isolation
"""

from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as phase2_settings
from app.core.settings import settings as phase1_settings
from app.core.constants import SUPPORTED_PROVIDERS, DEBATE_STRATEGIES
from app.database.models import (
    User,
    Debate,
    Message,
    DebateStatus,
    QuestionType,
    AgentRole,
    ResponseType,
)
from app.database.repositories import (
    DebateRepository,
    MessageRepository,
    UserRepository,
)
from app.debate.debate_engine import DebateEngine
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DebateService:
    """
    Service layer for debate operations.

    Coordinates between API routes, repositories, and business logic.

    Example:
        service = DebateService(session)
        debate_response = await service.create_debate(
            question="Is AI dangerous?",
            provider="groq"
        )
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize DebateService with database session.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        self.session = session
        self.debate_repo = DebateRepository(session)
        self.message_repo = MessageRepository(session)
        self.user_repo = UserRepository(session)

    # ==================== DEBATE CREATION ====================

    async def create_debate(
        self,
        question: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        strategy: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Create and execute a debate.

        This is the main orchestration method that:
        1. Validates inputs
        2. Creates debate record
        3. Executes debate engine
        4. Stores agent executions
        5. Updates debate status
        6. Returns formatted response

        Args:
            question: The question to debate
            provider: AI provider (uses default if not specified)
            model: Model identifier (uses default if not specified)
            strategy: Debate strategy (uses default if not specified)
            user_id: Optional user ID (for multi-user support)

        Returns:
            Formatted debate response dict

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If debate execution fails

        Example:
            result = await service.create_debate(
                question="Is AI dangerous?",
                provider="groq"
            )
        """
        logger.info(f"Creating debate: question='{question[:50]}...'")

        # Validate inputs
        self._validate_create_debate_inputs(question, provider, model, strategy)

        # Use defaults if not specified
        provider = provider or phase2_settings.ai.provider
        model = model or phase2_settings.ai.default_model
        strategy = strategy or "simple"

        # Create debate record
        debate = await self.debate_repo.create(
            user_id=user_id or UUID('00000000-0000-0000-0000-000000000000'),  # Anonymous user
            question=question,
            question_type=self._classify_question(question),
            strategy=strategy,
            status=DebateStatus.PENDING,
            provider=provider,
            model=model,
        )

        logger.info(f"Debate created: id={debate.id}")

        # Start debate execution
        try:
            debate = await self.debate_repo.start_debate(debate)
            await self.session.flush()

            # Execute debate engine
            logger.info(f"Starting debate execution: id={debate.id}")
            start_time = datetime.now(timezone.utc)

            try:
                debate_result = await self._execute_debate(
                    debate_id=debate.id,
                    question=question,
                    provider=provider,
                    model=model,
                    strategy=strategy,
                )
            except Exception as exec_error:
                logger.error(f"Debate execution error: {exec_error}", exc_info=True)
                raise

            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Mark debate as completed
            debate = await self.debate_repo.complete_debate(debate)
            await self.session.flush()

            logger.info(f"Debate completed: id={debate.id}, time={execution_time_ms}ms")

            # Get full debate with messages
            debate = await self.debate_repo.get_with_messages(debate.id)

            # Return formatted response
            return self._format_debate_response(
                debate=debate,
                execution_time_ms=execution_time_ms,
                final_answer=debate_result.get("consensus"),
            )

        except Exception as e:
            logger.error(f"Debate execution failed: {e}")
            debate = await self.debate_repo.fail_debate(debate)
            await self.session.flush()
            await self.session.commit()
            raise RuntimeError(f"Debate execution failed: {str(e)}")

    # ==================== DEBATE EXECUTION ====================

    async def _execute_debate(
        self,
        debate_id: UUID,
        question: str,
        provider: str,
        model: str,
        strategy: str,
    ) -> dict:
        """
        Execute debate engine and store results.

        Args:
            debate_id: ID of debate being executed
            question: Question to debate
            provider: Provider to use
            model: Model to use
            strategy: Strategy to use

        Returns:
            Debate result with consensus answer

        Raises:
            RuntimeError: If debate engine fails
        """
        try:
            # Create debate engine with Phase 1 settings
            engine = DebateEngine(settings=phase1_settings)

            # Execute debate (Phase 1 logic)
            debate_result = await engine.run(question)

            # Store executions from debate state
            await self._store_debate_executions(
                debate_id=debate_id,
                debate_state=debate_result.state,
                provider=provider,
                model=model,
            )

            return {
                "consensus": debate_result.consensus,
                "final_answer": debate_result.consensus,
            }

        except Exception as e:
            logger.error(f"Debate engine execution failed: {e}")
            raise

    async def _store_debate_executions(
        self,
        debate_id: UUID,
        debate_state,
        provider: str,
        model: str,
    ) -> None:
        """
        Store agent executions from debate state.

        Args:
            debate_id: Debate ID
            debate_state: DebateState with messages
            provider: Provider used
            model: Model used
        """
        if not debate_state or not debate_state.messages:
            return

        for message in debate_state.messages:
            # Map debate_state ResponseType to database ResponseType
            response_type_map = {
                "opening": ResponseType.INITIAL,
                "rebuttal": ResponseType.REBUTTAL,
                "consensus": ResponseType.CONSENSUS,
            }
            db_response_type = response_type_map.get(message.response_type.value, ResponseType.INITIAL)

            # Map agent role string to database AgentRole enum
            role_map = {
                "research": AgentRole.RESEARCH,
                "opponent": AgentRole.OPPONENT,
                "consensus": AgentRole.CONSENSUS,
            }
            agent_role = role_map.get(message.role, AgentRole.RESEARCH)

            await self.message_repo.create(
                debate_id=debate_id,
                agent_name=message.agent_name,
                agent_role=agent_role,
                provider=message.provider or provider,
                model=message.model or model,
                round_number=message.round,
                response_type=db_response_type,
                content=message.content,
                latency_ms=int(message.latency_ms or 0),
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=message.token_usage or 0,
                cost=0.0,
                success=True,
            )

        await self.session.flush()

    # ==================== DEBATE RETRIEVAL ====================

    async def get_debate(self, debate_id: UUID) -> dict:
        """
        Get a specific debate with all details.

        Args:
            debate_id: ID of debate to retrieve

        Returns:
            Formatted debate response

        Raises:
            ValueError: If debate not found
        """
        debate = await self.debate_repo.get_with_all_relations(debate_id)

        if not debate:
            raise ValueError(f"Debate not found: {debate_id}")

        logger.info(f"Retrieved debate: id={debate_id}")

        # Calculate execution time
        execution_time_ms = None
        if debate.started_at and debate.completed_at:
            execution_time_ms = int(
                (debate.completed_at - debate.started_at).total_seconds() * 1000
            )

        return self._format_debate_response(
            debate=debate,
            execution_time_ms=execution_time_ms,
        )

    async def list_debates(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> dict:
        """
        List debates with pagination and filtering.

        Args:
            skip: Number of debates to skip
            limit: Number of debates to return
            status: Filter by status
            provider: Filter by provider

        Returns:
            Paginated list of debates

        Example:
            result = await service.list_debates(
                skip=0,
                limit=20,
                status="completed"
            )
        """
        # Get filtered debates
        if status:
            debates = await self.debate_repo.get_by_status(status)
        elif provider:
            debates = await self.debate_repo.get_by_provider(provider)
        else:
            debates = await self.debate_repo.get_recent(limit=100)

        # Apply pagination
        total = len(debates)
        debates_paginated = debates[skip : skip + limit]

        # Format responses
        formatted_debates = [
            self._format_debate_summary(d) for d in debates_paginated
        ]

        logger.info(f"Listed {len(formatted_debates)} debates (total: {total})")

        return {
            "debates": formatted_debates,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    # ==================== DEBATE DELETION ====================

    async def delete_debate(self, debate_id: UUID) -> bool:
        """
        Delete a debate.

        Args:
            debate_id: ID of debate to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If debate not found
        """
        deleted = await self.debate_repo.delete_by_id(debate_id)

        if not deleted:
            raise ValueError(f"Debate not found: {debate_id}")

        await self.session.commit()
        logger.info(f"Deleted debate: id={debate_id}")

        return True

    # ==================== FORMATTING ====================

    def _format_debate_response(
        self,
        debate: Debate,
        execution_time_ms: Optional[int] = None,
        final_answer: Optional[str] = None,
    ) -> dict:
        """
        Format Debate object into API response.

        Args:
            debate: Debate model instance
            execution_time_ms: Optional execution time
            final_answer: Optional final consensus answer

        Returns:
            Formatted debate response dict
        """
        messages = [
            {
                "id": str(msg.id),
                "debate_id": str(msg.debate_id),
                "agent_name": msg.agent_name,
                "agent_role": msg.agent_role.value,
                "round_number": msg.round_number,
                "response_type": msg.response_type.value,
                "content": msg.content,
                "provider": msg.provider,
                "model": msg.model,
                "latency_ms": msg.latency_ms,
                "prompt_tokens": msg.prompt_tokens,
                "completion_tokens": msg.completion_tokens,
                "total_tokens": msg.total_tokens,
                "cost": msg.cost,
                "success": msg.success,
                "error_message": msg.error_message,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in debate.messages
        ]

        # Calculate metadata
        metadata = None
        if debate.messages:
            total_cost = sum(m.cost for m in debate.messages)
            total_tokens = sum(m.total_tokens for m in debate.messages)
            providers_used = list(set(m.provider for m in debate.messages))
            successful = sum(1 for m in debate.messages if m.success)
            success_rate = successful / len(debate.messages) if debate.messages else 0

            metadata = {
                "total_executions": len(debate.messages),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "providers_used": providers_used,
                "execution_time_ms": execution_time_ms or 0,
                "success_rate": success_rate,
            }

        return {
            "id": str(debate.id),
            "question": debate.question,
            "status": debate.status.value,
            "question_type": debate.question_type.value,
            "strategy": debate.strategy,
            "provider": debate.provider,
            "model": debate.model,
            "final_answer": final_answer,
            "created_at": debate.created_at.isoformat(),
            "started_at": debate.started_at.isoformat() if debate.started_at else None,
            "completed_at": debate.completed_at.isoformat() if debate.completed_at else None,
            "execution_time_ms": execution_time_ms,
            "messages": messages,
            "metadata": metadata,
        }

    def _format_debate_summary(self, debate: Debate) -> dict:
        """
        Format Debate object into summary for listing.

        Args:
            debate: Debate model instance

        Returns:
            Formatted debate summary dict
        """
        execution_time_ms = None
        if debate.started_at and debate.completed_at:
            execution_time_ms = int(
                (debate.completed_at - debate.started_at).total_seconds() * 1000
            )

        return {
            "id": str(debate.id),
            "question": debate.question[:100],  # Truncate for summary
            "status": debate.status.value,
            "provider": debate.provider,
            "model": debate.model,
            "created_at": debate.created_at.isoformat(),
            "completed_at": debate.completed_at.isoformat() if debate.completed_at else None,
            "execution_time_ms": execution_time_ms,
            "message_count": len(debate.messages) if debate.messages else 0,
        }

    # ==================== VALIDATION ====================

    def _validate_create_debate_inputs(
        self,
        question: str,
        provider: Optional[str],
        model: Optional[str],
        strategy: Optional[str],
    ) -> None:
        """
        Validate inputs for debate creation.

        Args:
            question: Question to validate
            provider: Provider to validate
            model: Model to validate
            strategy: Strategy to validate

        Raises:
            ValueError: If any input is invalid
        """
        # Question validation
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if len(question) > 2000:
            raise ValueError("Question is too long (max 2000 characters)")

        # Provider validation
        if provider and provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        # Strategy validation
        if strategy and strategy not in DEBATE_STRATEGIES:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def _classify_question(self, question: str) -> QuestionType:
        """
        Classify question type based on question text.

        Args:
            question: Question to classify

        Returns:
            QuestionType enum value
        """
        question_lower = question.lower()

        # Simple heuristics for question classification
        if any(keyword in question_lower for keyword in ["is", "does", "can", "will"]):
            return QuestionType.FACTUAL
        elif any(keyword in question_lower for keyword in ["why", "how", "what"]):
            return QuestionType.REASONING
        elif any(keyword in question_lower for keyword in ["vs", "versus", "better", "worse"]):
            return QuestionType.COMPARISON
        elif any(keyword in question_lower for keyword in ["code", "program", "algorithm"]):
            return QuestionType.CODING
        else:
            return QuestionType.DEBATE
