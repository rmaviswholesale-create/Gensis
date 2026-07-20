"""Microphone capture: 16 kHz mono PCM16 blocks delivered to a callback.

sounddevice is imported lazily; a stream factory can be injected for tests.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger(__name__)

_BLOCK_MS = 30


class MicrophoneCapture:
    def __init__(
        self,
        sample_rate: int = 16000,
        device: str | int | None = None,
        stream_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._device = device
        self._stream_factory = stream_factory or _sounddevice_stream
        self._stream: Any = None

    def start(self, on_pcm: Callable[[bytes], None]) -> None:
        self.stop()

        def callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            if status:
                log.warning("audio input status: %s", status)
            on_pcm(bytes(indata))

        self._stream = self._stream_factory(
            samplerate=self._sample_rate,
            channels=1,
            dtype="int16",
            device=self._device,
            blocksize=self._sample_rate * _BLOCK_MS // 1000,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is None:
            return
        stream, self._stream = self._stream, None
        stream.stop()
        stream.close()


def _sounddevice_stream(**kwargs: Any) -> Any:
    import sounddevice

    return sounddevice.RawInputStream(**kwargs)
