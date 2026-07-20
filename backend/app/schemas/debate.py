"""
Debate API Request/Response Schemas

Pydantic models for API validation and serialization.

Never expose SQLAlchemy models directly.
All API responses go through these schemas.

Design Principles:
- Validation at the boundary (FastAPI dependency)
- Serialization for external consumption
- Type safety for all requests/responses
- OpenAPI documentation auto-generated
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ==================== REQUEST SCHEMAS ====================


class CreateDebateRequest(BaseModel):
    """Request to create a new debate."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to debate",
        example="Is artificial intelligence a threat to humanity?"
    )

    provider: Optional[str] = Field(
        default=None,
        description="AI provider (groq, mistral, openai, cerebras). Uses default if not specified.",
        example="groq"
    )

    model: Optional[str] = Field(
        default=None,
        description="Model identifier. Uses default if not specified.",
        example="llama-3.3-70b-versatile"
    )

    strategy: Optional[str] = Field(
        default="simple",
        description="Debate strategy (simple, adversarial, comparative)",
        example="simple"
    )

    stream: bool = Field(
        default=False,
        description="Stream results (not yet implemented, reserved for future use)"
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean question."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Should AI be regulated?",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "strategy": "simple"
            }
        }


class UpdateDebateRequest(BaseModel):
    """Request to update a debate (reserved for future use)."""

    status: Optional[str] = Field(
        default=None,
        description="New status (pending, running, completed, failed)"
    )


class ListDebatesQuery(BaseModel):
    """Query parameters for listing debates."""

    skip: int = Field(
        default=0,
        ge=0,
        description="Number of debates to skip (pagination)"
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of debates to return (max 100)"
    )

    status: Optional[str] = Field(
        default=None,
        description="Filter by status (pending, running, completed, failed)"
    )

    provider: Optional[str] = Field(
        default=None,
        description="Filter by provider"
    )

    sort_by: str = Field(
        default="created_at",
        description="Sort field (created_at, completed_at, status)"
    )

    sort_order: str = Field(
        default="desc",
        description="Sort order (asc, desc)"
    )


# ==================== RESPONSE SCHEMAS ====================


class MessageResponse(BaseModel):
    """Single agent execution record response."""

    id: UUID = Field(description="Message unique identifier")
    debate_id: UUID = Field(description="Parent debate ID")
    agent_name: str = Field(description="Name of the agent")
    agent_role: str = Field(description="Role of the agent (research, opponent, consensus)")
    round_number: int = Field(description="Debate round number")
    response_type: str = Field(description="Type of response (initial, rebuttal, consensus, final)")
    content: str = Field(description="Response content from the agent")
    provider: str = Field(description="Provider used for this execution")
    model: str = Field(description="Model used for this execution")
    latency_ms: int = Field(description="Execution latency in milliseconds")
    prompt_tokens: int = Field(description="Tokens used in prompt")
    completion_tokens: int = Field(description="Tokens generated in response")
    total_tokens: int = Field(description="Total tokens used")
    cost: float = Field(description="Cost of this execution in dollars")
    success: bool = Field(description="Whether execution succeeded")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    created_at: datetime = Field(description="When this execution occurred")

    class Config:
        from_attributes = True


class ExecutionMetadata(BaseModel):
    """Execution summary metadata."""

    total_executions: int = Field(description="Total number of agent executions")
    total_cost: float = Field(description="Total cost in dollars")
    total_tokens: int = Field(description="Total tokens used")
    providers_used: List[str] = Field(description="List of providers used")
    execution_time_ms: int = Field(description="Total execution time in milliseconds")
    success_rate: float = Field(description="Success rate (0.0 to 1.0)")


class DebateResponse(BaseModel):
    """Complete debate response with all details."""

    id: UUID = Field(description="Debate unique identifier")
    question: str = Field(description="The question being debated")
    status: str = Field(description="Current status (pending, running, completed, failed)")
    question_type: str = Field(description="Classification of the question")
    strategy: str = Field(description="Debate strategy used")
    provider: str = Field(description="Primary provider used")
    model: str = Field(description="Primary model used")
    
    # Results (populated when completed)
    final_answer: Optional[str] = Field(
        None,
        description="Final consensus answer (when completed)"
    )
    
    # Timestamps
    created_at: datetime = Field(description="When debate was created")
    started_at: Optional[datetime] = Field(None, description="When debate execution started")
    completed_at: Optional[datetime] = Field(None, description="When debate execution completed")
    execution_time_ms: Optional[int] = Field(
        None,
        description="Total execution time in milliseconds"
    )

    # Execution details
    messages: List[MessageResponse] = Field(
        default_factory=list,
        description="All agent execution records"
    )
    
    metadata: Optional[ExecutionMetadata] = Field(
        None,
        description="Execution summary metadata"
    )

    class Config:
        from_attributes = True

    @field_validator('messages', mode='before')
    @classmethod
    def validate_messages(cls, v):
        """Ensure messages is a list."""
        return v or []


class DebateSummaryResponse(BaseModel):
    """Summarized debate response (for listing)."""

    id: UUID = Field(description="Debate unique identifier")
    question: str = Field(description="The question being debated")
    status: str = Field(description="Current status")
    provider: str = Field(description="Provider used")
    model: str = Field(description="Model used")
    created_at: datetime = Field(description="When debate was created")
    completed_at: Optional[datetime] = Field(None, description="When debate completed")
    execution_time_ms: Optional[int] = Field(None, description="Execution time")
    message_count: int = Field(default=0, description="Number of executions")

    class Config:
        from_attributes = True


class DebateListResponse(BaseModel):
    """List of debates with pagination info."""

    debates: List[DebateSummaryResponse] = Field(
        description="List of debate summaries"
    )
    total: int = Field(description="Total number of debates available")
    skip: int = Field(description="Number of debates skipped (offset)")
    limit: int = Field(description="Number of debates returned")

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status (healthy, unhealthy)")
    timestamp: datetime = Field(description="When health check was performed")
    version: str = Field(description="API version")
    database: str = Field(description="Database status (connected, disconnected, unknown)")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type/message")
    detail: Optional[str] = Field(None, description="Detailed error description")
    status_code: int = Field(description="HTTP status code")
    timestamp: datetime = Field(description="When error occurred")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    class Config:
        from_attributes = True


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    error: str = Field(default="Validation Error", description="Error type")
    details: List[dict] = Field(description="Validation error details")
    status_code: int = Field(default=422, description="HTTP status code")
    timestamp: datetime = Field(description="When error occurred")


# ==================== HELPER SCHEMAS ====================


class PaginationInfo(BaseModel):
    """Pagination metadata."""

    skip: int = Field(description="Offset")
    limit: int = Field(description="Limit")
    total: int = Field(description="Total available")
    pages: int = Field(description="Total number of pages")


# ==================== WEBSOCKET SCHEMAS (RESERVED) ====================


class StreamDebateMessage(BaseModel):
    """Websocket message for streaming (reserved for future)."""

    event: str = Field(description="Event type (agent_started, agent_completed, debate_completed)")
    debate_id: UUID = Field(description="Debate ID")
    data: dict = Field(description="Event-specific data")
    timestamp: datetime = Field(description="When event occurred")
