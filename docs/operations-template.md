# Harness Operations — User Overlay

This file is the user-editable overlay for the claude-code-harness methodology.
It is auto-loaded every session alongside `harness-methodology.md`.

## What belongs here

Operational rules, personal preferences, and project-independent conventions
that extend the methodology without modifying it. Examples:

- Model routing preferences (e.g., which tasks default to which model)
- Skill invocation rules (e.g., which skills are allowed per model tier)
- Personal workflow overlays (e.g., a session-handoff format you favor)
- Terminology aliases (e.g., "Tier 0 = Fixed Evaluator" shorthand for personal use)
- Additive interpretations of the six core principles

## What does NOT belong here

- Anything that contradicts `harness-methodology.md` — the upstream snapshot is
  the anchor. If you disagree with it, open a PR against claude-code-harness
  instead of silently overriding it.
- Project-specific rules — those go in that project's `CLAUDE.md`.
- Secrets, credentials, or any sensitive data.

## Why a separate file

The methodology file is locked (`chmod 444`) and protected by hooks so that
extending the harness means adding to this file, not mutating the upstream
snapshot. This preserves a stable anchor for the six Meta-Harness principles
while leaving you freedom to accumulate operational wisdom on top.

---

<!-- Your operational rules below. Start empty; add as patterns stabilize. -->
