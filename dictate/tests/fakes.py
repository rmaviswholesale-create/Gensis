"""Test doubles for the pipeline's external boundaries."""

from __future__ import annotations

from dictate.interfaces import AudioChunk


def chunk(tag: bytes = b"\x00\x00") -> AudioChunk:
    return AudioChunk(pcm16=tag, sample_rate=16000)


class FakeEngine:
    """Maps each chunk to the next queued text; raises when text is an Exception."""

    def __init__(self, texts: list[str | Exception]):
        self.texts = list(texts)
        self.calls = 0

    def transcribe(self, chunk: AudioChunk) -> str:
        self.calls += 1
        item = self.texts.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class RecordingInjector:
    def __init__(self) -> None:
        self.injected: list[str] = []

    def inject(self, text: str) -> None:
        self.injected.append(text)


def upper_transform(text: str) -> str:
    return text.upper()


def exclaim_transform(text: str) -> str:
    return text + "!"
