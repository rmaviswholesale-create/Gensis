"""Text injection into the focused window.

Short text is typed via simulated unicode keystrokes (pynput → SendInput on
Windows, so accents/emoji/CJK survive). Long text goes through the clipboard
with Ctrl+V, restoring the previous clipboard contents afterwards. All OS
dependencies are injectable for tests and lazily imported in production.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Protocol

log = logging.getLogger(__name__)


class Clipboard(Protocol):
    def get(self) -> str: ...

    def set(self, text: str) -> None: ...


class TypingInjector:
    def __init__(
        self,
        clipboard_threshold_chars: int = 200,
        pre_inject_delay_ms: int = 50,
        typer: Callable[[str], None] | None = None,
        clipboard: Clipboard | None = None,
        paste: Callable[[], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._threshold = clipboard_threshold_chars
        self._delay_s = pre_inject_delay_ms / 1000
        self._typer = typer or _pynput_typer
        self._clipboard = clipboard if clipboard is not None else _PyperclipClipboard()
        self._paste = paste or _pynput_paste
        self._sleep = sleep

    def inject(self, text: str) -> None:
        if not text:
            return
        # Let the hotkey's modifier keys settle before synthesizing input,
        # otherwise the first characters land while Ctrl/Alt are still down.
        self._sleep(self._delay_s)
        if len(text) < self._threshold:
            self._typer(text)
            return
        try:
            previous = self._clipboard.get()
            self._clipboard.set(text)
            self._paste()
            self._sleep(0.15)  # give the target app time to read the clipboard
            self._clipboard.set(previous)
        except Exception:
            log.warning("clipboard injection failed; falling back to typing", exc_info=True)
            self._typer(text)


def _pynput_typer(text: str) -> None:
    from pynput.keyboard import Controller

    Controller().type(text)


def _pynput_paste() -> None:
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    with keyboard.pressed(Key.ctrl):
        keyboard.press("v")
        keyboard.release("v")


class _PyperclipClipboard:
    def get(self) -> str:
        import pyperclip

        return pyperclip.paste()

    def set(self, text: str) -> None:
        import pyperclip

        pyperclip.copy(text)
