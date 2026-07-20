from __future__ import annotations

import pytest

from dictate.hotkey import HotkeyController


def make_controller(mode):
    events = []
    controller = HotkeyController(
        combo="<ctrl>+<alt>+d",
        mode=mode,
        on_start=lambda: events.append("start"),
        on_stop=lambda: events.append("stop"),
    )
    return controller, events


class TestToggleMode:
    def test_press_starts_then_stops(self):
        controller, events = make_controller("toggle")
        controller.hotkey_activated()
        controller.hotkey_activated()
        controller.hotkey_activated()
        assert events == ["start", "stop", "start"]

    def test_release_is_ignored(self):
        controller, events = make_controller("toggle")
        controller.hotkey_activated()
        controller.hotkey_released()
        assert events == ["start"]

    def test_active_property_tracks_state(self):
        controller, _ = make_controller("toggle")
        assert not controller.active
        controller.hotkey_activated()
        assert controller.active


class TestPushToTalkMode:
    def test_press_starts_release_stops(self):
        controller, events = make_controller("push_to_talk")
        controller.hotkey_activated()
        controller.hotkey_released()
        assert events == ["start", "stop"]

    def test_key_repeat_activations_do_not_restart(self):
        controller, events = make_controller("push_to_talk")
        controller.hotkey_activated()
        controller.hotkey_activated()
        controller.hotkey_activated()
        controller.hotkey_released()
        assert events == ["start", "stop"]

    def test_release_without_press_is_noop(self):
        controller, events = make_controller("push_to_talk")
        controller.hotkey_released()
        assert events == []


def test_unknown_mode_rejected():
    with pytest.raises(ValueError, match="telepathy"):
        HotkeyController("<ctrl>+d", "telepathy", lambda: None, lambda: None)
