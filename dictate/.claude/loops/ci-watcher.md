# CI Watcher (self-paced /loop)

Paste when you have an open PR:

/loop 5m Check the CI status on the current PR. If it failed, read the failure log, identify the root cause, fix it, commit, and push. If it passed, stop. Record each check in .claude/loop-state.json.

## Instructions for the loop

Follow `.claude/loop-guardrails.md`. Read `.claude/loop-state.json` first.

- Note: this project has no CI workflow of its own. The repo's `.github/workflows` covers the Expo examples only.
  If the PR has no checks at all, say so and stop. Do not invent a pipeline.
- Each check: read the PR's check runs. Paste the status and the failing check names, if any.
- On failure: read the job log, reproduce locally with the test, lint, or typecheck command from `CLAUDE.md`,
  fix the root cause, re-run locally and paste the output, then commit and push to the PR branch.
- Do not touch the permission-boundary files (guardrail 7). Flag and stop if the fix needs them.
- Stop when checks are green, or after 3 failed fix attempts on the same failure (guardrail 5), and report
  the diagnosis.
- Record each check in `.claude/loop-state.json` under `loops.ci-watcher`.
