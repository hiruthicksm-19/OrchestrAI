"""
Abstract base class that every provider must implement.

The rest of the application depends only on this interface, never on a
concrete provider.  Swapping Groq for OpenAI means writing a new class
that satisfies this contract — nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class Message:
    """
    Lightweight representation of a single chat message.

    Parameters
    ----------
    role:
        ``"system"``, ``"user"``, or ``"assistant"``.
    content:
        The text payload of the message.
    """

    __slots__ = ("role", "content")

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        """Serialise to the standard OpenAI-compatible dict format."""
        return {"role": self.role, "content": self.content}

    def __repr__(self) -> str:
        preview = self.content[:60].replace("\n", " ")
        return f"Message(role={self.role!r}, content={preview!r}...)"


class BaseProvider(ABC):
    """
    Abstract provider interface.

    Every concrete provider (Groq, Mistral, Cerebras …) must implement
    :meth:`complete` and :meth:`provider_name`.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. ``"groq"``)."""

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Send *messages* to the provider and return the assistant reply.

        Parameters
        ----------
        messages:
            Conversation history including system and user messages.
        model:
            Model identifier string understood by this provider.
        temperature:
            Sampling temperature (0.0 – 1.0).
        max_tokens:
            Maximum tokens allowed in the completion.

        Returns
        -------
        str
            The assistant's reply text.

        Raises
        ------
        ProviderAuthError
            On authentication failures.
        ProviderRateLimitError
            When the provider returns a rate-limit response.
        ProviderTimeoutError
            When the request exceeds the configured timeout.
        ProviderError
            For any other provider-side failure.
        """
