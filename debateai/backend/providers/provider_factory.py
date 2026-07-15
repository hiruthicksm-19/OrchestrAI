"""
Provider Factory.

Resolves a provider name string to a concrete BaseProvider instance.
The rest of the application never instantiates provider classes directly
— they always go through this factory, which keeps import coupling low
and makes swapping providers trivial.
"""

from __future__ import annotations

from backend.providers.base_provider import BaseProvider
from backend.utils.exceptions import RegistryError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_provider(
    provider_name: str,
    api_key: str,
    timeout: int = 60,
) -> BaseProvider:
    """
    Instantiate and return a provider by name.

    Parameters
    ----------
    provider_name:
        One of ``"groq"``, ``"mistral"``, ``"cerebras"``.
    api_key:
        API key for the chosen provider.
    timeout:
        Per-request timeout in seconds.

    Returns
    -------
    BaseProvider
        A ready-to-use provider instance.

    Raises
    ------
    RegistryError
        If *provider_name* is not recognised.
    """
    name = provider_name.lower()

    if name == "groq":
        from backend.providers.groq_provider import GroqProvider
        return GroqProvider(api_key=api_key, timeout=timeout)

    if name == "mistral":
        from backend.providers.mistral_provider import MistralProvider
        return MistralProvider(api_key=api_key, timeout=timeout)

    if name == "cerebras":
        from backend.providers.cerebras_provider import CerebrasProvider
        return CerebrasProvider(api_key=api_key, timeout=timeout)

    if name == "openai":
        from backend.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, timeout=timeout)

    raise RegistryError(
        f"Unknown provider '{provider_name}'. "
        "Supported providers: groq, mistral, cerebras, openai"
    )
