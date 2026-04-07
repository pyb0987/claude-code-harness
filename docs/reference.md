# Harness Engineering Reference

Detailed reference loaded when init-harness or harness-engineer skills are invoked.
Not auto-loaded every session. Core principles are in docs/methodology.md

## 1. Trace Filesystem — Structure and Format

### Evolution Log Format (`traces/evolution/NNN-{name}.md`)
```markdown
---
iteration: NNN
date: "YYYY-MM-DD"
type: additive | subtractive | structural
verdict: improved | regressed | neutral
files_changed: ["file1.md", "file2.sh"]
refs: [1, 2]  # Referenced prior iteration numbers
---

## Iteration NNN: {title}
Trigger: {why was the change needed}

### Diagnosis
{Diagnosis based on reading prior traces/code/scores}
- Referenced files: {specific paths/lines}

### Change
- Diff summary: {core changes, 1-3 lines}

### Result
- Before: {pre-change metrics}
- After: {post-change metrics}

### Lesson
{Lesson for subsequent iterations to reference}
```

### Failure Diagnosis Format (`traces/failures/NNN-{name}.md`)
```markdown
---
date: "YYYY-MM-DD"
escalated_to: CLAUDE.md | docs | skill | hook | none
search_set_id: "SS-NNN"  # Reference to search-set entry if applicable
resolved: true | false
---

## Failure: {title}

### Observation
{What failed — include raw error messages, test output, execution logs}

### Root Cause
{Why it failed — specific cause in code/config/data. File:line references}

### Fix
{How it was fixed — change details}

### Prevention
{How to prevent recurrence — added rules/hooks/tests and their content}
```

### Autoresearch Failure Trace Supplement

When recording a Tier 0 autoresearch REJECT in failures/, additionally include:
- **genome diff**: `git diff HEAD~1` output (captured before revert)
- **evaluator JSON**: full evaluate.py stdout
- **causal analysis**: 1-2 line summary (why hypothesis and result diverged)

**Reject workflow**: (1) parse verdict → (2) if recording trigger applies, capture diff + JSON → (3) `git reset --hard HEAD~1` → (4) jsonl logging.
Code is unrecoverable after revert, so order matters.

### Numbering
- `NNN` is a 3-digit sequence number (001, 002, ...)
- `traces/evolution/` and `traces/failures/` within a project have independent numbering
- `{name}` is a kebab-case summary (e.g., `001-add-env-bootstrap`, `003-zscore-drift-bug`)

### Experiment Episode Format (`traces/experiments/NNN-{name}.md`)

Preserves autoresearch session results as episodes.
experiments.jsonl is a 1-line summary, insufficient for diagnosis context.
Episode traces preserve "why this hypothesis succeeded/failed" with raw context.

```markdown
---
session: "auto-search/session-YYYYMMDD-HHMMSS"
date: "YYYY-MM-DD"
experiment_range: "E1-E12"        # Experiment number range in this episode
adopts: 2                         # Number of ADOPTs
rejects: 10                      # Number of REJECTs
metric_start: 0.15               # Baseline metric at episode start
metric_end: 0.22                  # Baseline metric at episode end
---

## Episode NNN: {session summary title}

### Context
{Direction and motivation explored in this session}
- program.md direction: {research direction at this point}
- Prior episode lessons: {referenced episode numbers + key lessons}

### Key Experiments
| # | Hypothesis | Verdict | Metric | Δ% | Insight |
|---|-----------|---------|--------|-----|---------|
| E1 | ... | ADOPT | 0.18 | +5.2% | {1-line lesson} |
| E2 | ... | REJECT_GUARD | - | - | {why it failed} |

### Adopted Changes
{Summary of specific code changes from ADOPTed experiments — not diff-level but what was changed and why}

### Exhausted Axes (axes exhausted in this episode)
- {axis}: {why exhausted, supporting data}

### Lesson
{Key lessons for subsequent episodes/sessions}
- Promising directions: {remaining exploration possibilities}
- Warnings: {approaches to avoid}
```

#### Episode Recording Timing — Immediate Recording Principle
Do not wait for session end. Write immediately when milestones occur.
(Reason: if the user hits Ctrl+C, there is no recording opportunity)

- **On ADOPT**: immediately record the adopted change and rationale
- **On axis exhaustion**: record experiment range and exhaustion rationale + **add the exhausted axis to the `## Rejection History` section of program.md** (prevents re-exploration in the next session). program.md is co-managed by human and agent, so the agent can update Rejection History
- **On termination**: record full session experiment summary
- **Every 10 experiments**: write an interim summary (even without ADOPTs)
- Multiple episode files are possible per session

#### Relationship with experiments.jsonl
- `experiments.jsonl`: machine-readable 1-line log per experiment (for agent loop resumption)
- `traces/experiments/NNN-*.md`: episode-level diagnostic context for humans/agents (why?)
- Not duplication but complementary: jsonl records "what", episodes record "why"

### Trace Usage Patterns
When harness-engineer diagnoses:
1. Check the full list of `traces/evolution/` — understand prior changes and results
2. grep `traces/failures/` for similar failures
3. Check `traces/experiments/` episodes for exhausted axes and lessons
4. Read Lesson/Prevention sections of related traces
5. Verify new changes do not repeat prior confounding variables

Useful grep filters:
- `grep -l 'verdict: regressed' traces/evolution/` — find regressed changes
- `grep -l 'resolved: false' traces/failures/` — find unresolved failures
- `grep -l 'type: structural' traces/evolution/` — find structural changes

## 2. Analysis — Project Diagnosis

When applying a harness to a new project, analyze the following:

### Project Characteristics
- Type: web | mobile | game | research | backend | monorepo | hybrid
- Package manager & build system
- Framework & core dependencies
- Directory structure & architecture patterns
- Linter/formatter configuration
- Test framework & structure
- CI/CD pipeline
- Existing documentation (README, CLAUDE.md, etc.)

### Environment Mapping
- Build commands (dev, build, test, lint)
- Environment variable patterns
- Deployment targets
- External system connections (DB, API, monitoring)

## 3. Decision — What Is Needed

Determine components based on analysis results. Do not include everything.

### Required (All Projects)

| Component | Content |
|-----------|---------|
| Build | dev, build, test, lint commands |
| Conventions | Naming, structure, style rules (extracted from linter) |
| Architecture | Layer direction, dependency rules, prohibited patterns |
| Traces | `.claude/traces/` directory initialization |
| Feedback rules | Rules to prevent repeated failures (added incrementally) |

### Conditional (Only When Applicable)

| Project Characteristic | Additional Component |
|----------------------|---------------------|
| Monorepo | Workspace structure, inter-package dependency direction |
| Frontend | Component patterns, state management, routing rules |
| Backend/API | API design, DB patterns, error handling, auth flow |
| Research | Data flow, experiment structure, reproducibility rules |
| Tests exist | Test commands, coverage criteria, test patterns |
| CI exists | CI reference, lint pass conditions, merge gates |

### MCP vs CLI Decision Criteria
- Tools the model already knows (git, docker, gh, psql, curl, etc.) should use CLI over MCP
- MCP tool descriptions consume system prompt space, eating into instruction budget
- MCP should only connect to external systems not coverable by CLI

## 4. Generation — CLAUDE.md Writing Principles

### Structure
- Core instructions within 100 lines (serving as a table of contents)
- Detailed documents separated into the docs/ directory
- Imperative sentences the agent can read and act on immediately

### Prohibited
- Long-form natural language explanations
- Repeating information inferable from code/linters
- Codebase overviews, directory listings
- Exceeding 100 lines (split to docs/ if exceeded)

## 5. Search-Set — Regression Verification

### Format (`traces/search-set.md`)
```markdown
## Search Set

Curated failure cases for verifying harness changes don't regress.

### SS-001: {failure title}
- **Source**: traces/failures/003-zscore-drift-bug.md
- **Symptom**: {what went wrong}
- **verify**: `{command that can be run to check this case}`

### SS-002: {failure title}
- **Source**: traces/failures/007-missing-env-var.md
- **Symptom**: {what went wrong}
- **verify**: `{command that can be run to check this case}`
```

### Usage
- Before applying a harness change, run all `verify` commands to check for regressions
- After applying a change, run all `verify` commands again and compare results
- Each entry must have a `verify` field — an automatically executable verification command
- Add new entries when a failure is worth guarding against in future changes
