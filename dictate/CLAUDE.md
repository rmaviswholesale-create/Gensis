# Project

- Language: Python 3.11+ (src layout, `src/dictate`)
- Framework: none (stdlib-first; optional `faster-whisper`, `sounddevice`, `pynput`, `pystray`, `pillow`, `pyperclip`)
- Build backend: hatchling
- Test runner: pytest (`testpaths = ["tests"]`)
- Test command: `python -m pytest`
- Coverage command: `python -m pytest --cov=dictate --cov-report=term-missing`
- Coverage target: 80% total (baseline at setup: 80%, 93 tests)
- Lint command: `python -m ruff check src tests` (14 pre-existing errors at setup, see Known Issues)
- Typecheck command: `python -m mypy src` (1 pre-existing error at setup, see Known Issues)
- Build command: none needed; install with `python -m pip install -e .`
- CI provider: none for this project (`.github/workflows` only covers the Expo examples)
- Deploy target: none. End-user Windows app, launched with `run-windows.bat` or `python -m dictate`

## Setup for a fresh environment

```
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e .
python -m pip install pytest pytest-cov ruff mypy
```

`pip install -e .` installs no runtime deps. The tests use fakes and do not need a microphone,
a display, Ollama, or the Whisper model.

# Conventions (from codebase)

- File naming: `snake_case.py`. Tests are `tests/test_<module>.py`. Shared test doubles live in `tests/fakes.py`.
- Error handling: raise a specific exception at the boundary (`ConfigError`, `ValueError` for bad WAV input).
  Catch narrow exceptions (`urllib.error.URLError`, `TimeoutError`, `OSError`). The pipeline logs and
  skips a failing chunk instead of crashing (see `test_engine_error_skips_chunk_and_continues`).
- Imports: `from __future__ import annotations` at the top of each module. Absolute `dictate.*` imports.
  Optional deps are imported inside `try/except ImportError` so tests run without the `stt` and `windows` extras.
- Logging: `log = logging.getLogger(__name__)` at module level.
- Typing: annotated public functions; `Protocol` interfaces in `src/dictate/interfaces.py`. Use `typing.Callable`/`Sequence`
  today, though ruff's UP035 wants `collections.abc`.
- Formatting: ruff, line length 100 (`[tool.ruff]` in `pyproject.toml`). No separate formatter is configured.
- Module docstrings explain design intent (threading model, latency choices). Keep that style for new modules.

# Architecture pointers

- `docs/spec-dictation.md`: requirements and acceptance criteria (AC1–AC7).
- `docs/plan-dictation.md`: slice plan.
- `progress.md`: current slice status and AC-to-test mapping. Update it when behavior changes.
- `LATER.md`: deliberately deferred ideas. Do not implement these unless asked.
- Concurrency: `PipelineRunner` serializes all events onto one worker thread. Do not add locks around `DictationPipeline`.

# Known Issues (at setup)

- `ruff check` reports 14 errors: UP035 (`typing.Callable`/`Sequence`/`Mapping` imports) and UP037 (quoted annotations) across `src/` and one C408 in `tests/test_chunker.py`. Fixing these is a separate cleanup, not part of any loop unless asked.
- `mypy src` reports `numpy` import-not-found in `transcribe.py:58`. It goes away once the `stt` extra is installed.

# Permission boundary

Do not modify without explicit permission: `config.default.json`, `config.quicktest.json`, `run-windows.bat`,
`src/dictate/inject.py` (keystroke injection), `src/dictate/hotkey.py`, the `[project.scripts]` entry point, or any
`.github/` workflow. Loops must flag these instead of changing them. See `.claude/loop-guardrails.md`.

# Loop State

Loop prompts live in `.claude/loops/`. Guardrails are in `.claude/loop-guardrails.md`. Run state is in
`.claude/loop-state.json`, which is the source of truth between sessions.

## Active Loops
(managed by Claude Code — do not hand-edit)
