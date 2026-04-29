# Codex Adapter Backlog

Codex-specific backlog for adapter behavior that should not be pushed into the shared core. Core methodology follow-ups live in `backlog/core.md`.

## Priority Candidates

### 1. Add Codex sandbox/escalation recording template

The Codex `harness-engineer` skill says sandbox, permission, and network outcomes are first-class verification outcomes, but it does not give a compact recording template.

Potential improvement:

```markdown
- command: `{command}`
- status: PASS | FAIL | SKIPPED
- blocked_by: sandbox | permission | network | unsafe_side_effect | missing_dependency | none
- escalation_required: yes | no
- approval_reason: {short reason, if escalation is needed}
- rerun_status: {what should happen after approval or environment change}
```

Keep actual approval mechanics in Codex runtime instructions rather than duplicating them in the skill.

### 2. Clarify Codex trace-root migration behavior

Codex prefers `.harness/traces/`, but may need to reuse existing `.claude/traces/` history when a project is migrated from Claude Code.

Potential improvement:

- Define when Codex should continue using `.claude/traces/` temporarily.
- Define when it should propose migration into `.harness/traces/`.
- Define the minimum migration plan: copy/move strategy, search-set preservation, and a trace entry recording the migration.

### 3. Map stronger enforcement surfaces for Codex

Codex does not consume Claude Code `settings.local.json` hooks. Adapter docs should keep a concrete map from core enforcement levels to Codex-compatible surfaces.

Potential improvement:

- Level 1 warning: AGENTS.md reminder plus explicit verify command.
- Level 2 block: project-local script, test, CI, or git hook.
- Level 3 structural impossibility: single source, generator, protected generated derivatives, and CI/git-hook drift check.
- Future plugin hooks: document once a stable Codex plugin hook surface exists.

## Current Status

- Source review: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md`.
- Last reviewed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
