from __future__ import annotations

from dictate.audio import MicrophoneCapture


class FakeStream:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.closed = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def test_start_opens_16k_mono_int16_stream():
    streams = []

    def factory(**kwargs):
        stream = FakeStream(**kwargs)
        streams.append(stream)
        return stream

    capture = MicrophoneCapture(sample_rate=16000, device=3, stream_factory=factory)
    capture.start(on_pcm=lambda pcm: None)
    stream = streams[0]
    assert stream.started
    assert stream.kwargs["samplerate"] == 16000
    assert stream.kwargs["channels"] == 1
    assert stream.kwargs["dtype"] == "int16"
    assert stream.kwargs["device"] == 3
    assert stream.kwargs["blocksize"] == 480  # 30ms at 16kHz


def test_callback_forwards_pcm_bytes():
    received = []
    holder = {}

    def factory(**kwargs):
        holder["callback"] = kwargs["callback"]
        return FakeStream(**kwargs)

    capture = MicrophoneCapture(stream_factory=factory)
    capture.start(on_pcm=received.append)
    holder["callback"](memoryview(b"\x01\x02\x03\x04"), 2, None, None)
    assert received == [b"\x01\x02\x03\x04"]


def test_stop_closes_stream_and_is_idempotent():
    streams = []

    def factory(**kwargs):
        stream = FakeStream(**kwargs)
        streams.append(stream)
        return stream

    capture = MicrophoneCapture(stream_factory=factory)
    capture.start(on_pcm=lambda pcm: None)
    capture.stop()
    capture.stop()
    assert streams[0].stopped and streams[0].closed
    assert len(streams) == 1


def test_start_twice_restarts_cleanly():
    streams = []

    def factory(**kwargs):
        stream = FakeStream(**kwargs)
        streams.append(stream)
        return stream

    capture = MicrophoneCapture(stream_factory=factory)
    capture.start(on_pcm=lambda pcm: None)
    capture.start(on_pcm=lambda pcm: None)
    assert streams[0].closed
    assert len(streams) == 2
