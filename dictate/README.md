# dictate

System-wide, fully local voice-to-text. Press a global hotkey in any app, speak, and polished
text — filler words removed, grammar and punctuation fixed, your jargon spelled your way —
is typed straight into the focused text field. No audio or text ever leaves your machine.

```
hotkey ─► mic (16 kHz) ─► VAD chunker ─► faster-whisper (local)
       ─► dictionary overrides ─► polish (Ollama LLM, rule-based fallback) ─► typed into active window
```

## Install (Windows)

Requires Python 3.11+.

```powershell
cd dictate
pip install -e ".[stt,windows]"
```

Optional but recommended — local LLM polish via [Ollama](https://ollama.com):

```powershell
ollama pull llama3.2:3b   # once
```

If Ollama isn't running, dictate automatically falls back to its built-in rule-based polisher
(filler removal + punctuation heuristics); dictation never stalls.

## Run

```powershell
python -m dictate                    # defaults: Ctrl+Alt+D toggle, "small" model, Ollama polish
python -m dictate --config my.json   # custom config
```

A gray tray dot appears; it turns red while recording. Press **Ctrl+Alt+D**, speak, press it
again — the polished text is typed into whatever window has focus. Text longer than 200 chars
is pasted via the clipboard (and your previous clipboard contents are restored).

First run downloads the Whisper model (~460 MB for "small"; use `"model": "base"` or `"tiny"`
in config for smaller/faster).

## Configuration

Copy `config.default.json` to `config.json` and edit; anything omitted keeps its default.

| Key | Default | Notes |
| --- | --- | --- |
| `hotkey.combo` | `<ctrl>+<alt>+d` | pynput syntax |
| `hotkey.mode` | `toggle` | or `push_to_talk` (hold to speak) |
| `stt.model` | `small` | `tiny`/`base`/`small`/`medium`, or a local CTranslate2 path |
| `polish.mode` | `ollama` | or `rules` (instant, no LLM) |
| `polish.ollama_model` | `llama3.2:3b` | any pulled Ollama model |
| `polish.timeout_seconds` | `3.0` | LLM budget before rule-based fallback |
| `dictionary_path` | `dictionary.json` | resolved relative to the config file |
| `inject.clipboard_threshold_chars` | `200` | longer text pastes instead of types |

### Dictionary

`dictionary.json` maps spoken forms to written forms, matched case-insensitively on word
boundaries **before** the polish pass so the LLM can't mangle your jargon:

```json
{ "overrides": { "get hub": "GitHub", "jason": "JSON", "cube control": "kubectl" } }
```

## Headless verification

No mic needed — run the whole pipeline on a WAV file (mono 16-bit):

```sh
python -m dictate --simulate path/to/speech.wav
```

## Development

```sh
uv venv && uv pip install -e . --group dev
uv run pytest          # 92 tests, no audio hardware or models required
uv run ruff check .
```

The core pipeline is dependency-free; OS and model integrations sit behind small protocols
(`interfaces.py`) with everything heavy imported lazily. See `docs/spec-dictation.md` and
`docs/plan-dictation.md`.

## Manual smoke checklist (Windows)

1. `python -m dictate` → gray tray dot appears; log line shows the hotkey.
2. Focus Notepad → hotkey → say "um hello world" → hotkey → "Hello world." appears (no "um").
3. Repeat in a browser URL bar and VS Code.
4. Say "push it to get hub" → text contains "GitHub" (dictionary).
5. Stop Ollama (`ollama stop` / quit) → dictate keeps working with rule-based polish.
6. Dictate a long paragraph (>200 chars) → text is pasted; previous clipboard is restored.
7. `push_to_talk` mode: hold hotkey while speaking, release → text appears.
8. Tray → Quit → process exits cleanly.

## Known limitations

- Windows-only injection today (macOS/Linux backends are LATER.md).
- Chunked STT trades a little accuracy at chunk boundaries for latency; the `small` model on a
  modern CPU transcribes each chunk in roughly the 300–500 ms range.
- Ollama polish adds ~1–2 s (CPU) after you stop speaking; set `polish.mode` to `rules` for
  instant injection.
