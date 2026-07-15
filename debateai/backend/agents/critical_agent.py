"""
Critical Agent — kept for registry backward compatibility.

In the new architecture the Opponent Agent handles adversarial debate.
The Critical Agent class is retained so existing registry entries with
role="critical" do not break.  It delegates to the same behaviour as
the OpponentAgent when used in a debate context.

For new deployments, register an "opponent" role agent instead.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.agents.opponent_agent import OpponentAgent
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CriticalAgent(OpponentAgent):
    """
    Alias for OpponentAgent.

    Preserves backward compatibility for registry entries that use
    role="critical".  Behaviour is identical to OpponentAgent.
    """
    pass
