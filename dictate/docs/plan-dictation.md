# Plan: dictate implementation

## Approach

A synchronous, dependency-free pipeline core (`DictationPipeline`) that transforms
chunks → text → polished utterance, driven by a thin threaded runner (`PipelineRunner`) fed from
OS callbacks (hotkey, audio). All OS/heavy integrations (faster-whisper, sounddevice, pynput,
pystray, Ollama HTTP) sit behind four small Protocols so the core is fully unit-testable and
platform backends slot in per-OS.

Rejected alternative: asyncio end-to-end — sounddevice/pynput deliver data on their own OS
threads anyway, so async would add an event-loop bridge at every boundary for no latency win.

## Slices

1. **Scaffold + contracts + pipeline core** (riskiest: concurrency/ordering design)
   - Files: pyproject.toml, docs/, progress.md, src/dictate/{interfaces,pipeline}.py,
     tests/{fakes,test_pipeline}.py
2. **Dictionary + rule polisher** — src/dictate/{dictionary.py,polish/rules.py} + tests
3. **STT + simulate** — src/dictate/{transcribe.py,chunker.py,app.py(--simulate)} + fixture WAV
4. **Ollama polisher** — src/dictate/polish/ollama.py + mock-HTTP tests
5. **Windows layer** — src/dictate/{hotkey.py,audio.py,inject.py} (thin, lazy imports)
6. **Tray app + config + docs** — src/dictate/{app.py,config.py}, README, manual checklist

## Risks

- Whisper model download may fail in sandboxed CI → engine is lazy; simulate falls back cleanly;
  unit tests mock the model.
- Ollama latency on CPU (1–2 s) → per-utterance polish only, hard timeout, rules fallback.
- Injection focus races (hotkey release vs first keystroke) → inject only after utterance flush;
  small configurable pre-inject delay.

## Rollback

One conventional commit per slice; `git revert` of a slice's commit restores the previous
working state.
