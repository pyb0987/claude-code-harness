---
name: autoresearch
description: "Set up or run a Codex-compatible autoresearch loop with program.md direction, fixed JSON evaluator, mutable genome, experiments.jsonl, and .harness trace episodes. Use for measurable hypothesis -> experiment -> evaluate -> ADOPT/REJECT cycles."
---

# Autoresearch for Codex

Apply the autoresearch pattern in Codex without relying on Claude Code slash commands or `.claude/settings.local.json` hooks.

Core separation:

```text
program.md      <- human direction, constraints, rejection history
evaluate.py     <- fixed evaluator, JSON stdout, binary verdict
mutable genome  <- files Codex may modify during experiments
```

The evaluator and its dependencies are the feedback signal. Once setup is complete, Codex must not modify them during experiment runs.

## Shared Inputs

- Core methodology: `core/methodology.md` when available
- Core reference: `core/reference.md` when available
- Existing harness traces: `.harness/traces/` preferred, `.claude/traces/` reused when it already contains project history

If shared core files are unavailable because the skill was installed standalone, proceed from this skill and project-local traces.

## When To Use

Use this skill when the project has:

- a measurable objective expressible as one scalar metric
- binary guard conditions that can reject unsafe or invalid variants
- a mutable code/config surface suitable for iterative experiments
- enough evaluation speed and determinism to run repeated trials

Do not use this skill for one-off debugging, subjective design review without a fixed evaluator, business/product strategy choices, or ordinary feature work.

## Modes

This skill has two modes:

- **Setup Mode**: create or update the autoresearch harness for a project.
- **Run Mode**: execute experiments when `program.md`, `evaluate.py`, and `experiments.jsonl` already exist.

If the user asks only for a plan or review, stop at the plan. Do not edit files or start experiments unless asked.

## Setup Mode

### Step 1: Inspect and Bound the Experiment

Read raw project files directly. Identify:

- objective metric and baseline source
- guard checks and failure modes
- mutable genome files Codex may edit
- immutable evaluator files and imported project dependencies
- build/test/evaluate commands
- existing `AGENTS.md`, `program.md`, `evaluate.py`, `experiments.jsonl`, `.harness/`, `.claude/`, and CI/git hook configuration

Ask the user for missing objective or guard information only if it cannot be inferred safely.

### Step 2: Choose Trace Root

Use the existing harness trace root when present:

1. Existing `.harness/traces/`
2. Existing `.claude/traces/` when it has meaningful project history
3. New `.harness/traces/`

Ensure `{trace_root}/experiments/` exists. Do not split trace history without explicit migration intent.

### Step 3: Write `evaluate.py`

Create a project-specific evaluator with these properties:

- stdout is JSON only
- verdict is one of `ADOPT`, `REJECT_GUARD`, `REJECT_THRESHOLD`, `ERROR`
- returns a single scalar metric plus guard details
- includes a timeout or bounded execution path
- compares against a single source of truth baseline, normally `best_score.txt`
- atomically updates the baseline only on `ADOPT`

Minimum shape:

```python
"""Fixed evaluator. Codex must not modify this file during experiment runs."""

import json

THRESHOLD_PCT = 1.0


def evaluate():
    metric = ...
    baseline = ...
    guards = {"guard_1": "PASS"}
    improvement_pct = (metric / baseline - 1) * 100
    all_pass = all(value == "PASS" for value in guards.values())

    if all_pass and improvement_pct >= THRESHOLD_PCT:
        verdict = "ADOPT"
    elif not all_pass:
        verdict = "REJECT_GUARD"
    else:
        verdict = "REJECT_THRESHOLD"

    return {
        "verdict": verdict,
        "metric": metric,
        "improvement_pct": improvement_pct,
        "guards": guards,
    }


result = evaluate()
if result["verdict"] == "ADOPT":
    with open("best_score.txt", "w", encoding="utf-8") as f:
        f.write(f"{result['metric']}\\n")
print(json.dumps(result))
```

Do not duplicate the baseline value in `program.md`, handoff notes, or trace prose. Refer to `best_score.txt` instead.

### Step 4: Write `program.md`

`program.md` is the human-readable research state. It should include:

```markdown
# Auto-Search Program - {Project}

## Identity
You are an autonomous researcher for this project. Optimize through code/config experiments.

## Objective
Maximize {metric}. Current baseline is read from `best_score.txt`.

## What You Can Modify
- {mutable genome path}: {allowed changes}

## What You Cannot Modify
- `evaluate.py` and evaluator dependencies
- `program.md` except `## Rejection History`
- `best_score.txt` except through `evaluate.py`
- data or fixtures used by evaluation, unless explicitly listed as mutable

## Experiment Loop
hypothesis -> modify mutable genome -> commit -> evaluate -> ADOPT or REJECT -> log -> repeat

## Adoption Criteria
- improvement >= {threshold}% over current best
- all guards PASS

## Structural Constraints
- {domain invariants}

## Rejection History
{exhausted axes; Codex may append axis-exhaustion entries here}

## Promising Unexplored Directions
{human-curated hints}

## Logging Format
experiments.jsonl contains one full evaluator JSON result per line plus hypothesis, experiment number, commit sha, and revert status.
```

### Step 5: Initialize Runtime Files

Create or verify:

```text
program.md
evaluate.py
best_score.txt
experiments.jsonl
{trace_root}/experiments/
```

Initialize `experiments.jsonl` as an empty file. First experiment number is `1` unless existing logs show a later value.

### Step 6: Add Codex-Facing Project Instructions

Update `AGENTS.md` or a linked project doc with a concise Autoresearch section:

- evaluator command and JSON schema
- mutable genome paths
- immutable evaluator/dependency paths
- baseline source of truth (`best_score.txt`)
- trace root and experiment episode timing
- REJECT diff preservation before revert
- escalation condition: 20 consecutive REJECTs or suspected evaluator defect

If `AGENTS.md` would become too long, put details in `docs/autoresearch.md` and leave a short pointer in `AGENTS.md`.

### Step 7: Add Evaluator Protection

Codex does not consume Claude Code `PreToolUse` hooks. Use project-local enforcement instead.

Preferred protection bundle:

- a tracked file listing immutable evaluator paths, e.g. `.harness/autoresearch-protected.txt`
- a project-local check script that fails when staged or working-tree diffs modify protected paths
- a git hook and/or CI job that runs the check
- `AGENTS.md` instruction that Codex must run the check before committing experiments

Protection must cover the evaluator file and project modules/data it imports. Protecting only `evaluate.py` is insufficient if metric logic lives elsewhere.

Do not silently overwrite existing hooks or CI. If enforcement files exist, inspect and merge; if behavior differs structurally, show the diff and ask before replacing.

### Step 8: Setup Completion Check

Before ending Setup Mode, verify:

- `program.md` exists and names mutable/immutable boundaries
- `evaluate.py` emits JSON with a binary verdict
- `best_score.txt` is the baseline source of truth
- `experiments.jsonl` exists
- `{trace_root}/experiments/` exists
- `AGENTS.md` or `docs/autoresearch.md` documents the loop and trace timing
- evaluator protection is installed or the skipped reason is recorded

## Run Mode

Run Mode executes experiments when the autoresearch files already exist.

### Runtime Protocol

1. Read `program.md`, especially mutable genome paths and `## Rejection History`.
2. Read `experiments.jsonl` and resume at the next experiment number.
3. Check git status. Start from a clean worktree unless the user explicitly says the dirty state is intentional.
4. Formulate a one-line hypothesis that does not duplicate rejection history.
5. Modify only mutable genome files.
6. Commit the experiment change with `experiment: {short hypothesis}`.
7. Run `evaluate.py` and parse JSON stdout.
8. On `ADOPT`, keep the commit and append the full evaluator result to `experiments.jsonl`.
9. On `REJECT_*` or `ERROR`, preserve the diff/evaluator JSON when recording triggers apply, then revert according to the current Codex permission policy.
10. Repeat until a termination condition is reached.

Destructive revert note: if `git reset --hard HEAD~1` requires approval or conflicts with current runtime policy, request approval or stop with the exact command and preserved evidence. Never revert before preserving required diagnostic context.

### Logging Requirements

Append one JSON line per experiment to `experiments.jsonl`. Include at least:

```json
{"ts":"ISO8601","n":1,"hypothesis":"...","verdict":"ADOPT","metric":0.0,"improvement_pct":0.0,"guards":{},"sha":"...","reverted":false}
```

Preserve the evaluator's raw JSON fields. Do not summarize away guard details, metrics, or error output.

### Episode Trace Recording

Write `{trace_root}/experiments/NNN-{name}.md` immediately at milestones:

- on every `ADOPT`
- on axis exhaustion, and append that axis to `program.md ## Rejection History`
- on termination
- every 10 experiments, even with no ADOPTs

Episode traces explain why, while `experiments.jsonl` records what. Use the experiment episode format from `core/reference.md` when available.

### Termination Conditions

Stop and record status when:

- max experiments reached, default `100`
- 20 consecutive REJECTs occur
- hypothesis space appears exhausted
- evaluator defect is suspected
- budget, time, sandbox, or permission constraints prevent valid evaluation

For 20 consecutive REJECTs or suspected evaluator defect, record a failure diagnosis when triggers apply and escalate to `harness-engineer`. Do not keep retrying the same axis.

### Session Continuity

On pause, interruption, or termination, update a handoff note such as `.harness/handoff.md`:

```markdown
## Status: in_progress | blocked | paused
## Last completed: experiment n={N}, verdict={ADOPT|REJECT|ERROR}
## Current state: consecutive_rejects={count}
## Baseline: see `best_score.txt`
## Remaining
- [ ] {remaining axis or hint}
## Next entry point
{next hypothesis or decision needed}
## Git state
clean | dirty, with reason
```

Do not duplicate the numeric baseline in the handoff note.

## Evaluator Problem Detection

Suspect evaluator or guard problems when:

- all experiments fail the same guard despite diverse hypotheses
- metric improves but verdict is REJECT unexpectedly
- `ERROR` repeats for environment reasons rather than hypothesis quality
- 20 consecutive REJECTs occur while promising hypothesis space remains

When suspected, stop normal experimentation, preserve raw evaluator output, record a failure trace if triggers apply, and escalate to `harness-engineer`. Codex must not redesign `evaluate.py` during Run Mode without user confirmation.

## Output Format

For Setup Mode:

```markdown
### Autoresearch Setup
- Objective: {metric and threshold}
- Trace root: {path}
- Mutable genome: {paths}
- Immutable evaluator boundary: {paths}
- Evaluator command: {command}
- Protection: installed | skipped, with reason

### Verification
- Evaluator smoke test: PASS | FAIL | SKIPPED
- Protection check: PASS | FAIL | SKIPPED
- Notes: {sandbox/permission/network constraints}
```

For Run Mode:

```markdown
### Autoresearch Run
- Experiments run: {range}
- ADOPT: {count}
- REJECT: {count}
- Current baseline: see `best_score.txt`
- Episode traces written: {paths}
- Handoff: {path or not needed}

### Next
- Continue with: {axis/hypothesis}
- Escalate because: {reason or none}
```

## Anti-Patterns

- Modifying evaluator files during Run Mode
- Letting Codex update `best_score.txt` directly instead of through `evaluate.py`
- Duplicating baseline values in docs or traces
- Re-exploring axes already listed in `program.md ## Rejection History`
- Treating `ERROR` as a valid REJECT without diagnosing environment cause
- Reverting rejected code before preserving required diagnostic evidence
- Logging summarized evaluator results instead of raw JSON fields
- Copying Claude Code hook configuration into Codex projects as if Codex consumed it
