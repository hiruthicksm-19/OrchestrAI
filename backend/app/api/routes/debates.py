"""
Debate API Routes

REST API endpoints for debate operations.

Architecture:
    Request → Validation (Pydantic) → Route → Service → Response

Routes are thin - all business logic is in DebateService.

Design:
- Type-safe with Pydantic
- Dependency injection for session
- Proper HTTP status codes
- Structured error responses
- OpenAPI documentation
"""

from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.debate import (
    CreateDebateRequest,
    DebateResponse,
    DebateSummaryResponse,
    DebateListResponse,
    MessageResponse,
    ErrorResponse,
)
from app.services.debate_service import DebateService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/debates", tags=["debates"])


# ==================== POST /debates ====================


@router.post(
    "",
    response_model=DebateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new debate",
    description="Create a new debate with the given question. The debate will be executed immediately.",
    responses={
        201: {"description": "Debate created and executed successfully"},
        422: {"description": "Validation error in request body"},
        500: {"description": "Internal server error during debate execution"},
    },
)
async def create_debate(
    request: CreateDebateRequest,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create and execute a new debate.

    The following workflow occurs:
    1. Request is validated
    2. Debate record is created
    3. Debate Engine executes with agents
    4. Agent executions are stored
    5. Response is returned with results

    Args:
        request: Debate creation request
        session: Database session (injected)

    Returns:
        DebateResponse with complete execution details

    Raises:
        HTTPException: If validation fails or execution errors occur

    Example:
        POST /debates
        {
            "question": "Should AI be regulated?",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "strategy": "simple"
        }

        Response:
        {
            "id": "...",
            "question": "Should AI be regulated?",
            "status": "completed",
            "final_answer": "...",
            "messages": [...],
            "metadata": {...}
        }
    """
    try:
        service = DebateService(session)

        # Create and execute debate
        result = await service.create_debate(
            question=request.question,
            provider=request.provider,
            model=request.model,
            strategy=request.strategy,
        )

        await session.commit()
        logger.info(f"Debate created successfully: id={result['id']}")

        return result

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    except RuntimeError as e:
        logger.error(f"Debate execution error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Debate execution failed. Please try again.",
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# ==================== GET /debates ====================


@router.get(
    "",
    response_model=DebateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List debates",
    description="Get a paginated list of debates with optional filtering.",
    responses={
        200: {"description": "List retrieved successfully"},
        400: {"description": "Invalid query parameters"},
    },
)
async def list_debates(
    skip: int = Query(0, ge=0, description="Number of debates to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of debates to return (max 100)"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (pending, running, completed, failed)"
    ),
    provider: Optional[str] = Query(
        None,
        description="Filter by provider"
    ),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    List debates with pagination and filtering.

    Args:
        skip: Number of debates to skip (pagination offset)
        limit: Number of debates to return (max 100)
        status_filter: Optional status filter
        provider: Optional provider filter
        session: Database session (injected)

    Returns:
        DebateListResponse with paginated results

    Example:
        GET /debates?skip=0&limit=10&status=completed

        Response:
        {
            "debates": [
                {
                    "id": "...",
                    "question": "...",
                    "status": "completed",
                    "provider": "groq",
                    "created_at": "...",
                    "execution_time_ms": 3120
                }
            ],
            "total": 50,
            "skip": 0,
            "limit": 10
        }
    """
    try:
        service = DebateService(session)

        result = await service.list_debates(
            skip=skip,
            limit=limit,
            status=status_filter,
            provider=provider,
        )

        logger.info(f"Listed {len(result['debates'])} debates")

        return result

    except ValueError as e:
        logger.warning(f"Invalid filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error listing debates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve debates",
        )


# ==================== GET /debates/{id} ====================


@router.get(
    "/{debate_id}",
    response_model=DebateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get debate details",
    description="Get complete details of a specific debate including all agent executions.",
    responses={
        200: {"description": "Debate found and returned"},
        404: {"description": "Debate not found"},
    },
)
async def get_debate(
    debate_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get complete details of a debate.

    Returns full debate information including:
    - Question and status
    - All agent executions (messages)
    - Execution metadata and metrics
    - Timestamps

    Args:
        debate_id: UUID of the debate
        session: Database session (injected)

    Returns:
        DebateResponse with full details

    Raises:
        HTTPException: If debate not found

    Example:
        GET /debates/550e8400-e29b-41d4-a716-446655440000

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "question": "Should AI be regulated?",
            "status": "completed",
            "messages": [
                {
                    "agent_name": "research_agent",
                    "content": "..."
                },
                ...
            ],
            "metadata": {
                "total_executions": 3,
                "total_cost": 0.123
            }
        }
    """
    try:
        service = DebateService(session)
        debate = await service.get_debate(debate_id)

        logger.info(f"Retrieved debate: id={debate_id}")

        return debate

    except ValueError as e:
        logger.warning(f"Debate not found: {debate_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debate not found: {debate_id}",
        )

    except Exception as e:
        logger.error(f"Error retrieving debate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve debate",
        )


# ==================== DELETE /debates/{id} ====================


@router.delete(
    "/{debate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a debate",
    description="Delete a debate and all associated data.",
    responses={
        204: {"description": "Debate deleted successfully"},
        404: {"description": "Debate not found"},
    },
)
async def delete_debate(
    debate_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a debate.

    Removes the debate and all associated data:
    - Agent executions (messages)
    - User feedback
    - Any other related records (cascade delete)

    Args:
        debate_id: UUID of the debate to delete
        session: Database session (injected)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: If debate not found

    Example:
        DELETE /debates/550e8400-e29b-41d4-a716-446655440000

        Response: 204 No Content
    """
    try:
        service = DebateService(session)
        await service.delete_debate(debate_id)
        await session.commit()

        logger.info(f"Deleted debate: id={debate_id}")

    except ValueError as e:
        logger.warning(f"Debate not found: {debate_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debate not found: {debate_id}",
        )

    except Exception as e:
        logger.error(f"Error deleting debate: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete debate",
        )
