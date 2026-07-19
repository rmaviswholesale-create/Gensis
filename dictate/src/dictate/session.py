"""Glue between the hotkey, microphone, chunker, and pipeline runner.

One CaptureSession lives for the app's lifetime; each begin()/end() pair is
one utterance with a fresh chunker so state never leaks between utterances.
"""

from __future__ import annotations

import threading
from typing import Callable, Protocol

from dictate.chunker import SilenceChunker
from dictate.interfaces import AudioChunk


class _Runner(Protocol):
    def dictation_start(self) -> None: ...

    def dictation_stop(self) -> None: ...

    def submit(self, chunk: AudioChunk) -> None: ...


class _Capture(Protocol):
    def start(self, on_pcm: Callable[[bytes], None]) -> None: ...

    def stop(self) -> None: ...


class CaptureSession:
    def __init__(
        self,
        runner: _Runner,
        capture: _Capture,
        chunker_factory: Callable[[], SilenceChunker],
    ) -> None:
        self._runner = runner
        self._capture = capture
        self._chunker_factory = chunker_factory
        self._chunker: SilenceChunker | None = None
        # begin/end come from the hotkey thread, _on_pcm from the audio thread.
        self._lock = threading.Lock()

    def begin(self) -> None:
        with self._lock:
            if self._chunker is not None:
                return
            self._chunker = self._chunker_factory()
            self._runner.dictation_start()
        self._capture.start(self._on_pcm)

    def end(self) -> None:
        with self._lock:
            if self._chunker is None:
                return
            chunker, self._chunker = self._chunker, None
        self._capture.stop()
        tail = chunker.flush()
        if tail is not None:
            self._runner.submit(tail)
        self._runner.dictation_stop()

    def _on_pcm(self, pcm: bytes) -> None:
        with self._lock:
            chunker = self._chunker
            if chunker is None:  # audio callback racing a stop
                return
            for chunk in chunker.push(pcm):
                self._runner.submit(chunk)
