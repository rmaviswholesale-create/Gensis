"""JSON-backed local dictionary: spoken form → written form overrides.

Applied to raw transcription before any polish pass so jargon can't be
"corrected" away by the LLM.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Mapping

log = logging.getLogger(__name__)


class DictionaryError(ValueError):
    pass


class Dictionary:
    def __init__(self, overrides: Mapping[str, str]) -> None:
        self._map = {key.lower(): value for key, value in overrides.items()}
        if self._map:
            # Longest keys first so "post gress" wins over "post".
            alternation = "|".join(
                re.escape(key) for key in sorted(self._map, key=len, reverse=True)
            )
            self._pattern: re.Pattern[str] | None = re.compile(
                rf"\b(?:{alternation})\b", re.IGNORECASE
            )
        else:
            self._pattern = None

    @classmethod
    def load(cls, path: str | Path) -> "Dictionary":
        path = Path(path)
        if not path.exists():
            log.warning("dictionary file %s not found; using empty dictionary", path)
            return cls({})
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DictionaryError(f"{path}: invalid JSON: {exc}") from exc
        overrides = data.get("overrides", {}) if isinstance(data, dict) else None
        if not isinstance(overrides, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in overrides.items()
        ):
            raise DictionaryError(
                f'{path}: expected {{"overrides": {{"spoken": "written"}}}}'
            )
        return cls(overrides)

    def apply(self, text: str) -> str:
        if self._pattern is None or not text:
            return text
        return self._pattern.sub(lambda m: self._map[m.group(0).lower()], text)
