"""Rule-based polish: filler removal, spacing, capitalization, punctuation.

Always available and instant; also the fallback when the Ollama polisher is
unreachable or times out.
"""

from __future__ import annotations

import re
from typing import Iterable

FILLER_PHRASES = ("so basically", "you know", "i mean")
FILLER_WORDS = ("umm", "uhh", "ahh", "um", "uh", "er", "erm", "ah", "mhm", "hmm", "mm")

_SENTENCE_START = re.compile(r"(^|[.!?]\s+)([a-z])")


class RulePolisher:
    def __init__(self, extra_fillers: Iterable[str] = ()) -> None:
        fillers = [*FILLER_PHRASES, *FILLER_WORDS, *extra_fillers]
        alternation = "|".join(
            re.escape(f) for f in sorted(fillers, key=len, reverse=True)
        )
        # Absorb a comma on either side so removal doesn't strand punctuation.
        self._filler_pattern = re.compile(
            rf"(?:,\s*)?\b(?:{alternation})\b,?", re.IGNORECASE
        )

    def polish(self, text: str) -> str:
        if not text.strip():
            return ""
        text = self._filler_pattern.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r",(\s*,)+", ",", text)
        text = re.sub(r"^[\s,.;:]+", "", text)
        if not text:
            return ""
        text = re.sub(r"\bi\b", "I", text)
        text = _SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text)
        text = re.sub(r"[,\s]+$", "", text)
        if text and text[-1] not in ".!?":
            text += "."
        return text
