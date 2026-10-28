# Repo Cleanup (self-paced)

Paste when you want a cleanup:

/loop Inspect all branches, PRs, and worktrees. Recover any valuable unmerged work into a rescue branch. Delete stale branches older than 30 days after confirming they're merged or abandoned. Show evidence for each removal. Stop when the repository state is clean and intentional. Record in .claude/loop-state.json.

## Instructions for the loop

Follow `.claude/loop-guardrails.md`. Read `.claude/loop-state.json` first.

- Inspect first, change nothing yet:
  - `git branch -a --format='%(refname:short) %(committerdate:iso8601) %(upstream:track)'`
  - `git worktree list`
  - open PRs for each remote branch.
- Classify each branch: `merged` (ancestor of `master`), `open-pr` (keep), `unmerged-stale` (no PR, older than 30 days),
  `active` (younger than 30 days).
- Never delete `master`, the designated branch `claude/new-session-minulx`, or any branch with an open PR.
- For `unmerged-stale` branches with commits not on `master`: push a rescue branch `rescue/<name>-<YYYY-MM-DD>`
  first, then ask before deleting the original. This is a destructive step; confirm with the user (not a guardrail
  bypass, a confirmation request).
- Delete merged branches older than 30 days only after showing the `git log master..<branch>` evidence (empty) and the
  last commit date.
- Prune worktrees with `git worktree prune` only after checking `git worktree list` shows them as missing.
- Stop when only `master`, the designated branch, and branches with open PRs remain, and state that in chat with the
  command output. Write `"completed"` with a timestamp to `.claude/loop-state.json` under `loops.repo-cleanup`.
