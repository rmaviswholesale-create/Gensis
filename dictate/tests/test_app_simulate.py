from __future__ import annotations

import array
import io
import wave

from dictate.app import run_simulate
from tests.fakes import FakeEngine


def write_speech_wav(path, bursts=1):
    sr = 16000
    audio = array.array("h")
    for _ in range(bursts):
        audio.extend([8000] * (sr // 2))  # 500ms "speech"
        audio.extend([0] * (sr // 2))  # 500ms silence
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio.tobytes())


def test_simulate_prints_polished_text(tmp_path):
    path = tmp_path / "speech.wav"
    write_speech_wav(path, bursts=2)
    out = io.StringIO()
    code = run_simulate(
        path,
        engine=FakeEngine(["um hello there", "uh it works"]),
        transforms=[lambda t: t.upper()],
        out=out,
    )
    assert code == 0
    assert out.getvalue().strip() == "UM HELLO THERE UH IT WORKS"


def test_simulate_silent_wav_prints_nothing(tmp_path):
    path = tmp_path / "silent.wav"
    sr = 16000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\x00" * sr * 2)
    out = io.StringIO()
    code = run_simulate(path, engine=FakeEngine([]), transforms=[], out=out)
    assert code == 0
    assert out.getvalue() == ""
