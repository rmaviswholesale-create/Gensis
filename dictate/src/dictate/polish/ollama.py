"""LLM polish via a local Ollama server.

Every failure mode — connection refused, timeout, non-200, malformed JSON,
empty or off-task responses — degrades to the rule-based fallback so
dictation never stalls and never injects LLM chatter.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request

from dictate.interfaces import Polisher

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You clean up dictated text. Remove filler words (um, uh, you know, i mean), "
    "fix grammar, punctuation, and capitalization. Keep the speaker's wording and "
    "meaning; do not add or summarize anything. Output ONLY the corrected text — "
    "no quotes, no explanations, no preamble."
)

# Responses that are the LLM talking about the task instead of doing it.
_PREAMBLE = re.compile(
    r"^(sure|here is|here's|certainly|of course|i'm sorry|as an ai)", re.IGNORECASE
)
_MAX_GROWTH = 3.0  # polished text longer than this ratio of input is off-task


class OllamaPolisher:
    def __init__(
        self,
        host: str,
        model: str,
        fallback: Polisher,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._url = host.rstrip("/") + "/api/generate"
        self._model = model
        self._fallback = fallback
        self._timeout = timeout_seconds

    def polish(self, text: str) -> str:
        if not text.strip():
            return ""
        response = self._request(text)
        if response is None:
            return self._fallback.polish(text)
        return response

    def _request(self, text: str) -> str | None:
        payload = json.dumps(
            {
                "model": self._model,
                "system": SYSTEM_PROMPT,
                "prompt": text,
                "stream": False,
                "options": {"temperature": 0.0},
            }
        ).encode()
        request = urllib.request.Request(
            self._url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as resp:
                body = json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            log.warning("ollama polish failed (%s); using rule-based fallback", exc)
            return None
        polished = str(body.get("response", "")).strip().strip('"').strip()
        if not polished:
            log.warning("ollama returned an empty response; using fallback")
            return None
        if _PREAMBLE.match(polished) or len(polished) > max(80, len(text) * _MAX_GROWTH):
            log.warning("ollama response looks off-task (%.40r...); using fallback", polished)
            return None
        return polished
