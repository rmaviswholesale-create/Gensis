"""Local speech-to-text via faster-whisper, plus WAV helpers.

faster-whisper (and numpy) are imported lazily so the core package installs
and tests run without the heavy STT extra.
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any, Callable

from dictate.interfaces import AudioChunk


def read_wav_pcm16(path: str | Path) -> tuple[bytes, int]:
    """Return (pcm16 bytes, sample_rate) for a mono 16-bit WAV file."""
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1:
            raise ValueError(f"{path}: expected mono WAV, got {w.getnchannels()} channels")
        if w.getsampwidth() != 2:
            raise ValueError(f"{path}: expected 16-bit PCM, got {w.getsampwidth() * 8}-bit")
        return w.readframes(w.getnframes()), w.getframerate()


class FasterWhisperEngine:
    """TranscriptionEngine backed by a local Whisper model (CTranslate2)."""

    def __init__(
        self,
        model: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        if model_factory is None:
            from faster_whisper import WhisperModel  # heavy import, deferred

            model_factory = WhisperModel
        self._language = language
        self._model = model_factory(model, device=device, compute_type=compute_type)

    def transcribe(self, chunk: AudioChunk) -> str:
        audio = _pcm16_to_float32(chunk.pcm16)
        segments, _info = self._model.transcribe(
            audio,
            language=self._language,
            beam_size=1,
            condition_on_previous_text=False,
            vad_filter=False,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()


def _pcm16_to_float32(pcm16: bytes) -> Any:
    try:
        import numpy as np

        return np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    except ImportError:  # test environments without the stt extra
        import array

        ints = array.array("h")
        ints.frombytes(pcm16)
        return array.array("f", (s / 32768.0 for s in ints))
