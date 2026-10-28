from __future__ import annotations

import json

import pytest

from dictate.config import ConfigError, load_config


def test_defaults_when_no_file():
    config = load_config(None)
    assert config.stt.model == "small"
    assert config.polish.mode == "ollama"
    assert config.polish.timeout_seconds == pytest.approx(3.0)
    assert config.hotkey.combo == "<ctrl>+<alt>+d"
    assert config.hotkey.mode == "toggle"
    assert config.inject.clipboard_threshold_chars == 200


def test_partial_file_merges_over_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"stt": {"model": "tiny"}, "polish": {"mode": "rules"}}))
    config = load_config(path)
    assert config.stt.model == "tiny"
    assert config.stt.compute_type == "int8"  # default retained
    assert config.polish.mode == "rules"


def test_dictionary_path_resolved_relative_to_config_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"dictionary_path": "words.json"}))
    config = load_config(path)
    assert config.dictionary_path == tmp_path / "words.json"


def test_malformed_config_raises_with_filename(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{oops")
    with pytest.raises(ConfigError, match="config.json"):
        load_config(path)


def test_unknown_polish_mode_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"polish": {"mode": "telepathy"}}))
    with pytest.raises(ConfigError, match="telepathy"):
        load_config(path)


def test_missing_explicit_config_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="nope.json"):
        load_config(tmp_path / "nope.json")


def test_discover_config_path(tmp_path):
    from dictate.config import discover_config_path

    assert discover_config_path(tmp_path) is None
    (tmp_path / "config.json").write_text("{}")
    assert discover_config_path(tmp_path) == tmp_path / "config.json"
