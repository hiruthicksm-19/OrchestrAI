"""
Question Classifier.

Classifies a user's question into a category using heuristics only.
No LLM call is made.  This keeps latency near zero and keeps the
classification logic testable and deterministic.

Categories
----------
factual      — Has a single correct answer (who, what, when, where).
explanation  — Asks how or why something works.
comparison   — Compares two or more things.
coding       — Asks for code or a technical implementation.
architecture — Asks about system or software design.
debate       — Normative or contested (should, ought, best, vs humans).
reasoning    — Logic, math, or multi-step inference.
creative     — Open-ended, imaginative, or generative.
"""

from __future__ import annotations

import re
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionType(str, Enum):
    FACTUAL = "factual"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    CODING = "coding"
    ARCHITECTURE = "architecture"
    DEBATE = "debate"
    REASONING = "reasoning"
    CREATIVE = "creative"


# ---------------------------------------------------------------------------
# Keyword / pattern tables (order = priority, first match wins)
# ---------------------------------------------------------------------------

_CODING_PATTERNS = [
    r"\bwrite\b.*(code|function|class|script|program|implementation|algorithm)\b",
    r"\bimplement\b",
    r"\b(python|javascript|typescript|java|c\+\+|rust|go|sql)\b.*\b(code|function|class)\b",
    r"\bhow (do i|to) (code|program|implement|build|create)\b",
    r"\bdebug\b|\bfix.*(bug|error|exception)\b",
    r"\bsnippet\b",
]

_ARCHITECTURE_PATTERNS = [
    r"\b(design|architect|structure)\b.*(system|service|api|database|microservice)\b",
    r"\b(system design|database schema|api design|folder structure|project structure)\b",
    r"\bhow (would|should) (you|i|we) (design|architect|structure)\b",
    r"\bscalable\b.*\b(system|service|architecture)\b",
]

_DEBATE_PATTERNS = [
    r"\bshould\b",
    r"\bwill\b.*\b(replace|beat|outperform|take over)\b",
    r"\b(better|worse|best|worst)\b.*\bthan\b",
    r"\bversus\b|\bvs\.?\b",
    r"\b(pros and cons|advantages and disadvantages)\b",
    r"\bis (ai|automation|technology).*(good|bad|dangerous|safe|ethical)\b",
    r"\b(replace|displace|eliminate)\b.*\b(human|job|worker|engineer|doctor)\b",
    r"\bdo you (think|believe|agree)\b",
    r"\bshould (we|humans|society|companies)\b",
    r"\bworth it\b|\bis it (worth|right|wrong|ethical|moral)\b",
]

_COMPARISON_PATTERNS = [
    r"\bdifference between\b",
    r"\bcompare\b",
    r"\b(vs\.?|versus)\b",
    r"\bwhich (is|one is|one should|should i)\b",
    r"\bsimilarities (and|or) differences\b",
]

_REASONING_PATTERNS = [
    r"\bprove\b|\bproof\b",
    r"\b(how many|calculate|compute|solve)\b",
    r"\bstep.by.step\b",
    r"\bif .+ then\b",
    r"\bwhat (happens|would happen|is the result) (if|when|after)\b",
    r"\blogic\b|\balgorithm\b.*\btime complexity\b",
    r"\b\d+\s*[\+\-\*\/]\s*\d+\b",  # arithmetic
]

_EXPLANATION_PATTERNS = [
    r"\bwhat is\b|\bwhat are\b",
    r"\bhow (does|do|did)\b",
    r"\bexplain\b",
    r"\bwhy (does|do|did|is|are)\b",
    r"\bdefine\b|\bdefinition of\b",
    r"\bwhat (does|do).*(mean|stand for)\b",
    r"\bhow (it works|does it work)\b",
]

_FACTUAL_PATTERNS = [
    r"\bwho (is|was|are|were)\b",
    r"\bwhen (did|was|is|are)\b",
    r"\bwhere (is|was|are|were|did)\b",
    r"\bwhich (country|city|year|date|person|company|language)\b",
    r"\bwhat (year|date|time|country|language|version)\b",
    r"\bcurrent (president|prime minister|ceo|leader|version|price)\b",
    r"\bhow (old|tall|long|far|many|much) (is|was|are|were)\b",
    r"\bname (of|the)\b",
    r"\bcapital (of|city)\b",
]

_CREATIVE_PATTERNS = [
    r"\bwrite (a|an|me)\b.*(story|poem|joke|essay|email|letter|blog)\b",
    r"\bcreate (a|an)\b.*(story|poem|joke|name|slogan)\b",
    r"\bimagine\b",
    r"\bgive me (ideas|suggestions|names|examples)\b",
    r"\bbrainstorm\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Return True if *text* matches any regex pattern in *patterns*."""
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


class QuestionClassifier:
    """
    Heuristic question classifier.

    Uses ordered pattern matching.  The first matching category wins.
    The order (most specific → most general) prevents false positives.

    Usage
    -----
        classifier = QuestionClassifier()
        q_type = classifier.classify("Should AI replace software engineers?")
        # QuestionType.DEBATE
    """

    def classify(self, question: str) -> QuestionType:
        """
        Classify *question* into a QuestionType.

        Parameters
        ----------
        question:
            The raw user question string.

        Returns
        -------
        QuestionType
            The detected category.
        """
        q = question.strip()

        # Order matters — most specific first.
        if _matches_any(q, _CODING_PATTERNS):
            result = QuestionType.CODING
        elif _matches_any(q, _ARCHITECTURE_PATTERNS):
            result = QuestionType.ARCHITECTURE
        elif _matches_any(q, _COMPARISON_PATTERNS):
            result = QuestionType.COMPARISON
        elif _matches_any(q, _DEBATE_PATTERNS):
            result = QuestionType.DEBATE
        elif _matches_any(q, _REASONING_PATTERNS):
            result = QuestionType.REASONING
        elif _matches_any(q, _CREATIVE_PATTERNS):
            result = QuestionType.CREATIVE
        elif _matches_any(q, _EXPLANATION_PATTERNS):
            result = QuestionType.EXPLANATION
        elif _matches_any(q, _FACTUAL_PATTERNS):
            result = QuestionType.FACTUAL
        else:
            # Default: treat as explanation — sensible middle ground.
            result = QuestionType.EXPLANATION

        logger.info(f"QuestionClassifier: '{q[:60]}' → {result.value}")
        return result
