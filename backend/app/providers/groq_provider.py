"""
Groq provider implementation.

Wraps the official `groq` Python SDK and maps its exceptions to the
DebateAI exception hierarchy.  No other layer is aware of Groq-specific
types or error codes.
"""

from __future__ import annotations

from typing import List

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from backend.app.providers.base_provider import BaseProvider, Message
from backend.app.utils.exceptions import (
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class GroqProvider(BaseProvider):
    """
    AI provider backed by the Groq API.

    Parameters
    ----------
    api_key:
        Groq API key.  Should come from ``settings.groq_api_key``.
    timeout:
        Request timeout in seconds.
    """

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        try:
            from groq import AsyncGroq
        except ImportError as exc:
            raise ProviderError(
                "The 'groq' package is not installed. Run: pip install groq"
            ) from exc

        self._client = AsyncGroq(api_key=api_key, timeout=timeout)
        self._timeout = timeout
        logger.info("GroqProvider initialised")

    @property
    def provider_name(self) -> str:
        return "groq"

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ProviderRateLimitError),
    )
    async def complete(
        self,
        messages: List[Message],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Send *messages* to the Groq API and return the assistant's reply.
        """
        logger.debug(f"GroqProvider.complete | model={model} | messages={len(messages)}")

        raw_messages = [m.to_dict() for m in messages]

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=raw_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            logger.debug(f"GroqProvider response received | tokens={response.usage.total_tokens}")
            return content

        except Exception as exc:
            self._map_exception(exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_exception(self, exc: Exception) -> None:
        """Translate Groq SDK exceptions to DebateAI exceptions."""
        exc_str = str(exc).lower()
        exc_type = type(exc).__name__

        if "authentication" in exc_str or "api key" in exc_str or "unauthorized" in exc_str:
            raise ProviderAuthError(f"[Groq] Authentication failed: {exc}") from exc
        if "rate limit" in exc_str or "ratelimit" in exc_str or "429" in exc_str:
            raise ProviderRateLimitError(f"[Groq] Rate limit exceeded: {exc}") from exc
        if "timeout" in exc_str or "timed out" in exc_str:
            raise ProviderTimeoutError(f"[Groq] Request timed out: {exc}") from exc

        raise ProviderError(f"[Groq] Unexpected error ({exc_type}): {exc}") from exc
