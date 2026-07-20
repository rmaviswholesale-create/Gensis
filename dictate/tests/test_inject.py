from __future__ import annotations

from dictate.inject import TypingInjector


class FakeClipboard:
    def __init__(self, initial="old contents"):
        self.value = initial
        self.history: list[str] = []

    def get(self) -> str:
        return self.value

    def set(self, text: str) -> None:
        self.value = text
        self.history.append(text)


def make_injector(threshold=10, clipboard=None, **kwargs):
    events = []
    clipboard = clipboard if clipboard is not None else FakeClipboard()
    injector = TypingInjector(
        clipboard_threshold_chars=threshold,
        pre_inject_delay_ms=50,
        typer=lambda text: events.append(("type", text)),
        clipboard=clipboard,
        paste=lambda: events.append(("paste",)),
        sleep=lambda s: events.append(("sleep", s)),
        **kwargs,
    )
    return injector, events, clipboard


def test_short_text_is_typed():
    injector, events, _ = make_injector(threshold=100)
    injector.inject("hello")
    assert ("type", "hello") in events


def test_pre_inject_delay_applied_before_typing():
    injector, events, _ = make_injector(threshold=100)
    injector.inject("hi")
    assert events[0] == ("sleep", 0.05)
    assert events[1] == ("type", "hi")


def test_long_text_uses_clipboard_paste_and_restores():
    injector, events, clipboard = make_injector(threshold=5)
    injector.inject("this is long text")
    assert ("paste",) in events
    assert all(e[0] != "type" for e in events)
    assert clipboard.history[0] == "this is long text"
    assert clipboard.value == "old contents"  # restored


def test_empty_text_does_nothing():
    injector, events, _ = make_injector()
    injector.inject("")
    assert events == []


def test_clipboard_failure_falls_back_to_typing():
    class BrokenClipboard:
        def get(self):
            raise RuntimeError("no clipboard")

        def set(self, text):
            raise RuntimeError("no clipboard")

    injector, events, _ = make_injector(threshold=5, clipboard=BrokenClipboard())
    injector.inject("this is long text")
    assert ("type", "this is long text") in events
