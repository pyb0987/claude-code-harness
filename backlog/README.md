# Backlog

Repository-level backlog for non-blocking improvements discovered during harness reviews and adapter porting work.

Use this folder by ownership, not by where an issue was discovered:

| Area | File | Ownership |
|------|------|-----------|
| Core methodology | `core.md` | Agent-agnostic harness rules, trace formats, verification policy |
| Claude adapter | `claude-adapter.md` | Claude Code-specific trace roots, project hooks, slash commands, global skill install surfaces |
| Codex adapter | `codex-adapter.md` | Codex-specific runtime surfaces, sandbox behavior, AGENTS.md/plugin/git-hook integration |

Adapter reviews may uncover core work. Put those items in `core.md` so Claude, Codex, and future adapters do not solve the same problem separately.

## Theme Index

Use this index when choosing the next item. Several backlog entries describe the
same larger problem from different runtime angles; treat them as one theme unless
the adapter behavior truly differs.

| Theme | What It Covers | Related Items |
|-------|----------------|---------------|
| Distribution and install UX | How users install, activate, migrate, and eventually publish adapter bundles | `core.md` 8-9; `claude-adapter.md` 1 old install smoke; `codex-adapter.md` 4-5, 16-19 |
| Hook and protection enforcement | Runtime hooks, pre-commit/CI guardrails, protected-file checks, schema drift, and honest protection-level reporting | `claude-adapter.md` 1 hook/runtime follow-ups; `codex-adapter.md` 3, 12-15; `core.md` 10 |
| Verification and release gates | Deterministic verify commands, adapter smoke tests, release checklist, and staged/index semantics for repository checks | `core.md` 3, 9-10; `claude-adapter.md` 1 fixture/temp-git follow-ups; `codex-adapter.md` 6, 11, 18-19 |
| Trace lifecycle and migration | Trace-root selection, partial initialization, history tie-breakers, archive restore, and `.claude/traces` to `.harness/traces` migration | `core.md` 2, 4-5; `claude-adapter.md` 1 path contract; `codex-adapter.md` 2 |
| Autoresearch semantics | Detecting autoresearch projects, preserving evaluator boundaries, experiment episode traces, rejection history, and local-only protection states | `core.md` 1, 6; `codex-adapter.md` 12, 15 |
| Codex execution model | Codex sandbox, permissions, sub-agent availability, MCP/tool policy, browser/web usage, and skipped verification reporting | `codex-adapter.md` 1, 7-9 |
| Documentation boundary and examples | Keeping core as what/why, adapters as runtime how, and adding realistic examples without duplicating methodology | `core.md` 7; `codex-adapter.md` 10-11; adapter README/example follow-ups |

## Consolidation Notes

- `codex-adapter.md` 4, 5, 16, 17, 18, and 19 are one distribution epic:
  local plugin first, generated bundle integrity, activation smoke, then
  marketplace policy.
- `codex-adapter.md` 3, 12, 13, 14, and 15 are one protection epic: checker
  implementation, hook templates, hook output smoke, schema drift, and
  protection-level reporting.
- `core.md` 9-10 plus adapter smoke items are one release-gate epic. Keep
  adapter-specific smoke tests in adapter backlogs, but keep the checklist and
  staged/index policy in core.
- `core.md` 2, 4, and 5 plus `codex-adapter.md` 2 are one trace-lifecycle epic.
  Core should define the general trace-history rules; Codex should only define
  how `.claude/traces` and `.harness/traces` interact in that runtime.
- `claude-adapter.md` currently has one umbrella item because the Claude-specific
  debt is narrow: path consistency and smoke coverage around the existing
  Claude surfaces. Split it only if it grows beyond trace/hook/install smoke.
