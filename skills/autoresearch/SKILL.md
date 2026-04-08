---
name: autoresearch
description: "Autonomous experiment loop: setup and run Karpathy-style autoresearch with fixed evaluator + mutable genome + program.md direction. Use when a project needs automated hypothesis→experiment→evaluate→keep/discard cycles."
---

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
- **SSOT for baseline**: evaluate.py writes `best_score.txt` on ADOPT. This file is the **single source of truth** for the current baseline. Do NOT duplicate the baseline value in program.md, handoff.md, or anywhere else — duplication creates cadence-conflict drift (see traces/failures/ for the diagnosed failure mode).

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
- `traces/experiments/NNN-*.md`: include representative experiments' raw output in episode traces
- Preserve verdict, score, gates, metrics in full — no selective field omission

#### Step 6: Install Evaluator Protection Hooks

The Fixed Evaluator pattern requires protecting the **entire evaluator dependency chain**.
Paper principle: "The proposer never sees test-set results; its only feedback comes from the search set."

**Protection scope**: evaluator file itself + all dependencies it imports.
Protecting only the evaluator while leaving dependencies unguarded allows manipulating evaluation results via dependency modification.

**Bash tool bypass blocking**: `PreToolUse Edit|Write` alone is insufficient.
Add a `PreToolUse Bash` hook to also block write commands like `cp`, `mv`, `sed -i`, `python -c "open(...,'w')"` targeting protected files.

```
protect-files.sh protection target determination:
1. Trace import statements in the evaluator file
2. Add all imported project modules to the protection list
3. Include data files (prevent direct modification)
```

Install both hooks and register in `.claude/settings.local.json`. **Idempotency**: if `.claude/hooks/protect-files.sh` already exists, do not overwrite — read first, diff against the canonical version, and prompt the user before any changes. If `settings.local.json` already exists, merge into the existing `hooks.PreToolUse` array instead of replacing it.

settings.local.json fragment to merge:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "bash .claude/hooks/protect-files.sh"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "bash .claude/hooks/protect-files-bash.sh"}]
      }
    ]
  }
}
```

#### Step 7: Add Autoresearch Section to CLAUDE.md

Append (or merge into existing) an Autoresearch section to the project CLAUDE.md. This section must specify:

- **Evaluator output schema**: JSON stdout key list and verdict values (agent must parse)
- **Mutable/immutable file boundary**: evaluator + dependencies = IMMUTABLE, genome = MUTABLE
- **Trace recording timing**: record immediately on ADOPT, axis exhaustion, every 10 experiments, termination
- **Trace YAML frontmatter required fields**: session, date, experiment_range, adopts, rejects, metric_start, metric_end
- **Reject code preservation**: before reverting on REJECT, capture `git diff HEAD~1` into the failures/ trace when recording triggers apply (see methodology.md)

**Idempotency**: if CLAUDE.md already contains an "Autoresearch" heading, merge new bullets only. Do not duplicate. If the 100-line CLAUDE.md cap is exceeded, split the autoresearch section to `docs/autoresearch.md` and leave a one-line reference in CLAUDE.md.

#### Step 8: Document Episode Format

Ensure `.claude/traces/experiments/` exists (created by `/init-harness`; create now if missing) and verify that the episode format from `docs/reference.md` "Experiment Episode Format" section is referenced from CLAUDE.md or a project doc. The agent must know where to find the format when writing episodes.

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
- `consecutive_rejects >= 20` → record as blocked in handoff.md + **escalate**: record in traces/failures/ with diagnosis of the structural cause, then escalate to harness-engineer. No simple retries — structural cause diagnosis required
- Context window exhausted → record as in_progress in handoff.md (not recorded in failures/ — exhaustion is a budget/session limit, not a harness diagnosis target)
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
- Numbering: next sequence number within `traces/experiments/`
- Multiple episodes possible per session (e.g., one per ADOPT)
- **harness-engineer integration**: experiment episodes are a different layer from failures/ — harness-engineer reads Exhausted Axes / Lesson sections directly

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
1. Record in `traces/failures/NNN-{name}.md` (include symptoms + supporting data)
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

This skill's evaluate.py is the fixed evaluator from docs/methodology.md — the fastest and cheapest evaluation method.
For high-stakes qualitative decisions, escalate to human review.
