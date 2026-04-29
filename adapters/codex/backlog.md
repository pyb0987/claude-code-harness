# Codex Adapter Backlog

Non-blocking quality backlog for the Codex adapter. These items come from the strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` that passed at 9/10. They are not release blockers, but resolving them should make future Codex agents rely less on implicit judgment.

## Priority Candidates

### 1. Add autoresearch detection heuristics

Current wording says "if the project uses autoresearch", which leaves detection to the agent.

Potential improvement:

- Treat a project as autoresearch when two or more of these are present: `program.md`, `evaluate.py`, `experiments.jsonl`, `auto-search/session-*`, `{trace_root}/experiments/`.
- If only one signal exists, inspect nearby docs before deciding.
- If signals conflict, record uncertainty in the proposal instead of applying autoresearch-specific changes blindly.

### 2. Define meaningful trace history tie-breakers

When both `.harness/traces/` and `.claude/traces/` exist, the skill asks the agent to choose the root with meaningful history.

Potential improvement:

- Prefer roots with `search-set.md` and Active cases.
- Prefer roots with unresolved failures, recent evolution entries, or experiment episodes relevant to the current issue.
- Treat divergent non-empty roots as a migration question, not as a normal write target.

### 3. Strengthen Active seed verification quality rules

The skill requires an auto-executable verify command, but does not yet define quality criteria.

Potential improvement:

- Verify commands should be deterministic, non-interactive, and fail with a non-zero exit code on regression.
- Prefer local commands that avoid network and high cost.
- Record sandbox, permission, or network requirements explicitly.
- Avoid verify commands that only print information without checking the failure pattern.

### 4. Add Codex sandbox/escalation recording template

The skill says sandbox, permission, and network outcomes are first-class verification outcomes, but it does not give a compact recording template.

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

## Later Improvements

### 5. Handle partially initialized trace roots

A trace root may exist while one or more subdirectories are missing.

Potential improvement:

- After selecting a trace root, check for `evolution/`, `failures/`, `experiments/`, and `search-set.md`.
- For applied harness changes, create missing minimum directories/files before writing traces.
- For diagnosis-only requests, report missing trace infrastructure in the proposal.

### 6. Specify Archived case restore and re-archive workflow

The skill allows restoring Archived search-set cases but does not say when to re-archive them.

Potential improvement:

- Restore Archived cases when the same failure class recurs or when validating a harness change that touches the same prevention.
- Re-archive after the new prevention has passed and the case no longer needs active regression coverage.
- Update `archived_reason` with the date and reason for re-archive.

### 7. Expand standalone autoresearch reference details

The skill now includes an experiment episode schema, but standalone users may still benefit from a short relationship map.

Potential improvement:

- State that `experiments.jsonl` records machine-readable "what" and episode traces record diagnostic "why".
- Include a minimum `program.md ## Rejection History` example.
- Clarify that episode traces may be written multiple times in one session.

## Current Status

- Last strict multi-review result: 9/10 pass across Codex runtime fit, methodology fidelity, and practical usability.
- Current committed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Recommended next quality pass: start with autoresearch detection heuristics, then trace-root tie-breakers, then verify-command quality rules.
