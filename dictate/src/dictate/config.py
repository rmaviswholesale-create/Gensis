"""Typed config with defaults mirroring config.default.json.

A user file overrides defaults field-by-field; anything omitted keeps its
default so a partial (or absent) config always yields a runnable app.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields, replace
from pathlib import Path

POLISH_MODES = ("ollama", "rules")
HOTKEY_MODES = ("toggle", "push_to_talk")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class HotkeyConfig:
    combo: str = "<ctrl>+<alt>+d"
    mode: str = "toggle"


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    device: str | int | None = None


@dataclass(frozen=True)
class SttConfig:
    model: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "en"


@dataclass(frozen=True)
class PolishConfig:
    mode: str = "ollama"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    timeout_seconds: float = 3.0


@dataclass(frozen=True)
class InjectConfig:
    method: str = "type"
    clipboard_threshold_chars: int = 200
    pre_inject_delay_ms: int = 50


@dataclass(frozen=True)
class Config:
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    polish: PolishConfig = field(default_factory=PolishConfig)
    inject: InjectConfig = field(default_factory=InjectConfig)
    dictionary_path: Path = Path("dictionary.json")


def discover_config_path(directory: str | Path = ".") -> Path | None:
    """Return ./config.json if present; used when no --config is given."""
    candidate = Path(directory) / "config.json"
    return candidate if candidate.exists() else None


def load_config(path: str | Path | None) -> Config:
    """Load config from `path`; None means built-in defaults."""
    config = Config()
    if path is None:
        return config
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"{path}: config file not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected a JSON object")

    for section_field in fields(Config):
        if section_field.name == "dictionary_path":
            continue
        overrides = data.get(section_field.name)
        if overrides is None:
            continue
        if not isinstance(overrides, dict):
            raise ConfigError(f"{path}: '{section_field.name}' must be an object")
        section = getattr(config, section_field.name)
        known = {f.name for f in fields(section)}
        unknown = set(overrides) - known
        if unknown:
            raise ConfigError(f"{path}: unknown key(s) in '{section_field.name}': {sorted(unknown)}")
        config = replace(config, **{section_field.name: replace(section, **overrides)})

    if "dictionary_path" in data:
        config = replace(config, dictionary_path=path.parent / str(data["dictionary_path"]))

    if config.polish.mode not in POLISH_MODES:
        raise ConfigError(
            f"{path}: polish.mode '{config.polish.mode}' not one of {POLISH_MODES}"
        )
    if config.hotkey.mode not in HOTKEY_MODES:
        raise ConfigError(
            f"{path}: hotkey.mode '{config.hotkey.mode}' not one of {HOTKEY_MODES}"
        )
    return config
