# Progress

Status: v0.1 complete — all 6 slices shipped.
Verified: 93 tests green, ruff clean, mypy clean, real headless E2E
(`--simulate` on jfk.wav with the tiny model, ~500ms/chunk warm on shared vCPU).

Acceptance criteria → proof:
- AC1 (hotkey end-to-end): Windows manual checklist (README) — container has no mic/display;
  component chain covered by test_hotkey + test_session + test_pipeline + test_inject
- AC2 (filler removal): tests/test_rules.py::test_spec_ac2_filler_sentence
- AC3 (dictionary): tests/test_dictionary.py::test_multi_word_override
- AC4 (Ollama down → fallback): tests/test_ollama.py::test_connection_refused_falls_back, test_timeout_falls_back
- AC5 (--simulate): tests/test_app_simulate.py + real jfk.wav run
- AC6 (empty utterance): tests/test_pipeline.py::test_empty_utterance_injects_nothing
- AC7 (engine error resilience): tests/test_pipeline.py::test_engine_error_skips_chunk_and_continues

Remaining: user-run Windows smoke checklist (README). Deferred ideas: LATER.md.
