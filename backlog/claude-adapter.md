# Claude Adapter Backlog

Claude Code-specific follow-ups live here. Shared methodology belongs in
`backlog/core.md`; Codex runtime work belongs in `backlog/codex-adapter.md`.

## Priority Candidates

### 1. Keep Claude trace and hook paths mechanically consistent

Decision implemented: Claude adapter docs now use concrete Claude Code paths for
adapter-owned artifacts, and pre-commit validates the path contract.

This check is index-oriented lexical documentation validation. It does not
prove Claude Code runtime hook activation, `.claude/settings.local.json` schema
acceptance, or actual `/init-harness` generated project output.

Implemented foundation:

- Claude adapter trace paths resolve to `.claude/traces/...`.
- Claude hook scripts resolve to `.claude/hooks/...`.
- Claude hook settings resolve to `.claude/settings.local.json`.
- `scripts/check-claude-adapter-paths.py` rejects bare `traces/...`,
  `traces/`, `failures/`, `hooks/...`, `hooks/`, and `settings.local.json` in
  Claude adapter docs.
- The tracked pre-commit hook runs the path contract check after compatibility
  mirror validation.
- The checker discovers indexed `adapters/claude/**/*.md` surfaces plus the
  indexed README Claude section; core docs and Codex docs are intentionally
  outside its scope.

Remaining follow-up work:

- Add an old Claude install command smoke test while compatibility mirrors exist.
- Add a project-fixture smoke test that runs `/init-harness` output expectations
  against a minimal target project once command execution can be tested
  mechanically.
- Add temp-git fixture coverage for the path checker so real `git add`,
  `git rm`, and unstaged dirty-file flows prove the index-vs-working-tree
  semantics end to end.
- Add Claude hook settings schema/runtime activation smoke coverage when it can
  be tested mechanically.
- Track repo-wide staged-content semantics for compatibility mirror checks in
  `backlog/core.md`.

## Current Status

- Source review: external session found Claude adapter trace/hook path drift as
  the largest remaining operability issue.
