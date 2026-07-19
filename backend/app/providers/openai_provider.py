"""
OpenAI provider implementation.

Wraps the official `openai` Python SDK and maps its exceptions to the
DebateAI exception hierarchy.  No other layer is aware of OpenAI-specific
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

from app.providers.base_provider import BaseProvider, Message
from app.utils.exceptions import (
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseProvider):
    """
    AI provider backed by the OpenAI API.

    Parameters
    ----------
    api_key:
        OpenAI API key.  Should come from ``settings.openai_api_key``.
    timeout:
        Request timeout in seconds.
    """

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ProviderError(
                "The 'openai' package is not installed. Run: pip install openai"
            ) from exc

        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._timeout = timeout
        logger.info("OpenAIProvider initialised")

    @property
    def provider_name(self) -> str:
        return "openai"

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
        Send *messages* to the OpenAI API and return the assistant's reply.
        """
        logger.debug(f"OpenAIProvider.complete | model={model} | messages={len(messages)}")

        raw_messages = [m.to_dict() for m in messages]

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=raw_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            logger.debug(
                f"OpenAIProvider response received | "
                f"tokens={response.usage.total_tokens}"
            )
            return content

        except Exception as exc:
            self._map_exception(exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_exception(self, exc: Exception) -> None:
        """Translate OpenAI SDK exceptions to DebateAI exceptions."""
        exc_str = str(exc).lower()
        exc_type = type(exc).__name__

        if "authentication" in exc_str or "api key" in exc_str or "unauthorized" in exc_str:
            raise ProviderAuthError(f"[OpenAI] Authentication failed: {exc}") from exc
        if "rate limit" in exc_str or "ratelimit" in exc_str or "429" in exc_str:
            raise ProviderRateLimitError(f"[OpenAI] Rate limit exceeded: {exc}") from exc
        if "timeout" in exc_str or "timed out" in exc_str:
            raise ProviderTimeoutError(f"[OpenAI] Request timed out: {exc}") from exc

        raise ProviderError(f"[OpenAI] Unexpected error ({exc_type}): {exc}") from exc
