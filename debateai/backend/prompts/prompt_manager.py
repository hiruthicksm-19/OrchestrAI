"""
Prompt Manager.

Loads YAML prompt templates from the prompts directory and renders them
with the provided variables.  Prompts are never stored inside Python
source files — this manager is the only place where prompt text is read.

Usage
-----
    pm = PromptManager(prompts_dir=settings.prompts_dir)
    system_prompt = pm.get_system(key="research_agent")
    user_prompt   = pm.render_strategy(key="research_agent", question="Is AI safe?")
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

from backend.utils.exceptions import PromptError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    Loads and renders YAML-based prompt templates.

    Parameters
    ----------
    prompts_dir:
        Directory that contains ``<key>.yaml`` template files.
    """

    def __init__(self, prompts_dir: Path) -> None:
        self._dir = Path(prompts_dir)
        if not self._dir.is_dir():
            raise PromptError(f"Prompts directory not found: {self._dir}")
        logger.info(f"PromptManager initialised with directory: {self._dir}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_system(self, key: str) -> str:
        """
        Return the system prompt string for *key*.

        Parameters
        ----------
        key:
            Matches the ``name`` field in the YAML file (e.g. ``"research_agent"``).
        """
        template = self._load(key)
        system = template.get("system", "")
        if not system:
            raise PromptError(f"Prompt template '{key}' has no 'system' field.")
        return system.strip()

    def get_shared_rules(self) -> Dict[str, Any]:
        """
        Return the parsed shared_rules.yaml as a dictionary.

        This is available for future use (e.g. injecting shared rules into
        agent system prompts at runtime).  Currently the rules are embedded
        directly in each agent's system prompt.
        """
        return self._load("shared_rules")

    def render_strategy(self, key: str, **variables: Any) -> str:
        """
        Load the strategy prompt for *key* and substitute *variables*.

        Parameters
        ----------
        key:
            Template key (file name without ``.yaml``).
        **variables:
            Named values to substitute into the template (e.g. ``question="…"``).
        """
        template = self._load(key)
        strategy: str = template.get("strategy", "")
        if not strategy:
            raise PromptError(f"Prompt template '{key}' has no 'strategy' field.")
        try:
            rendered = strategy.format(**variables)
        except KeyError as exc:
            raise PromptError(
                f"Missing variable {exc} when rendering strategy for '{key}'. "
                f"Provided variables: {list(variables.keys())}"
            ) from exc
        return rendered.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @lru_cache(maxsize=32)
    def _load(self, key: str) -> Dict[str, Any]:
        """Load and cache the YAML template for *key*."""
        path = self._dir / f"{key}.yaml"
        if not path.is_file():
            raise PromptError(
                f"Prompt template file not found: {path}. "
                f"Create '{key}.yaml' in {self._dir}"
            )
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise PromptError(f"Failed to parse prompt template '{path}': {exc}") from exc

        if not isinstance(data, dict):
            raise PromptError(f"Prompt template '{path}' must be a YAML mapping.")
        logger.debug(f"Loaded prompt template '{key}'")
        return data
