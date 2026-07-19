from __future__ import annotations

import wave
from dataclasses import dataclass

import pytest

from dictate.interfaces import AudioChunk
from dictate.transcribe import FasterWhisperEngine, read_wav_pcm16


@dataclass
class StubSegment:
    text: str


class StubModel:
    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.transcribe_calls: list[dict] = []

    def transcribe(self, audio, **kwargs):
        self.transcribe_calls.append({"audio": audio, **kwargs})
        return iter([StubSegment(" hello "), StubSegment("world ")]), None


def make_engine(**kwargs):
    holder = {}

    def factory(*args, **fkwargs):
        holder["model"] = StubModel(*args, **fkwargs)
        return holder["model"]

    engine = FasterWhisperEngine(model_factory=factory, **kwargs)
    return engine, holder["model"]


def test_joins_and_strips_segments():
    engine, _ = make_engine()
    text = engine.transcribe(AudioChunk(pcm16=b"\x00\x00" * 1600))
    assert text == "hello world"


def test_pcm16_scaled_to_float():
    engine, model = make_engine()
    engine.transcribe(AudioChunk(pcm16=(16384).to_bytes(2, "little", signed=True) * 100))
    audio = model.transcribe_calls[0]["audio"]
    assert audio[0] == pytest.approx(0.5, abs=0.001)


def test_language_and_model_options_passed_through():
    engine, model = make_engine(model="tiny", language="en", compute_type="int8")
    assert model.init_args[0] == "tiny"
    assert model.init_kwargs["compute_type"] == "int8"
    engine.transcribe(AudioChunk(pcm16=b"\x00\x00" * 100))
    assert model.transcribe_calls[0]["language"] == "en"


def write_wav(path, sample_rate=16000, channels=1, width=2, ms=100):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00" * (width * channels * sample_rate * ms // 1000))


def test_read_wav_pcm16(tmp_path):
    path = tmp_path / "ok.wav"
    write_wav(path)
    data, rate = read_wav_pcm16(path)
    assert rate == 16000
    assert len(data) == 3200


def test_read_wav_rejects_stereo(tmp_path):
    path = tmp_path / "stereo.wav"
    write_wav(path, channels=2)
    with pytest.raises(ValueError, match="mono"):
        read_wav_pcm16(path)


def test_read_wav_rejects_8bit(tmp_path):
    path = tmp_path / "8bit.wav"
    write_wav(path, width=1)
    with pytest.raises(ValueError, match="16-bit"):
        read_wav_pcm16(path)
