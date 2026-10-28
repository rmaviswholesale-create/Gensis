# Nightly Docs Sweep (Routine, 03:07 UTC daily)

Follow `.claude/loop-guardrails.md`. Read `.claude/loop-state.json` first.

1. Read the commits from the previous 24 hours on the branch: `git log --since="24 hours ago" --stat`.
   If there are none, record `"noChanges"` in state and stop.
2. For each changed module under `src/dictate/`, check the docs that describe it: `README.md`,
   `CLAUDE.md`, `docs/spec-dictation.md`, `docs/plan-dictation.md`, `progress.md`, `LATER.md`.
3. Where a doc no longer matches the implementation (flags, config keys, file names, behavior, test names
   cited in `progress.md`), update that doc. Do not rewrite docs that are still accurate.
4. Verify the cited test names still exist: `python -m pytest --collect-only -q` and paste the summary.
5. Run `python -m pytest` and paste the summary line. Docs-only changes must not change test results.
6. Show the diff summary (guardrail 6), then create a branch `loop/docs-<YYYY-MM-DD>`, commit, push, and open a
   draft PR. If nothing needed changing, open no PR.
7. Write the run to `.claude/loop-state.json` under `loops.nightly-docs`: timestamp, commits reviewed, files changed,
   PR URL or `"noChanges"`, test summary line.
