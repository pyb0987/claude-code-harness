---
name: harness-engineer
description: "Use for Codex harness evolution after repeated agent failure, failed prior prevention, or explicit harness-engineering review. Not for one-off debugging, initial setup, product logic, or broad refactors."
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

## When To Use

Use this skill for Codex harness evolution only:

| Use | Do NOT use |
|-----|------------|
| Codex repeats the same task-pattern mistake | One-off debugging or ordinary feature work |
| A prior harness prevention failed | Initial project setup (use `init-codex-harness`) |
| AGENTS.md/search-set/trace rules need review | Business logic or product architecture decisions |
| CI/lint/test failure suggests missing harness feedback | Broad refactors unrelated to agent reliability |
| Existing traces show recurring confounders | External documentation research |

If the user asks only for diagnosis or review, stop at the Proposal and Verification Plan. Do not edit files unless the user asks you to apply the harness change.

## Trace Root Selection

Select the trace root by evidence, not by fixed path preference:

1. If only one of `.harness/traces/` or `.claude/traces/` exists, use it.
2. If both exist, inspect both before choosing:
   - count files in `evolution/`, `failures/`, `experiments/`
   - check which has `search-set.md`
   - prefer the root with meaningful history, not merely the newer directory
3. If both have meaningful but divergent history, stop and propose a migration/merge plan before recording new traces.
4. If neither exists, propose initializing `.harness/traces/` with `init-codex-harness` before making harness evolution claims.

Do not create a second trace root without explicit migration intent.

## Required Diagnosis Procedure

Before starting harness evolution work, define `Done when: ...` as a specific, verifiable condition.

1. Inspect `{trace_root}/failures/` before diagnosing. Use `ls`/`rg` and read similar failures directly.
2. Inspect `{trace_root}/evolution/` for prior harness changes and regressions.
3. Inspect `{trace_root}/search-set.md`; identify Active cases before proposing changes.
4. If the project uses autoresearch, inspect `{trace_root}/experiments/` for exhausted axes and lessons.
5. Read raw command output, diffs, test failures, and relevant code. Do not rely on summaries.
6. If a similar failure exists, diagnose why the prior Prevention did not work before proposing a new one.

## Change Strategy

Apply changes in this order:

1. Additive: add missing context, verify command, AGENTS.md instruction, script, or test
2. Subtractive: remove stale/conflicting instructions
3. Structural: change workflow, generated artifacts, CI, git hooks, protected paths, or single-source generation

Keep one functional harness change per iteration. Batch only independent non-functional health fixes.

## Structural Prevention Review

Before adding or strengthening instructions, ask whether the failure can be made structurally impossible.

Escalation ladder:

1. Project instruction in `AGENTS.md`
2. Explicit verify command in `{trace_root}/search-set.md`
3. Project-local script, test, CI check, or git hook
4. Single Source + Generated Derivatives + protection

Mandatory structural review triggers:

- same failure category has 3 or more evidence items
- prior Prevention failed for the same failure category
- truth is duplicated in 2 or more places
- failure came from stale generated/docs/code derivatives

If duplicated truth exists, prefer Single Source + Generated Derivatives before adding more instructions.

## Codex-Specific Surfaces

Prefer these targets:

- `AGENTS.md` for concise project instructions
- `{trace_root}/search-set.md` for Active verification cases
- project-local scripts, tests, CI, or git hooks for enforceable rules
- Codex permission/escalation notes when sandboxing affects the workflow

Do not add Claude-only `.claude/settings.local.json` hooks for Codex unless the project is intentionally shared with Claude Code and the user asks for Claude behavior too.

## Verification Discipline

Before applying a harness change, run all Active verify commands from `{trace_root}/search-set.md` when practical.

After applying a harness change, run all relevant Active verify commands again and compare results.

If `{trace_root}/search-set.md` is missing, create it from the minimum Search-set schema before applying a functional harness change, then treat it as Active-0.

Active-0 policy:

- If no Active cases exist, do not claim regression protection.
- Search unresolved failures with `rg "resolved: false" {trace_root}/failures/`.
- Promote a relevant unresolved failure to Active, or restore an Archived case before applying functional harness changes.
- If there are no unresolved failures and no Archived cases, create a new Active seed case from the current failure or harness risk before applying a functional harness change. The seed must include an auto-executable `verify` command.
- If no executable verification can be defined, stop at Proposal and ask for the missing verification surface; do not mark the change verified.

Sandbox/permission/network outcomes are first-class verification outcomes:

- If a command cannot run because of Codex sandboxing, permission approval, missing network, or unsafe side effects, record the reason.
- Provide the exact command to run later and whether escalation is required.
- Do not convert a skipped verification into PASS.

## Recording

Record every harness change in `{trace_root}/evolution/NNN-{name}.md` with YAML frontmatter.

Record failure diagnoses in `{trace_root}/failures/NNN-{name}.md` when any trigger applies:

- failure required causal reasoning
- before/after comparison is needed to understand the fix
- new guard violation type
- result opposite to hypothesis
- suspected confounding-variable failure
- structural code change failure
- recurring failure whose Prevention failed
- unresolved failure is worth adding to the search-set

Do not record simple typos, obvious one-off fixes, or failures with no future verification value.

A `resolved: true` failure must have at least one of:

- `escalated_to` is not `none`
- an Active search-set guard covers the same pattern
- classification clearly marks it as a false alarm

Autoresearch recording rules, when the project uses autoresearch:

- Record `{trace_root}/experiments/NNN-{name}.md` immediately on ADOPT, axis exhaustion, termination, and every 10 experiments. Do not wait for the session end.
- On axis exhaustion, record the experiment range and exhaustion rationale, then add the exhausted axis to the `## Rejection History` section of `program.md` when that file is the project's research state file.
- For an autoresearch REJECT that meets failure recording triggers, capture the genome diff and evaluator JSON before reverting. The minimum command evidence is `git diff HEAD~1` plus the full evaluator stdout.
- Preserve REJECT code context before any destructive revert; reverting first loses the evidence needed for diagnosis.

## Minimum Trace Schemas

Use the full formats from `core/reference.md` when available. If the shared reference is unavailable, use these minimum schemas.

Numbering rules:

- `NNN` is a 3-digit sequence number, starting at `001`.
- `evolution/`, `failures/`, and `experiments/` have independent numbering.
- Use kebab-case names, e.g. `003-missing-verify-command.md`.
- Pick the next number by listing existing files in the target directory; do not reuse numbers.

Evolution trace:

```markdown
---
iteration: NNN
date: "YYYY-MM-DD"
type: additive | subtractive | structural
verdict: improved | regressed | neutral
files_changed: ["path"]
refs: []
---

## Iteration NNN: {title}
Trigger: {why this change was needed}

### Diagnosis
{raw-trace/code/command evidence}

### Change
{diff summary}

### Result
- Before: {verification result or baseline}
- After: {verification result or skipped reason}

### Lesson
{future guidance}
```

Failure trace:

```markdown
---
date: "YYYY-MM-DD"
escalated_to: instructions | docs | skill | hook | tool | test | ci | none
search_set_id: "SS-NNN"
resolved: true | false
---

## Failure: {title}

### Observation
{raw error, command output, diff, or behavior}

### Root Cause
{specific cause with file/line references}

### Fix
{what changed or proposal if not applied}

### Prevention
{AGENTS.md/search-set/script/test/CI/structural prevention}

### Autoresearch Supplement
{for recorded REJECTs only: genome diff from `git diff HEAD~1`, full evaluator JSON, and causal analysis captured before revert}
```

Experiment episode trace:

```markdown
---
session: "auto-search/session-YYYYMMDD-HHMMSS"
date: "YYYY-MM-DD"
experiment_range: "E1-E10"
adopts: 0
rejects: 10
metric_start: 0.0
metric_end: 0.0
---

## Episode NNN: {session summary title}

### Context
{direction and motivation explored}
- program.md direction: {research direction at this point}
- Prior episode lessons: {referenced episode numbers + key lessons}

### Key Experiments
| # | Hypothesis | Verdict | Metric | Delta | Insight |
|---|------------|---------|--------|-------|---------|
| E1 | ... | ADOPT | 0.18 | +5.2% | {1-line lesson} |
| E2 | ... | REJECT_GUARD | - | - | {why it failed} |

### Adopted Changes
{specific code changes from ADOPTed experiments and why they helped}

### Exhausted Axes
- {axis}: {why exhausted, supporting data}

### Lesson
{key lessons for later episodes or sessions}
- Promising directions: {remaining exploration possibilities}
- Warnings: {approaches to avoid}
```

Search-set file:

```markdown
---
description: "Collection of failure cases for verifying harness changes."
last_updated: "YYYY-MM-DD"
---
# Harness Search Set

## Active

### SS-NNN: {failure title}
- **Source**: traces/failures/NNN-name.md
- **Symptom**: {what went wrong}
- **verify**: `{auto-executable command}`

## Archived

### SS-NNN: {archived failure title}
- **Source**: traces/failures/NNN-name.md
- **Symptom**: {what went wrong}
- **verify**: `{auto-executable command}`
- **archived_reason**: {why this no longer needs to be active}
```

## Output Format

For diagnosis-only requests:

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
- Active search-set cases: {cases or Active-0 action}
- Commands: {commands to run}
- Recording target: {evolution/failure trace path}
```

For applied changes, add:

```markdown
### Verification Result
- Before: PASS | FAIL | SKIPPED, with key output lines
- After: PASS | FAIL | SKIPPED, with key output lines
- Skipped reason: {sandbox/permission/network/cost/unsafe side effect, if any}

### Trace Written
- Evolution: {path or "not written because ..."}
- Failure: {path or "not applicable"}
```

## Anti-Patterns

- Editing business logic while claiming to do harness diagnosis
- Using this skill for initial setup instead of `init-codex-harness`
- Adding more instructions when a test, script, CI check, or git hook can enforce the rule
- Strengthening a rule before diagnosing why the prior rule was violated
- Creating a second trace root without explicit migration intent
- Marking failures resolved without escalation or an Active verification guard
- Treating skipped verification as PASS
- Recording only a summary when raw command output or diffs are available
