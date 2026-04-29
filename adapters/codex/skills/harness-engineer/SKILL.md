---
name: harness-engineer
description: "Diagnose repeated Codex agent failures and evolve a project harness using raw traces, search-set verification, AGENTS.md updates, and structural prevention. Use when Codex repeats a mistake, harness rules need evolution, or a Codex-compatible harness needs review."
---

# Harness Engineer for Codex

Evolve the environment that lets Codex work reliably. This skill handles failure response and harness evolution for existing Codex-compatible harnesses. New harness creation is handled by `init-codex-harness`.

## Shared Inputs

- Core methodology: `core/methodology.md` when available
- Core reference: `core/reference.md` when available
- Project trace root: selected from the project itself, not assumed globally

If shared core files are unavailable because the skill was installed standalone, proceed from this skill and read project-local traces directly.

## Objective

Diagnose from raw project evidence and propose the smallest harness change that prevents recurrence.

## Trace Root Selection

Use the first existing path in this order:

1. `.harness/traces/`
2. `.claude/traces/`

If neither exists, propose initializing `.harness/traces/` with `init-codex-harness` before making harness evolution claims.

Do not split history by creating `.harness/traces/` when `.claude/traces/` already contains project harness history unless the user explicitly asks for migration.

## Required Diagnosis Procedure

1. Inspect `{trace_root}/failures/` before diagnosing. Use `ls`/`rg` and read similar failures directly.
2. Inspect `{trace_root}/evolution/` for prior harness changes and regressions.
3. If the project uses autoresearch, inspect `{trace_root}/experiments/` for exhausted axes and lessons.
4. Read raw command output, diffs, test failures, and relevant code. Do not rely on summaries.
5. If a similar failure exists, diagnose why the prior Prevention did not work before proposing a new one.

## Change Strategy

Apply changes in this order:

1. Additive: add missing context, verify command, AGENTS.md instruction, script, or test
2. Subtractive: remove stale/conflicting instructions
3. Structural: change workflow, generated artifacts, CI, git hooks, or protected paths

Keep one functional harness change per iteration. Batch only independent non-functional health fixes.

## Codex-Specific Surfaces

Prefer these targets:

- `AGENTS.md` for concise project instructions
- `{trace_root}/search-set.md` for Active verification cases
- project-local scripts, tests, CI, or git hooks for enforceable rules
- Codex permission/escalation notes when sandboxing affects the workflow

Do not add Claude-only `.claude/settings.local.json` hooks for Codex unless the project is intentionally shared with Claude Code and the user asks for Claude behavior too.

## Verification

Before and after a harness change, run relevant Active verify commands from `{trace_root}/search-set.md` when practical. Record PASS/FAIL and key output lines in the evolution trace.

If verification is skipped, record why and provide the exact command to run later.

## Recording

Record every harness change in `{trace_root}/evolution/NNN-{name}.md` with YAML frontmatter.

Record failure diagnoses in `{trace_root}/failures/NNN-{name}.md` when any trigger applies:

- new guard violation type
- result opposite to hypothesis
- structural code change failure
- recurring failure whose prevention failed

A `resolved: true` failure must have at least one of:

- `escalated_to` is not `none`
- an Active search-set guard covers the same pattern
- classification clearly marks it as a false alarm

## Output Format

```markdown
### Diagnosis
- Cause: {specific cause with file/line or trace references}
- Prior similar cases: {trace references or "none"}
- Prevention review: {why prior prevention worked, failed, or did not apply}

### Proposal
- Change type: additive | subtractive | structural
- Content: {specific change}
- Rationale: {why this prevents recurrence}
- Risk: {confounders or compatibility concerns}

### Verification Plan
- Active search-set cases: {cases}
- Commands: {commands to run}
- Recording target: {evolution/failure trace path}
```

## Anti-Patterns

- Editing business logic while claiming to do harness diagnosis
- Adding more instructions when a test, script, CI check, or git hook can enforce the rule
- Creating a second trace root without explicit migration intent
- Marking failures resolved without escalation or an Active verification guard
- Recording only a summary when raw command output or diffs are available
