from __future__ import annotations

import array

from dictate.chunker import SilenceChunker

SR = 16000
FRAME_MS = 30


def pcm(ms: int, amplitude: int) -> bytes:
    samples = array.array("h", [amplitude] * (SR * ms // 1000))
    return samples.tobytes()


def silence(ms: int) -> bytes:
    return pcm(ms, 0)


def speech(ms: int) -> bytes:
    return pcm(ms, 8000)


def make_chunker(**kwargs) -> SilenceChunker:
    defaults = dict(
        sample_rate=SR,
        frame_ms=FRAME_MS,
        silence_threshold=500,
        min_silence_ms=300,
        min_speech_ms=150,
        max_chunk_seconds=5.0,
    )
    defaults.update(kwargs)
    return SilenceChunker(**defaults)


def drive(chunker: SilenceChunker, audio: bytes, step: int = 480) -> list:
    out = []
    for i in range(0, len(audio), step):
        out.extend(chunker.push(audio[i : i + step]))
    return out


def test_silence_only_yields_no_chunks():
    chunker = make_chunker()
    assert drive(chunker, silence(2000)) == []
    assert chunker.flush() is None


def test_speech_then_silence_yields_one_chunk():
    chunker = make_chunker()
    chunks = drive(chunker, speech(600) + silence(600))
    assert len(chunks) == 1
    assert chunks[0].sample_rate == SR
    assert chunks[0].duration_seconds >= 0.6


def test_two_bursts_yield_two_chunks():
    chunker = make_chunker()
    chunks = drive(chunker, speech(500) + silence(600) + speech(500) + silence(600))
    assert len(chunks) == 2


def test_short_blip_is_discarded():
    chunker = make_chunker()
    chunks = drive(chunker, speech(60) + silence(600))
    assert chunks == []


def test_long_speech_splits_at_max_duration():
    chunker = make_chunker(max_chunk_seconds=1.0)
    chunks = drive(chunker, speech(3500) + silence(600))
    assert len(chunks) >= 3
    assert all(c.duration_seconds <= 1.2 for c in chunks)


def test_flush_returns_trailing_speech():
    chunker = make_chunker()
    assert drive(chunker, speech(500)) == []
    tail = chunker.flush()
    assert tail is not None
    assert tail.duration_seconds >= 0.4


def test_leading_silence_is_trimmed_not_accumulated():
    chunker = make_chunker()
    chunks = drive(chunker, silence(4000) + speech(500) + silence(600))
    assert len(chunks) == 1
    assert chunks[0].duration_seconds < 2.0
