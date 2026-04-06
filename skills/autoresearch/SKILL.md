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

# stdout JSON only
print(json.dumps(evaluate(...)))
```

Requirements:
- JSON stdout (agent parses this)
- Timeout guard (prevent infinite loops)
- Binary verdict: ADOPT / REJECT_GUARD / REJECT_THRESHOLD / ERROR
- Immutable: state "do not modify" in program.md

#### Step 3: Write program.md
```markdown
# Auto-Search Program — [Project Name]

## Identity
You are an autonomous researcher for [project]. Operate autonomously.
Do NOT pause. Stop at 100 experiments or hypothesis exhaustion.

## Objective
Maximize [metric]. Current best: [value].

## What You Can Modify (Mutable Genome)
- [file1] — [what can change]
- [file2] — [what can change]

## What You CANNOT Modify (Immutable)
- evaluate.py, program.md (except `## Rejection History` which the agent updates), data/*

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
7. ADOPT → keep + update baseline + log
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
## Current state: baseline metric=<value>, consecutive_rejects=<count>
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
