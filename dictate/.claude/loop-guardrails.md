# Loop Guardrails

Every loop in `.claude/loops/` must follow these rules.

## 1. PROOF MUST LAND IN CHAT
The /goal evaluator cannot run tools. It only reads the transcript. Always surface the actual command output in chat. Never say "tests pass" without running them and pasting the summary line.

Wrong: "All tests pass."
Right: Run `python -m pytest` and paste the exit code and summary line (e.g. `93 passed in 4.37s`, exit 0).

## 2. RE-READ FILES EVERY TURN
Never trust file state from a previous turn. Re-read every file before modifying it.

## 3. TOKEN CAP
If a loop will take more than 12 turns, stop and say why. The user decides whether to continue.

## 4. STATE IS IN .claude/loop-state.json
Read it at the start of each turn. Write to it at the end. Never rely on conversation memory for loop state.

## 5. NO SILENT FAILURES
If a command fails, surface the error in chat. If a loop cannot make progress after 3 turns, stop and report why.

## 6. DIFF BEFORE COMMIT
Before committing, show a summary of what changed and why.

## 7. PERMISSION BOUNDARY
Never modify without explicit permission: `config.default.json`, `config.quicktest.json`, `run-windows.bat`, `src/dictate/inject.py`, `src/dictate/hotkey.py`, `pyproject.toml` entry points or dependencies, `.github/` workflows, or any auth/credential handling. Flag these if a loop touches them.

## 8. CLEAN EXIT
When a loop stops, write the final state to `.claude/loop-state.json` with a `"completed"` status and a timestamp.

## 9. NO PRODUCT SCOPE CREEP
Coverage, changelog, and docs loops change tests and docs. They do not change runtime behavior in `src/` except to fix a bug a failing test exposes, and then only with a flagged diff.
