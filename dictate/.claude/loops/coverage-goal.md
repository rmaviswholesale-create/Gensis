# Coverage Goal (in-session /goal)

Paste when you want it:

/goal test coverage is at or above the target stated in CLAUDE.md, with no regressions. Run the coverage command, identify gaps, add tests for the largest gap, re-run, repeat. Surface the coverage percentage in chat after each turn so the evaluator can read it. Stop when coverage meets the target.

## Instructions for the loop

Follow `.claude/loop-guardrails.md`. Read `.claude/loop-state.json` first.

- Target: 80% total, from `CLAUDE.md`.
- Each turn:
  1. Run `python -m pytest --cov=dictate --cov-report=term-missing` and paste the TOTAL line and the summary line.
  2. Pick the file with the most missing lines that is testable without hardware. Skip `tray.py` (pystray, GUI) and
     the Windows-only paths of `hotkey.py` and `inject.py` unless a fake can cover them. Note the skip in chat.
  3. Add tests in `tests/test_<module>.py` using `tests/fakes.py`. Do not change `src/` behavior.
  4. Re-run and paste the new TOTAL line.
- No regressions: every previously passing test must still pass. If a test fails, stop and report it (guardrail 5).
- Stop when TOTAL meets 80%. Write `"completed"` and the final percentage to `.claude/loop-state.json` under
  `loops.coverage-goal` (guardrail 8).
- Turn cap: 12 turns (guardrail 3).
