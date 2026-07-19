"""
Mistral AI provider implementation.

Wraps the official `mistralai` Python SDK and maps its exceptions to the
DebateAI exception hierarchy.
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


class MistralProvider(BaseProvider):
    """
    AI provider backed by the Mistral API.

    Parameters
    ----------
    api_key:
        Mistral API key.  Should come from ``settings.mistral_api_key``.
    timeout:
        Request timeout in seconds.
    """

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise ProviderError(
                "The 'mistralai' package is not installed. Run: pip install mistralai"
            ) from exc

        self._client = Mistral(api_key=api_key)
        self._timeout = timeout
        logger.info("MistralProvider initialised")

    @property
    def provider_name(self) -> str:
        return "mistral"

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
        Send *messages* to the Mistral API and return the assistant's reply.
        """
        logger.debug(f"MistralProvider.complete | model={model} | messages={len(messages)}")

        raw_messages = [m.to_dict() for m in messages]

        try:
            response = await self._client.chat.complete_async(
                model=model,
                messages=raw_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            logger.debug("MistralProvider response received")
            return content

        except Exception as exc:
            self._map_exception(exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_exception(self, exc: Exception) -> None:
        """Translate Mistral SDK exceptions to DebateAI exceptions."""
        exc_str = str(exc).lower()
        exc_type = type(exc).__name__

        if "unauthorized" in exc_str or "api key" in exc_str or "authentication" in exc_str:
            raise ProviderAuthError(f"[Mistral] Authentication failed: {exc}") from exc
        if "rate limit" in exc_str or "429" in exc_str:
            raise ProviderRateLimitError(f"[Mistral] Rate limit exceeded: {exc}") from exc
        if "timeout" in exc_str or "timed out" in exc_str:
            raise ProviderTimeoutError(f"[Mistral] Request timed out: {exc}") from exc

        raise ProviderError(f"[Mistral] Unexpected error ({exc_type}): {exc}") from exc
