# Spec: System-Wide Dictation ("dictate")

## Problem

Typing is the bottleneck for capturing thought. Existing OS dictation is cloud-bound, injects raw
unpunctuated text full of filler words, and can't learn project jargon. This app gives any text
field on the machine low-latency, locally-processed, polished dictation with a user-owned
dictionary — no audio ever leaves the device.

## Requirements

1. User can start/stop dictation with a configurable global hotkey from any application
   (toggle mode) or hold it to talk (push-to-talk mode).
2. While active, microphone audio is captured at 16 kHz mono and split into chunks at speech/
   silence boundaries; each chunk is transcribed locally in under ~500 ms on a modern CPU.
3. Transcribed text passes through, in order: (a) local dictionary overrides, (b) polish —
   filler-word removal, punctuation, capitalization, grammar. Polish runs via a local Ollama
   model; if Ollama is unreachable or exceeds its timeout, a rule-based polisher is used instead
   and dictation never stalls.
4. The polished text is injected into the currently focused OS text field (Windows first) via
   simulated unicode typing, with clipboard-paste fallback for long text.
5. A JSON dictionary file maps spoken forms to written forms (e.g. "get hub" → "GitHub"),
   matched case-insensitively on word boundaries, applied before polish so the polish pass
   cannot mangle jargon.
6. Configuration (hotkey, STT model, polish mode, Ollama host/model, dictionary path) lives in a
   JSON config file with sane defaults; a missing config file must not prevent startup.
7. A `--simulate <wav>` CLI mode runs the full pipeline on a WAV file and prints the injected
   text to stdout, enabling headless end-to-end verification.

## Acceptance criteria

- AC1: With the app running and a text editor focused, pressing the hotkey, speaking, and
  pressing it again results in polished text appearing in the editor.
- AC2: Speaking "um so basically the uh meeting is tomorrow" injects text without "um"/"uh"/
  "so basically" fillers, correctly punctuated and capitalized.
- AC3: With `{"get hub": "GitHub"}` in the dictionary, speaking "push it to get hub" injects
  text containing "GitHub".
- AC4: With Ollama stopped, dictation still works (rule-polished) with no added latency beyond
  the configured timeout.
- AC5: `python -m dictate --simulate tests/fixtures/hello.wav` prints the polished transcription
  and exits 0.
- AC6: An utterance containing no speech injects nothing (no stray whitespace or keystrokes).
- AC7: A transcription-engine error on one chunk does not crash the app or lose subsequent
  chunks.

## Non-goals

- macOS / Linux injection backends (interfaces are kept ready; not built now).
- Cloud STT engines, streaming partial hypotheses UI, GUI settings window.
- Auto-start on boot, signed installer / PyInstaller packaging.
- Multi-language tuning (Whisper language is configurable but only English is validated).

## Edge cases & failure modes

- Empty/silence-only utterance → nothing injected (AC6).
- Engine raises on a chunk → chunk skipped, error logged once, pipeline continues (AC7).
- Ollama down / timeout / non-200 / garbage response → rule polish fallback (AC4); the polished
  result must never be an LLM apology or wrapper prose (strict prompt + response validation).
- Dictionary file missing → warning, empty dictionary; malformed JSON → clear error naming the file.
- Overlapping hotkey presses (start while flushing) → events are queued; utterances are processed
  strictly in order; a second "start" while recording is idempotent.
- Very long dictation (> clipboard_threshold_chars) → clipboard-paste injection, original
  clipboard restored afterwards.
- Unicode (accents, emoji, CJK) survives injection intact — simulated typing is unicode-based,
  never scancode-based.

## Data model

- `AudioChunk { pcm16: bytes (LE mono PCM16), sample_rate: int }`
- `dictionary.json`: `{ "overrides": { "<spoken form>": "<written form>", ... } }`
- `config.json`: see `config.default.json` — hotkey{combo,mode}, audio{sample_rate,device},
  stt{model,device,compute_type,language}, dictionary_path,
  polish{mode,ollama_host,ollama_model,timeout_seconds}, inject{method,clipboard_threshold_chars}.
