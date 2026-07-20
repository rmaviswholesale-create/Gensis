from __future__ import annotations

from dictate.chunker import SilenceChunker
from dictate.session import CaptureSession


class FakeRunner:
    def __init__(self):
        self.events: list = []

    def dictation_start(self):
        self.events.append("start")

    def dictation_stop(self):
        self.events.append("stop")

    def submit(self, chunk):
        self.events.append(chunk)


class FakeCapture:
    def __init__(self):
        self.on_pcm = None
        self.stopped = False

    def start(self, on_pcm):
        self.on_pcm = on_pcm
        self.stopped = False

    def stop(self):
        self.stopped = True


def make_session():
    runner, capture = FakeRunner(), FakeCapture()
    session = CaptureSession(
        runner=runner,
        capture=capture,
        chunker_factory=lambda: SilenceChunker(
            sample_rate=16000, min_silence_ms=300, min_speech_ms=150
        ),
    )
    return session, runner, capture


def speech(ms):
    import array

    return array.array("h", [8000] * (16000 * ms // 1000)).tobytes()


def silence(ms):
    return b"\x00" * (2 * 16000 * ms // 1000)


def test_begin_starts_runner_then_capture():
    session, runner, capture = make_session()
    session.begin()
    assert runner.events == ["start"]
    assert capture.on_pcm is not None


def test_audio_flows_through_chunker_to_runner():
    session, runner, capture = make_session()
    session.begin()
    capture.on_pcm(speech(500) + silence(600))
    chunks = [e for e in runner.events if e not in ("start", "stop")]
    assert len(chunks) == 1


def test_end_stops_capture_flushes_tail_then_stops_runner():
    session, runner, capture = make_session()
    session.begin()
    capture.on_pcm(speech(500))  # no silence boundary: still buffered
    session.end()
    assert capture.stopped
    assert runner.events[0] == "start"
    assert runner.events[-1] == "stop"
    chunks = [e for e in runner.events if e not in ("start", "stop")]
    assert len(chunks) == 1  # the flushed tail


def test_end_without_begin_is_noop():
    session, runner, capture = make_session()
    session.end()
    assert runner.events == []
    assert not capture.stopped


def test_begin_twice_is_idempotent():
    session, runner, _ = make_session()
    session.begin()
    session.begin()
    assert runner.events == ["start"]


def test_new_utterance_gets_fresh_chunker():
    session, runner, capture = make_session()
    session.begin()
    capture.on_pcm(speech(500))
    session.end()
    session.begin()
    session.end()  # no audio: must not re-flush the previous tail
    chunks = [e for e in runner.events if e not in ("start", "stop")]
    assert len(chunks) == 1
