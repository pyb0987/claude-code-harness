---
description: Analyze project and generate a Meta-Harness (traces + CLAUDE.md + hooks + domain skills)
---

# /init-harness

Analyze a project and configure its Meta-Harness.
Core elements: Traces, Additive Modification, Fixed Evaluator, Skill Document quality.

## Workflow

### Step 1: Load Methodology

Read docs/reference.md (Section 1 Analysis through Section 3 Generation).
Core principles are in docs/methodology.md (auto-loaded every session).

### Step 2: Analyze Project

Scan the project directly with an Explore agent:
- Type, tech stack, directory structure, architecture patterns
- Existing CLAUDE.md, .claude/ directory, linters/formatters, CI/CD
- Test framework, build commands
- Existing hooks, skills, documents

Determine components based on analysis results per Section 3 Decision criteria.

### Step 3: Initialize Trace Filesystem

Create `.claude/traces/` directory and empty search-set template:
```
mkdir -p .claude/traces/{evolution,failures,experiments}
```

```markdown
# traces/search-set.md
---
description: "Collection of failure cases for verifying harness changes. After changes, confirm these cases don't recur."
last_updated: "YYYY-MM-DD"
---
# Harness Search Set
After harness changes, verify effectiveness using active cases in this list.
Update last_updated when adding/removing items.

## Operational Policy
- When Active reaches 0, the regression safety net vanishes → restore an Archived entry's verify to Active, or run `grep -l 'resolved: false' .claude/traces/failures/` to register an unresolved failure as a new SS
- Archive criteria: (a) the linked failure's `escalated_to` is filled (absorbed into CLAUDE.md / hook / tool) AND (b) another active guard exists for the same pattern — if either is missing, keep it in Active

## Active
### SS-001: {first failure scenario identified from project analysis}
- **Symptom**: {risk found in Step 2 analysis — e.g., deploying without tests, ignoring type errors}
- **verify**: `{auto-executable verification command}`
- **ref**: (linked to traces/failures/ when recorded later)
## Archived
(Resolved cases with low regression risk)
```

**Seed entry creation rule**: write the most frequent or critical failure scenario from Step 2 analysis as SS-001. The verify field must be an auto-executable shell command. Examples by project type:
- TypeScript: `tsc --noEmit 2>&1 | tail -5; echo "EXIT: $?"`
- Python: `pytest -x -q 2>&1 | tail -5; echo "EXIT: $?"`
- Godot: `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests/ -glog=1 -gexit 2>&1 | tail -10`

**Evolution log is written in Step 7** (recorded after all components are confirmed).

> **Note**: Autoresearch-specific layer (evaluator protection hooks, autoresearch CLAUDE.md section, experiments/ episode format documentation, raw output preservation) is **not** installed by init-harness. It is installed by `/autoresearch` Setup Mode when (and only when) the user adopts the Fixed Evaluator pattern. This separation lets a project add autoresearch later without re-running init-harness, and keeps init-harness universal.

### Step 4: Write/Enhance CLAUDE.md

Write or enhance project CLAUDE.md:

1. **If existing CLAUDE.md**: merge, don't overwrite. If existing file exceeds 100 lines, split excess to docs/ and replace with reference links to compress under 100 lines
2. **Stay within 100 lines** — split to docs/ if exceeded
3. Exclude rules already enforced by linters (record intent only)
4. Check for duplicates/conflicts with global rules (~/.claude/rules/common/)
5. **Harness section required**:
   - Hook list + each hook's enforcement level (blocking/warning)
   - traces/ structure
   - **Change strategy**: Additive first -> Subtractive -> Structural (one at a time, confounding variable isolation)
   - **Failure escalation loop**: a `resolved: true` entry in `traces/failures/*.md` must satisfy at least one of — (a) `escalated_to` is not empty (absorbed into CLAUDE.md / hook / tool), (b) an active search-set guard for the same pattern exists. If neither holds, do not mark it resolved
   - **Sub-agent triggers**: reference docs/methodology.md "Sub-Agent Invocation" — three categories (multi-review for qualitative judgment, parallel Explore for independent exploration, generic sub-agent for context firewall). Prefer over-invoking to under-invoking
   - Protected files (if applicable)

### Step 5: Configure Hooks

Propose hooks appropriate for the project type. Select only applicable ones from the recipe below.
Explain "why needed" for each proposal. Don't add if user declines.

#### Hook Recipe (by project type)

PostToolUse (Edit|Write) hooks — auto-verification on code changes:

| Project Type | Hook Target Pattern | Command | Enforcement | Purpose |
|-------------|-------------------|---------|-------------|---------|
| TypeScript | `*.ts\|*.tsx` | `tsc --noEmit 2>&1 \| tail -20` | **Blocking** (exit 1) | Catch type errors immediately |
| Python (typed) | `*.py` | `mypy {changed_file} 2>&1 \| tail -10` | **Blocking** (exit 1) | Type hint verification |
| Python (sim/test) | `sim/*.py\|test/*.py` | `pytest -x -q 2>&1 \| tail -15` | **Blocking** (exit 1) | Test break detection |
| Monorepo | Per-package | Run only changed package's build/test | **Blocking** (exit 1) | Prevent full build |
| Doc-code sync | Design doc related code | echo warning message | **Warning** (echo only) | Design doc cross-reference reminder |

**Enforcement policy**:
- **Blocking (exit 1)**: verification with programmatic pass/fail judgment. Blocks tool execution on failure.
- **Warning (echo only)**: verification not programmatically possible, needs human judgment. Message output only.
- **Default**: build/type/test = blocking. Doc sync/design reference = warning.

Hook writing principles:
- Match file_path from `$CLAUDE_TOOL_INPUT` with grep
- On success: 1-line summary only (save context)
- On failure: tail last N lines only (no full output)
- Blocking hooks must `exit 1` on failure (PreToolUse: blocks tool execution, PostToolUse: emphasizes warning)
- Write in settings.local.json (project scope, not global)
- If existing settings.local.json: Read first, then merge (no overwriting)

hooks JSON schema (settings.local.json):
```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash|Edit|Write", "hooks": [{"type": "command", "command": "...", "timeout": 5000}]}
    ],
    "PostToolUse": [
      {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "..."}]}
    ]
  }
}
```
- `matcher`: tool name pattern (`|` for OR). `Bash`, `Edit`, `Write`, `Read`, etc.
- `type`: always `"command"`. `timeout`: in ms (default none, add when needed).
- `command`: shell command. Access tool input JSON via `$CLAUDE_TOOL_INPUT`.

Hook coverage priority:
1. **Build break prevention** (highest): catch type check/compile errors immediately
2. **Test break prevention**: auto-run tests for changed code paths
3. **Lint/format**: style consistency (only for projects with linters)
4. **Doc-code sync**: code change doc verification alerts for projects with master documents

### Step 6: Domain Skill Decision

Determine whether the project needs domain expertise.

**Immediate creation conditions** (all must be met):
- Planning docs/domain knowledge are abundant
- Domain rules in CLAUDE.md expected to exceed 20 lines
- Recurring expert judgment needed (e.g., card balancing, strategy design, API design)

**Create later** (default):
- Record domain rules in CLAUDE.md first
- Split when same question repeats, CLAUDE.md exceeds 20 lines of domain rules, or anti-patterns accumulate

Domain skills go in `.claude/skills/{name}/SKILL.md`.
Skills are "how to" documents, not agent definitions.

**Skill document quality criteria** (paper: "skill document quality = highest leverage"):
- **State prohibitions and goals**, leave diagnosis methods free (agent decides)
- Define role, directory structure, CLI commands, output format
- Include Anti-patterns section (prohibited patterns learned from past failures)
- Debug with 3-5 short test iterations before production runs

### Step 6.5: Verify Multi-Review Skill Availability

Check whether `multi-review` is installed as a global skill at `~/.claude/skills/multi-review/SKILL.md`.

- **If installed**: confirmed. The harness can invoke `/multi-review` for qualitative multi-perspective decisions.
- **If missing**: instruct the user to copy it from this repository:
  ```bash
  cp -r {repo}/skills/multi-review ~/.claude/skills/multi-review
  ```
  Multi-review is a **global dependency**, not a per-project install. It is shipped in this repo as the source of truth so that the methodology is self-contained, but it is consumed from the global skill location.

Rationale: multi-review is the tactical mechanism for the "qualitative multi-perspective judgment" trigger documented in docs/methodology.md "Sub-Agent Invocation". Without it, that trigger has no implementation.

### Step 7: Write Evolution Log

After all components (CLAUDE.md, hooks, skills) are confirmed, write the initial evolution log:

`traces/evolution/001-initial-harness.md`:
- iteration 1, date, type: additive, verdict: neutral
- Record actually added hooks/rules/tests and their rationale
- Format: see reference.md Section 1

### Step 8: Completion Verification

All items below must pass for init-harness to be complete:

- [ ] `.claude/traces/{evolution,failures,experiments}/` directories exist
- [ ] `traces/search-set.md` template created
- [ ] `traces/evolution/001-initial-harness.md` written (Step 7)
- [ ] CLAUDE.md includes Harness section (hooks, traces/, change strategy, sub-agent triggers)
- [ ] Multi-review skill availability verified (`~/.claude/skills/multi-review/SKILL.md` exists, or user instructed to install from `{repo}/skills/multi-review/`)
- [ ] CLAUDE.md within 100 lines (split to docs/ complete if exceeded)
- [ ] Hooks registered in `settings.local.json`
- [ ] `.claude/agents/` directory was NOT created
- [ ] (if skill created in Step 6) `.claude/skills/{name}/SKILL.md` exists + Anti-patterns section included + domain rules migrated from CLAUDE.md
- [ ] No duplicates between global rules (~/.claude/rules/common/) and CLAUDE.md
- [ ] Every `resolved: true` entry in `traces/failures/*.md` has a non-empty `escalated_to` or is linked to an active search-set guard (exception: `classification: false_alarm` does not require escalation)
- [ ] `traces/search-set.md` has at least 1 Active entry (if 0, restore an Archived item or register an unresolved failure)

## Important

- Start with minimal viable harness — incrementally strengthen via feedback loop
- Include only "agent will fail without this", not "nice to have"
- **Do NOT create agent teams/orchestrators/agent definition files (.claude/agents/)** — Meta-Harness focuses on single-agent environment optimization. Subagents (evaluator, explore, multi-review critics, etc.) are allowed for context isolation and tactical decision support — this is single-agent tool usage, not multi-persona collaboration. See docs/methodology.md "Sub-Agent Invocation" for the three trigger categories
- Achieve full coverage via hooks + explicit done conditions. Avoid over-installing hooks

## Hook Configuration Example (settings.local.json)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/auto-format.sh",
            "timeout": 10000
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/protect-files.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```
