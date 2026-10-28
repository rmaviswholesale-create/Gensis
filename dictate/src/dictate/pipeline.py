"""Utterance pipeline core and its threaded runner.

`DictationPipeline` is synchronous and single-threaded by contract; all
concurrency lives in `PipelineRunner`, which serializes hotkey/audio callbacks
onto one worker thread through a queue. This keeps ordering guarantees trivial:
events are processed strictly in submission order, so utterances can never
interleave or arrive at the injector out of order.
"""

from __future__ import annotations

import logging
import queue
import threading
from enum import Enum, auto
from typing import Callable, Sequence

from dictate.interfaces import AudioChunk, TextInjector, TranscriptionEngine

log = logging.getLogger(__name__)

Transform = Callable[[str], str]


class DictationPipeline:
    """Accumulates transcribed chunks into an utterance, then transforms and injects it.

    With ``stream=True`` each chunk is transformed and injected immediately
    (trailing space appended) instead of waiting for the utterance to end.
    """

    def __init__(
        self,
        engine: TranscriptionEngine,
        transforms: Sequence[Transform],
        injector: TextInjector,
        stream: bool = False,
    ) -> None:
        self._engine = engine
        self._transforms = list(transforms)
        self._injector = injector
        self._stream = stream
        self._recording = False
        self._segments: list[str] = []

    @property
    def recording(self) -> bool:
        return self._recording

    def start_utterance(self) -> None:
        if self._recording:
            return
        self._recording = True
        self._segments = []

    def feed(self, chunk: AudioChunk) -> None:
        if not self._recording:
            return
        try:
            text = self._engine.transcribe(chunk).strip()
        except Exception:
            log.exception("transcription failed for a %.2fs chunk; skipping", chunk.duration_seconds)
            return
        if not text:
            return
        if self._stream:
            self._injector.inject(self._apply_transforms(text) + " ")
        else:
            self._segments.append(text)

    def end_utterance(self) -> str:
        if not self._recording:
            return ""
        self._recording = False
        if self._stream:
            return ""
        raw = " ".join(self._segments)
        self._segments = []
        if not raw.strip():
            return ""
        polished = self._apply_transforms(raw)
        if not polished.strip():
            return ""
        self._injector.inject(polished)
        return polished

    def _apply_transforms(self, text: str) -> str:
        for transform in self._transforms:
            text = transform(text)
        return text


class _Event(Enum):
    START = auto()
    STOP = auto()
    CLOSE = auto()


class PipelineRunner:
    """Drives a DictationPipeline on a dedicated worker thread.

    Producers (hotkey listener, audio callback) call `dictation_start`,
    `submit`, and `dictation_stop` from any thread; events are drained FIFO.
    `close()` processes everything already queued, then joins the worker.
    """

    def __init__(self, pipeline: DictationPipeline) -> None:
        self._pipeline = pipeline
        self._queue: queue.Queue[_Event | AudioChunk] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._closed = False

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="dictate-pipeline", daemon=True)
        self._thread.start()

    def dictation_start(self) -> None:
        self._queue.put(_Event.START)

    def dictation_stop(self) -> None:
        self._queue.put(_Event.STOP)

    def submit(self, chunk: AudioChunk) -> None:
        self._queue.put(chunk)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_Event.CLOSE)
        if self._thread is not None:
            self._thread.join(timeout=10)

    def _run(self) -> None:
        while True:
            event = self._queue.get()
            if event is _Event.CLOSE:
                return
            if event is _Event.START:
                self._pipeline.start_utterance()
            elif event is _Event.STOP:
                self._pipeline.end_utterance()
            else:
                self._pipeline.feed(event)
