"""Global hotkey → dictation start/stop.

The state machine (toggle vs push-to-talk) is plain Python and unit-tested;
the pynput listener glue is created lazily in `start()` so nothing OS-level
loads in headless environments.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from dictate.config import HOTKEY_MODES

log = logging.getLogger(__name__)


class HotkeyController:
    def __init__(
        self,
        combo: str,
        mode: str,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        if mode not in HOTKEY_MODES:
            raise ValueError(f"hotkey mode '{mode}' not one of {HOTKEY_MODES}")
        self._combo = combo
        self._mode = mode
        self._on_start = on_start
        self._on_stop = on_stop
        self._active = False
        self._listener: Any = None

    @property
    def active(self) -> bool:
        return self._active

    def hotkey_activated(self) -> None:
        """The full combo was pressed."""
        if self._mode == "toggle":
            if self._active:
                self._deactivate()
            else:
                self._activate()
        elif not self._active:  # push_to_talk; ignore key-repeat re-activations
            self._activate()

    def hotkey_released(self) -> None:
        """A key of the combo was released."""
        if self._mode == "push_to_talk" and self._active:
            self._deactivate()

    def _activate(self) -> None:
        self._active = True
        self._on_start()

    def _deactivate(self) -> None:
        self._active = False
        self._on_stop()

    def start(self) -> None:
        """Begin listening for the global hotkey (blocks nothing; own thread)."""
        from pynput import keyboard

        if self._mode == "toggle":
            self._listener = keyboard.GlobalHotKeys({self._combo: self.hotkey_activated})
        else:
            hotkey_keys = set(keyboard.HotKey.parse(self._combo))
            hotkey = keyboard.HotKey(hotkey_keys, self.hotkey_activated)

            def on_press(key: Any) -> None:
                hotkey.press(listener.canonical(key))

            def on_release(key: Any) -> None:
                canonical = listener.canonical(key)
                hotkey.release(canonical)
                if canonical in hotkey_keys:
                    self.hotkey_released()

            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener = listener
        self._listener.start()
        log.info("listening for %s (%s mode)", self._combo, self._mode)

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
