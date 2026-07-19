# Progress

Current slice: 4 — Ollama polisher
Done: slices 1-3 (pipeline core; dictionary + rules; SilenceChunker, FasterWhisperEngine, config loader,
CLI --simulate; 60 tests green; real E2E verified on jfk.wav, ~500ms/chunk warm with tiny model)
Next: failing tests for OllamaPolisher (mock HTTP server: success, timeout, non-200, garbage), then implement
