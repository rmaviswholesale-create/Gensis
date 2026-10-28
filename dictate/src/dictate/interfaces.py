"""Core contracts. Platform backends and engines implement these; the pipeline
depends only on this module so the core stays dependency-free and testable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AudioChunk:
    """Little-endian mono PCM16 audio."""

    pcm16: bytes
    sample_rate: int = 16000

    @property
    def duration_seconds(self) -> float:
        return len(self.pcm16) / 2 / self.sample_rate


class TranscriptionEngine(Protocol):
    def transcribe(self, chunk: AudioChunk) -> str:
        """Return the text for one chunk ('' if no speech)."""
        ...


class Polisher(Protocol):
    def polish(self, text: str) -> str:
        """Return cleaned-up text (fillers removed, punctuation/grammar fixed)."""
        ...


class TextInjector(Protocol):
    def inject(self, text: str) -> None:
        """Type text into the currently focused text field."""
        ...
