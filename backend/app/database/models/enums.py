"""
Database Enumerations

Defines all enumerated types used throughout the database schema.

These enums are used in SQLAlchemy columns and ensure type safety
while preventing invalid values in the database.

Design:
- Each enum is defined as a Python Enum
- Database stores string values for readability
- Easily extensible for future statuses
"""

from enum import Enum


class DebateStatus(str, Enum):
    """Status of a debate."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestionType(str, Enum):
    """Classification of the question."""

    FACTUAL = "factual"
    REASONING = "reasoning"
    COMPARISON = "comparison"
    CODING = "coding"
    CREATIVE = "creative"
    DEBATE = "debate"
    EXPLANATION = "explanation"
    ARCHITECTURE = "architecture"


class AgentRole(str, Enum):
    """Role of an AI agent in the debate."""

    RESEARCH = "research"
    OPPONENT = "opponent"
    CONSENSUS = "consensus"


class ResponseType(str, Enum):
    """Type of response from an agent."""

    INITIAL = "initial"
    REBUTTAL = "rebuttal"
    CONSENSUS = "consensus"
    FINAL = "final"
