---
name: init-codex-harness
description: "Initialize or update a Codex-compatible harness for a project using the shared Code Harness methodology. Use when the user asks to apply codex-harness, initialize a harness for Codex, convert a Claude harness to Codex, or set up trace/search-set driven project instructions."
---

# Init Codex Harness

Bootstrap a project harness for Codex while keeping the methodology sourced from `core/`.

## Inputs

- Shared methodology: `core/methodology.md`
- Shared reference: `core/reference.md`
- Codex project template: bundled `assets/AGENTS.md.template` (adapter compatibility mirror: `adapters/codex/templates/AGENTS.md.template`)

If this skill is installed outside the repository and shared `core/` files are unavailable, use the workflow below and the bundled AGENTS template; state that shared references were not locally available.

## Objective

Create the minimal project-local structure Codex needs to work reliably:

```text
.harness/
└── traces/
    ├── evolution/
    ├── failures/
    ├── experiments/
    └── search-set.md
AGENTS.md
```

Prefer `.harness/traces/` for runtime-neutral projects. If the project already has `.claude/traces/`, keep it and document that Codex should use the existing trace root to avoid splitting history.

## Workflow

### Step 1: Inspect the Project

Read raw files, not summaries:

- package/build files
- existing `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.harness/`, `.codex/`
- test, lint, typecheck, build commands
- CI configuration
- docs that define architecture or domain constraints

Use `rg --files` first. Keep inspection targeted.

### Step 2: Choose Trace Root

Use this order:

1. Existing `.harness/traces/`
2. Existing `.claude/traces/`
3. New `.harness/traces/`

Do not create both `.claude/traces/` and `.harness/traces/` in the same project unless the user explicitly asks for split histories.

### Step 3: Create Trace Filesystem

Create:

```text
{trace_root}/evolution/
{trace_root}/failures/
{trace_root}/experiments/
{trace_root}/search-set.md
```

`search-set.md` must use the Active/Archived format from `core/reference.md` and contain at least one Active case with an executable `verify` command. Choose the most important command found during inspection, usually typecheck, tests, lint, or build.

### Step 4: Write or Update AGENTS.md

If `AGENTS.md` exists, merge without overwriting. Keep it concise.

Required sections:

- Build: dev/build/test/lint/typecheck commands discovered from the project
- Architecture: only non-obvious boundaries that tools cannot infer
- Harness: trace root, search-set policy, change strategy, verification rule
- Codex Notes: permission/escalation or local workflow facts that affect Codex

Do not duplicate rules already enforced by linters, tests, or typecheckers. Mention the command instead.

### Step 5: Verification Discipline

Codex does not consume Claude Code `PostToolUse` hooks. Replace hook assumptions with explicit verification:

- Before meaningful harness changes, run Active `search-set.md` verify commands when practical.
- After code or harness changes, run the relevant verify commands.
- Record PASS/FAIL and key output lines in the evolution trace.

If verification is expensive or unsafe, record why it was skipped and what command should be run later.

### Step 6: Write Initial Evolution Trace

Write `{trace_root}/evolution/001-initial-codex-harness.md` with YAML frontmatter and sections for Trigger, Diagnosis, Change, Result, and Lesson.

### Step 7: Completion Check

Confirm:

- Trace directories exist
- `search-set.md` has at least one Active executable `verify`
- `AGENTS.md` names the trace root and verification policy
- Initial evolution trace exists
- No Claude-only hook configuration was added for Codex

## Output

Report:

- trace root chosen
- files created or changed
- Active search-set verify command
- verification result or reason skipped
- any Claude harness history reused
