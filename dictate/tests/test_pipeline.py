"""Behavioral tests for the pipeline core and its threaded runner."""

from __future__ import annotations

import time

import pytest

from dictate.pipeline import DictationPipeline, PipelineRunner
from tests.fakes import (
    FakeEngine,
    RecordingInjector,
    chunk,
    exclaim_transform,
    upper_transform,
)


def make_pipeline(texts, transforms=(), stream=False):
    injector = RecordingInjector()
    engine = FakeEngine(texts)
    pipe = DictationPipeline(
        engine=engine, transforms=list(transforms), injector=injector, stream=stream
    )
    return pipe, engine, injector


class TestUtteranceMode:
    def test_injects_polished_utterance_once(self):
        pipe, _, injector = make_pipeline(
            ["hello", "world"], transforms=[upper_transform, exclaim_transform]
        )
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["HELLO WORLD!"]

    def test_transforms_applied_in_order(self):
        pipe, _, injector = make_pipeline(
            ["a"], transforms=[exclaim_transform, upper_transform]
        )
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["A!"]

    def test_empty_utterance_injects_nothing(self):
        pipe, _, injector = make_pipeline([])
        pipe.start_utterance()
        pipe.end_utterance()
        assert injector.injected == []

    def test_whitespace_only_transcription_injects_nothing(self):
        pipe, _, injector = make_pipeline(["  ", ""])
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == []

    def test_engine_error_skips_chunk_and_continues(self):
        pipe, _, injector = make_pipeline(["before", RuntimeError("boom"), "after"])
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["before after"]

    def test_two_utterances_are_independent(self):
        pipe, _, injector = make_pipeline(["one", "two"])
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.end_utterance()
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["one", "two"]

    def test_feed_outside_utterance_is_ignored(self):
        pipe, engine, injector = make_pipeline(["stray"])
        pipe.feed(chunk())
        assert engine.calls == 0
        assert injector.injected == []

    def test_end_without_start_is_noop(self):
        pipe, _, injector = make_pipeline([])
        pipe.end_utterance()
        assert injector.injected == []


class TestStreamMode:
    def test_injects_each_chunk_with_trailing_space(self):
        pipe, _, injector = make_pipeline(
            ["hello", "world"], transforms=[upper_transform], stream=True
        )
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["HELLO ", "WORLD "]

    def test_stream_skips_empty_chunks(self):
        pipe, _, injector = make_pipeline(["", "hi"], stream=True)
        pipe.start_utterance()
        pipe.feed(chunk())
        pipe.feed(chunk())
        pipe.end_utterance()
        assert injector.injected == ["hi "]


class TestPipelineRunner:
    def wait_for(self, predicate, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.005)
        return False

    def test_processes_events_in_order(self):
        pipe, _, injector = make_pipeline(["hello", "world"], transforms=[upper_transform])
        runner = PipelineRunner(pipe)
        runner.start()
        runner.dictation_start()
        runner.submit(chunk())
        runner.submit(chunk())
        runner.dictation_stop()
        assert self.wait_for(lambda: injector.injected == ["HELLO WORLD"])
        runner.close()

    def test_multiple_utterances_in_order(self):
        pipe, _, injector = make_pipeline(["one", "two"])
        runner = PipelineRunner(pipe)
        runner.start()
        for _ in range(2):
            runner.dictation_start()
            runner.submit(chunk())
            runner.dictation_stop()
        assert self.wait_for(lambda: injector.injected == ["one", "two"])
        runner.close()

    def test_close_drains_pending_events(self):
        pipe, _, injector = make_pipeline(["tail"])
        runner = PipelineRunner(pipe)
        runner.start()
        runner.dictation_start()
        runner.submit(chunk())
        runner.dictation_stop()
        runner.close()
        assert injector.injected == ["tail"]

    def test_close_is_idempotent(self):
        pipe, _, _ = make_pipeline([])
        runner = PipelineRunner(pipe)
        runner.start()
        runner.close()
        runner.close()

    def test_double_start_while_recording_is_idempotent(self):
        pipe, engine, injector = make_pipeline(["a"])
        runner = PipelineRunner(pipe)
        runner.start()
        runner.dictation_start()
        runner.dictation_start()
        runner.submit(chunk())
        runner.dictation_stop()
        runner.close()
        assert injector.injected == ["a"]
        assert engine.calls == 1


class TestAudioChunk:
    def test_duration(self):
        from dictate.interfaces import AudioChunk

        one_second = AudioChunk(pcm16=b"\x00" * 32000, sample_rate=16000)
        assert one_second.duration_seconds == pytest.approx(1.0)
