"""
API Usage Model

Tracks API usage independently of debates.

Useful for:
- Provider usage analytics
- Cost tracking
- Performance monitoring
- Rate limiting
- Billing and metering

Fields:
- id: UUID primary key
- provider: Which provider was used
- model: Which model was used
- endpoint: Which endpoint was called
- latency_ms: Response time in milliseconds
- tokens: Tokens used in this call
- cost: Cost of this API call
- success: Whether the call succeeded
- created_at: When this call was made

Relationships:
- None (independent tracking)

Use Cases:
- Provider cost analysis
- Model performance comparison
- Endpoint usage statistics
- Token burn rate tracking
- Billing calculations
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, Float, Boolean, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base_model import BaseModel


class APIUsage(BaseModel):
    """API usage and provider cost tracking."""

    __tablename__ = "api_usage"

    # Provider and model
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Provider name (groq, mistral, openai, cerebras)",
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Model identifier",
    )

    # API call details
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="API endpoint called",
    )

    # Performance metrics
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Response time in milliseconds",
    )

    # Token and cost tracking
    tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Tokens used in this call",
    )

    cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Cost of this API call",
    )

    # Result tracking
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the API call succeeded",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_api_usage_provider", "provider"),
        Index("idx_api_usage_model", "model"),
        Index("idx_api_usage_created_at", "created_at"),
        Index("idx_api_usage_provider_created", "provider", "created_at"),
        Index("idx_api_usage_model_created", "model", "created_at"),
        CheckConstraint("latency_ms >= 0"),
        CheckConstraint("tokens >= 0"),
        CheckConstraint("cost >= 0"),
    )

    def __repr__(self) -> str:
        return (
            f"<APIUsage(provider={self.provider}, model={self.model}, "
            f"tokens={self.tokens})>"
        )
