"""Energy-based VAD chunker: splits a PCM16 stream into speech chunks at
silence boundaries, keeping each chunk small enough for low-latency STT.

Dependency-free on purpose — it runs in the audio callback path.
"""

from __future__ import annotations

import array

from dictate.interfaces import AudioChunk

_PREROLL_FRAMES = 10  # ~300ms of leading audio kept before speech onset


class SilenceChunker:
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        silence_threshold: int = 500,
        min_silence_ms: int = 400,
        min_speech_ms: int = 200,
        max_chunk_seconds: float = 5.0,
    ) -> None:
        self._sample_rate = sample_rate
        self._frame_ms = frame_ms
        self._frame_bytes = sample_rate * frame_ms // 1000 * 2
        self._threshold = silence_threshold
        self._min_silence_ms = min_silence_ms
        self._min_speech_ms = min_speech_ms
        self._max_chunk_bytes = int(max_chunk_seconds * sample_rate) * 2
        self._pending = bytearray()  # partial frame carry-over between pushes
        self._buf = bytearray()  # current chunk under construction
        self._speech_ms = 0
        self._trailing_silence_ms = 0

    def push(self, pcm16: bytes) -> list[AudioChunk]:
        self._pending.extend(pcm16)
        chunks: list[AudioChunk] = []
        while len(self._pending) >= self._frame_bytes:
            frame = bytes(self._pending[: self._frame_bytes])
            del self._pending[: self._frame_bytes]
            chunk = self._process_frame(frame)
            if chunk is not None:
                chunks.append(chunk)
        return chunks

    def flush(self) -> AudioChunk | None:
        """End of stream: return any buffered speech as a final chunk."""
        self._buf.extend(self._pending)
        self._pending.clear()
        chunk = self._emit() if self._speech_ms >= self._min_speech_ms else None
        self._reset()
        return chunk

    def _process_frame(self, frame: bytes) -> AudioChunk | None:
        is_speech = _mean_abs(frame) > self._threshold

        if not is_speech and self._speech_ms == 0:
            # Leading silence: keep only a short pre-roll so pauses between
            # utterances never accumulate into the next chunk.
            self._buf.extend(frame)
            max_preroll = self._frame_bytes * _PREROLL_FRAMES
            if len(self._buf) > max_preroll:
                del self._buf[: len(self._buf) - max_preroll]
            return None

        self._buf.extend(frame)
        if is_speech:
            self._speech_ms += self._frame_ms
            self._trailing_silence_ms = 0
        else:
            self._trailing_silence_ms += self._frame_ms

        boundary = self._trailing_silence_ms >= self._min_silence_ms
        overflow = len(self._buf) >= self._max_chunk_bytes
        if not boundary and not overflow:
            return None
        chunk = self._emit() if self._speech_ms >= self._min_speech_ms else None
        self._reset()
        return chunk

    def _emit(self) -> AudioChunk:
        return AudioChunk(pcm16=bytes(self._buf), sample_rate=self._sample_rate)

    def _reset(self) -> None:
        self._buf.clear()
        self._speech_ms = 0
        self._trailing_silence_ms = 0


def _mean_abs(frame: bytes) -> float:
    samples = array.array("h")
    samples.frombytes(frame)
    if not samples:
        return 0.0
    return sum(abs(s) for s in samples) / len(samples)
