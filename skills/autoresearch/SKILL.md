---
name: autoresearch
description: "Autonomous experiment loop: setup and run Karpathy-style autoresearch with fixed evaluator + mutable genome + program.md direction. Use when a project needs automated hypothesis→experiment→evaluate→keep/discard cycles."
---

<!-- Compatibility mirror of `adapters/claude/skills/autoresearch/SKILL.md`. Edit the canonical source, not this file. -->

# Autoresearch Protocol

Apply the Karpathy autoresearch pattern to projects.
Core: humans set direction (program.md) only; the agent autonomously runs the experiment loop.

## When to Activate

### User trigger
`/autoresearch`, "set up autonomous experiment loop", "apply autoresearch"

### Auto-suggest signal
- Project has a measurable objective and needs iterative experimentation
- Grid search, hyperparameter tuning, strategy optimization, etc.

## 3-File Architecture (Karpathy Principle)

```
program.md      ← Human domain (direction, constraints, rejection history)
evaluate.py     ← Fixed evaluation (immutable, binary verdict, JSON stdout)
mutable genome  ← Agent domain (code the agent freely modifies)
```

This separation is key. If the agent modifies evaluate.py, it contaminates self-evaluation.

## Mode: Setup vs Run

This skill operates in two modes.

---

### Setup Mode (once per project)

Run when first applying autoresearch to a project.

#### Step 1: Define Objective Function
```
Q: What are you optimizing? (single scalar metric)
Q: What guards are needed? (binary pass/fail constraints)
Q: What is the improvement threshold? (adopt if >= X% above baseline?)
```

#### Step 2: Write evaluate.py
```python
# Template — customize per project
"""Fixed evaluator. THIS FILE IS IMMUTABLE — agent must NOT modify it."""

import json, sys, signal

EVAL_TIMEOUT = 300  # 5 minutes

def evaluate(variant, baseline):
    # 1. Run variant experiment
    # 2. Compute metric (single scalar)
    # 3. Check guards (binary pass/fail)
    # 4. Compare to baseline
    metric = ...
    guards = {"guard_1": "PASS" if ... else "FAIL", ...}
    improvement = (metric / baseline_metric - 1) * 100
    all_pass = all(v == "PASS" for v in guards.values())

    if improvement >= THRESHOLD and all_pass:
        verdict = "ADOPT"
    elif not all_pass:
        verdict = "REJECT_GUARD"
    else:
        verdict = "REJECT_THRESHOLD"

    return {"verdict": verdict, "metric": metric, "improvement_pct": improvement, "guards": guards}

# Atomically update SSOT baseline on ADOPT
result = evaluate(...)
if result["verdict"] == "ADOPT":
    with open("best_score.txt", "w") as f:
        f.write(f"{result['metric']}\n")

# stdout JSON only
print(json.dumps(result))
```

Requirements:
- JSON stdout (agent parses this)
- Timeout guard (prevent infinite loops)
- Binary verdict: ADOPT / REJECT_GUARD / REJECT_THRESHOLD / ERROR
- Immutable: state "do not modify" in program.md
- **SSOT for baseline**: evaluate.py writes `best_score.txt` on ADOPT. This file is the **single source of truth** for the current baseline. Do NOT duplicate the baseline value in program.md, handoff.md, or anywhere else — duplication creates cadence-conflict drift (see `.claude/traces/failures/` for the diagnosed failure mode).

#### Step 3: Write program.md
```markdown
# Auto-Search Program — [Project Name]

## Identity
You are an autonomous researcher for [project]. Operate autonomously.
Do NOT pause. Stop at 100 experiments or hypothesis exhaustion.

## Objective
Maximize [metric]. Current baseline is read from `best_score.txt`
(SSOT, machine-managed by evaluate.py — do NOT duplicate the value here).

## What You Can Modify (Mutable Genome)
- [file1] — [what can change]
- [file2] — [what can change]

## What You CANNOT Modify (Immutable)
- evaluate.py, program.md (except `## Rejection History` which the agent updates), data/*
- `best_score.txt` — machine-managed by evaluate.py. Neither agent nor human edits directly.

## Experiment Loop
[standard loop — see Runtime Protocol below]

## Adoption Criteria
- [metric] improvement ≥ [X]% over current best
- Guards must ALL PASS: [list guards]

## Structural Constraints (NEVER violate)
- [domain-specific invariants]

## Rejection History — EXHAUSTED AXES (DO NOT REVISIT)
[grows over time]

## Promising Unexplored Directions (Hints)
[human-curated suggestions]

## Session Handoff Protocol
[standard handoff — experiments.jsonl resume + .claude/handoff.md]

## Logging Format (experiments.jsonl)
{"ts": "ISO8601", "n": 1, "hypothesis": "...", "metric": ..., "improvement_pct": ..., "verdict": "...", "guards": {...}, "sha": "...", "reverted": true}
```

#### Step 4: Write Launcher
```bash
#!/bin/bash
# auto-search.sh — creates branch + optional headless execution
MODE="${1:-interactive}"
MAX_BUDGET="${2:-5.00}"

git checkout -b "auto-search/session-$(date +%Y%m%d-%H%M%S)"

if [ "$MODE" = "headless" ]; then
  claude -p --dangerously-skip-permissions --max-budget-usd "$MAX_BUDGET" \
    "Read program.md and execute the auto-search loop"
fi
```

#### Step 5: Initialize experiments.jsonl
Create empty file. First experiment is n=1.

**Raw output preservation**: evaluate.py's JSON stdout is critical diagnostic material. Preserve originals, not summaries:
- `experiments.jsonl`: record each experiment's full JSON output as 1 line (machine parseable)
- `.claude/traces/experiments/NNN-*.md`: include representative experiments' raw output in episode traces
- Preserve verdict, score, gates, metrics in full — no selective field omission

#### Step 6: Install Evaluator Protection Hooks

The Fixed Evaluator pattern requires protecting the **entire evaluator dependency chain**.
Paper principle: "The proposer never sees test-set results; its only feedback comes from the search set."

**Protection scope**: evaluator file itself + all dependencies it imports.
Protecting only the evaluator while leaving dependencies unguarded allows manipulating evaluation results via dependency modification.

**Bash tool bypass blocking**: `PreToolUse Edit|Write` alone is insufficient.
Add a `PreToolUse Bash` hook to also block write commands like `cp`, `mv`, `sed -i`, `python -c "open(...,'w')"` targeting protected files.

**Protection target determination**:
1. Trace import statements in the evaluator file
2. Add all imported project modules to the protection list
3. Include data files (prevent direct modification)

> **Dependency**: both canonical templates use `jq` for JSON parsing of `$CLAUDE_TOOL_INPUT`. Naive regex extraction (`grep -oE '"command"\s*:\s*"[^"]*"'`) is **broken** — it halts at the first escaped quote inside a JSON string and silently truncates commands like `echo \"x\" > evaluate.py` or `python -c "open('evaluate.py','w')..."`, allowing bypass. Install jq (`brew install jq` / `apt install jq`) before enabling these hooks. If jq is unavailable, fail closed: have the hook `exit 1` with a "jq missing" error rather than running a fragile regex fallback.

**Canonical `.claude/hooks/protect-files.sh` template** (customize PROTECTED_BASENAMES per project):
```bash
#!/bin/bash
# protect-files.sh — block Edit/Write on evaluator + dependencies
# Invoked by PreToolUse hook with $CLAUDE_TOOL_INPUT JSON.

command -v jq >/dev/null || { echo "BLOCKED: jq required for protect-files.sh" >&2; exit 1; }

# Match by exact basename or exact relative path. Avoid bare 'evaluate.py' as a
# suffix glob — that would also block 'notevaluate.py'.
PROTECTED_BASENAMES=(
  "evaluate.py"
  # "metric.py"
)
PROTECTED_PATHS=(
  # "lib/metric.py"
  # "data/baseline.json"
)

FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH")
for b in "${PROTECTED_BASENAMES[@]}"; do
  if [ "$BASENAME" = "$b" ]; then
    echo "BLOCKED: $b is an evaluator file. Modifying it would contaminate self-evaluation." >&2
    exit 1
  fi
done
for p in "${PROTECTED_PATHS[@]}"; do
  # Match exact path or path-suffix anchored on '/'
  if [ "$FILE_PATH" = "$p" ] || [[ "$FILE_PATH" == */"$p" ]]; then
    echo "BLOCKED: $p is a protected evaluator dependency." >&2
    exit 1
  fi
done
exit 0
```

**Canonical `.claude/hooks/protect-files-bash.sh` template** (blocks Bash bypass):
```bash
#!/bin/bash
# protect-files-bash.sh — block write commands targeting protected files via Bash.
# Catches cp, mv, sed -i, tee, python -c "open(...,'w')", echo > redirects.

command -v jq >/dev/null || { echo "BLOCKED: jq required for protect-files-bash.sh" >&2; exit 1; }

PROTECTED_PATTERNS=(
  "evaluate\.py"
  # Mirror basenames/paths from protect-files.sh
)

# jq -r '.command' correctly handles JSON-escaped quotes inside the command string.
COMMAND=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // empty')
[ -z "$COMMAND" ] && exit 0

# Detect write-intent verbs targeting protected patterns
WRITE_VERBS='(\bcp\b|\bmv\b|sed -i|\btee\b|>|>>|python.* -c .*open\([^)]*,[^)]*["\x27]w)'
for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$WRITE_VERBS" && echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: write command targets protected evaluator file ($pattern)." >&2
    exit 1
  fi
done
exit 0
```

Install both hooks (`chmod +x` after writing) and register in `.claude/settings.local.json`. Verify protection with a smoke test before enabling: run `CLAUDE_TOOL_INPUT='{"command":"echo \"x\" > evaluate.py"}' bash .claude/hooks/protect-files-bash.sh; echo $?` and confirm exit 1 (BLOCKED).

**Idempotency rules** (re-entry on already-harnessed projects like chain-army):
- **`.claude/hooks/protect-files.sh` already exists**: read it, compare against the canonical template above. If identical (modulo PROTECTED_FILES customization), skip. If differs structurally, show the diff and prompt the user before any change. Never silently overwrite.
- **`.claude/hooks/protect-files-bash.sh` already exists**: same rule.
- **`.claude/settings.local.json` does not exist**: create with the fragment below as the full content.
- **`.claude/settings.local.json` exists but has no `hooks.PreToolUse` array**: add a new `PreToolUse` array containing the two entries below, while preserving any existing `PostToolUse` or other top-level keys.
- **`.claude/settings.local.json` exists with a `hooks.PreToolUse` array**: append the two entries below to that array. Skip any entry whose `command` already matches (idempotent).

Fragment to merge into `hooks.PreToolUse`:
```json
[
  {
    "matcher": "Edit|Write",
    "hooks": [{"type": "command", "command": "bash .claude/hooks/protect-files.sh"}]
  },
  {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "bash .claude/hooks/protect-files-bash.sh"}]
  }
]
```

#### Step 7: Add Autoresearch Section to CLAUDE.md

Append (or merge into existing) an Autoresearch section to the project CLAUDE.md. This section must specify:

- **Evaluator output schema**: JSON stdout key list and verdict values (agent must parse)
- **Mutable/immutable file boundary**: evaluator + dependencies = IMMUTABLE, genome = MUTABLE
- **Trace recording timing**: record immediately on ADOPT, axis exhaustion, every 10 experiments, termination
- **Trace YAML frontmatter required fields**: session, date, experiment_range, adopts, rejects, metric_start, metric_end
- **Reject code preservation**: before reverting on REJECT, capture `git diff HEAD~1` into the `.claude/traces/failures/` trace when recording triggers apply (see methodology.md)

**Idempotency**: if CLAUDE.md already contains an "Autoresearch" heading, merge new bullets only. Do not duplicate. If the 100-line CLAUDE.md cap is exceeded, split the autoresearch section to `docs/autoresearch.md` and leave a one-line reference in CLAUDE.md.

#### Step 8: Document Episode Format

Ensure `.claude/traces/experiments/` exists (created by `/init-harness`; create now if missing) and verify that the episode format from `~/.claude/docs/harness-reference.md` "Experiment Episode Format" section is referenced from CLAUDE.md or a project doc. The agent must know where to find the format when writing episodes.

#### Setup Completion Checklist

Before exiting Setup Mode, verify:
- [ ] evaluate.py written, immutable boundary documented
- [ ] program.md written with rejection history section
- [ ] auto-search.sh launcher exists
- [ ] experiments.jsonl initialized (empty)
- [ ] `.claude/hooks/protect-files.sh` and `protect-files-bash.sh` installed
- [ ] `.claude/settings.local.json` has both hooks registered (PreToolUse Edit|Write + PreToolUse Bash)
- [ ] CLAUDE.md has Autoresearch section (output schema, mutable/immutable boundary, trace timing, frontmatter fields, reject preservation)
- [ ] `.claude/traces/experiments/` exists and episode format is referenced

#### Reference
See the examples/ directory for a reference implementation.

---

### Run Mode (every session)

The loop the agent executes when program.md already exists.

#### Runtime Protocol
```
1. Read program.md (direction + rejection history)        [first session only]
   → Confirm mutable genome file paths from "What You Can Modify" section
2. Read experiments.jsonl → last n → resume from n+1     [every session]
3. Formulate hypothesis (1-line, must not duplicate rejection history)
4. Implement change (modify only mutable genome files specified in program.md)
5. git commit -m "experiment: [hypothesis]"
6. Run evaluate.py → parse JSON
7. ADOPT → keep + log to experiments.jsonl
     (baseline auto-updated by evaluate.py in best_score.txt — agent does NOT manually update any baseline doc)
   REJECT → git reset --hard HEAD~1 + log
8. Repeat from 3 (until budget or consecutive reject limit)
```

#### Termination Conditions
- `n >= MAX_EXPERIMENTS` (default: 100)
- `consecutive_rejects >= 20` → record as blocked in handoff.md + **escalate**: record in `.claude/traces/failures/` with diagnosis of the structural cause, then escalate to harness-engineer. No simple retries — structural cause diagnosis required
- Context window exhausted → record as in_progress in handoff.md (not recorded in `.claude/traces/failures/` — exhaustion is a budget/session limit, not a harness diagnosis target)
- ERROR verdict → revert + try different approach (not stop)

#### Episode Trace — Immediate Recording (do NOT wait for session end)

Episode traces are written **immediately at milestones**. Do not batch-write at session end.
(Reason: if the user hits Ctrl+C, there is no recording opportunity)

**Recording triggers** (write immediately when any applies):
1. **On ADOPT**: immediately record adopted change and rationale
2. **On axis exhaustion**: record experiment range and exhaustion rationale + **add exhausted axis to program.md `## Rejection History` section** (prevents re-exploration in next session). program.md is a human-agent co-managed document, so the agent can update Rejection History
3. **On termination**: record full session experiment summary
4. **Every 10 experiments**: interim summary (even without ADOPTs)

Episode file: `.claude/traces/experiments/NNN-{name}.md`
- experiments.jsonl is a machine-readable 1-line log; episodes provide diagnostic context ("why?")
- Format: see reference.md "Experiment Episode Format" section
- Numbering: next sequence number within `.claude/traces/experiments/`
- Multiple episodes possible per session (e.g., one per ADOPT)
- **harness-engineer integration**: experiment episodes are a different layer from `.claude/traces/failures/` — harness-engineer reads Exhausted Axes / Lesson sections directly

#### Session Continuity

On termination, update `.claude/handoff.md`:
```
## Status: in_progress | blocked | paused
## Last completed: experiment n=<N>, verdict=<ADOPT|REJECT>
## Current state: consecutive_rejects=<count>
  (baseline value: see best_score.txt — do NOT duplicate here)
## Remaining:
- [ ] <remaining exploration axes or unexplored hints>
## Next entry point: <suggested next hypothesis>
## Git state: clean | dirty
```
Next session reads handoff.md + latest episode traces to maintain continuity.

---

## Evaluator Problem Detection → Harness Feedback Loop

When structural problems with evaluate.py itself are suspected (gradient dead zone, guard malfunction, metric distortion, etc.):
1. Record in `.claude/traces/failures/NNN-{name}.md` (include symptoms + supporting data)
2. Escalate to harness-engineer for diagnosis
3. evaluate.py is immutable, so **the agent does not modify it directly** — redesign after user confirmation

Suspicion signals: all experiments fail on the same guard, metric improves but verdict is REJECT, consecutive REJECTs with sufficient remaining hypothesis space.

## What This Skill Does NOT Do

These are human-agent collaboration areas that are not automated:

- **Meta-level judgment**: "This methodology itself is inadequate"
- **Structural contradiction discovery**: "This conflicts with strategy DNA"
- **Axis exhaustion verdict**: "This direction is no longer worth exploring"
- **Next research axis selection**: Setting new program.md direction
- **evaluate.py redesign**: Reviewing the validity of evaluation criteria themselves

When these judgments are needed, escalate to human intervention.

## Evaluator Integration

This skill's evaluate.py is the fixed evaluator from `~/.claude/rules/common/harness-methodology.md` — the fastest and cheapest evaluation method. Repo source: `core/methodology.md`.
For high-stakes qualitative decisions, escalate to human review.
