# Backlog

Repository-level backlog for non-blocking improvements discovered during harness reviews and adapter porting work.

Use this folder by ownership, not by where an issue was discovered:

| Area | File | Ownership |
|------|------|-----------|
| Core methodology | `core.md` | Agent-agnostic harness rules, trace formats, verification policy |
| Codex adapter | `codex-adapter.md` | Codex-specific runtime surfaces, sandbox behavior, AGENTS.md/plugin/git-hook integration |

Adapter reviews may uncover core work. Put those items in `core.md` so Claude, Codex, and future adapters do not solve the same problem separately.
