# Nightly Changelog (Routine, 03:11 UTC daily)

Follow `.claude/loop-guardrails.md`. Read `.claude/loop-state.json` first.

1. List the previous 24 hours of commits: `git log --since="24 hours ago" --no-merges --format='%h %s'`.
   If there are none, record `"noChanges"` and stop.
2. Keep only user-relevant changes: new features, behavior changes, fixes, removed options, config or
   dictionary format changes. Skip pure refactors, test-only commits, and formatting.
3. Add entries to the `## [Unreleased]` section of `CHANGELOG.md`, following https://keepachangelog.com
   (`Added`, `Changed`, `Fixed`, `Removed`). One line per entry, written for a user, not a developer.
   Do not invent entries. If a commit message is unclear, read the diff before writing the entry.
4. Run `python -m pytest` and paste the summary line. Changelog edits must not change test results.
5. Show the diff summary (guardrail 6), then branch `loop/changelog-<YYYY-MM-DD>`, commit, push, and open a
   draft PR.
6. Write the run to `.claude/loop-state.json` under `loops.nightly-changelog`: timestamp, commits used, entries
   added, PR URL or `"noChanges"`, test summary line.
