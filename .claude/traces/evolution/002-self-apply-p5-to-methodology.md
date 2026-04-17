---
iteration: 2
date: "2026-04-17"
type: structural
verdict: improved
principle: P5
ladder_level_before: 0
ladder_level_after: 3
files_changed:
  - "scripts/install.sh"
  - "hooks/protect-global-methodology.sh"
  - "hooks/protect-global-methodology-bash.sh"
  - "docs/operations-template.md"
  - "README.md"
  - ".claude/traces/evolution/002-self-apply-p5-to-methodology.md"
refs:
  - "docs/methodology.md (P5 — Recurring failures absorbed by structure, not rules)"
  - "commit 4ad731b (reduce concepts from 17 to 11)"
  - "commit 97ad128 (reduce to pure paper 6 principles)"
---

## Iteration 2: Self-Apply P5 Ladder Level 3 to methodology.md

Trigger: A user (also the maintainer) observed that their global copy
(~/.claude/rules/common/harness-methodology.md) had drifted 71 lines
(189 → 260) from the upstream docs/methodology.md. Investigation showed the
drift accumulated through three mechanisms:

1. **Role confusion**: The user edited the global snapshot from a user-role
   session, treating it as their own document rather than an upstream anchor.
2. **No structural barrier**: `cp docs/methodology.md ~/.claude/...` installed
   the file as normally writable. Nothing blocked or warned against edits.
3. **Implicit expectation**: The project documented "upstream anchor" as an
   informal convention, not as an enforced boundary.

The three commits referenced above show the maintainer has performed
subtractive passes on methodology.md twice (17→11 concepts, then →6 paper
principles). Each pass was necessary because the document had accumulated
non-paper material over time. The underlying cause — lack of a structural
write barrier — was never addressed; only the symptoms were cleaned up.

### Diagnosis

Applying the P5 self-check from methodology.md: "Can this failure category be
eliminated by structure rather than rules?"

- Failure category: upstream-anchor drift in user environments
- Evidence (≥3 required for P5 escalation):
  1. commit 4ad731b — 62-line cleanup of accumulated non-paper content
  2. commit 97ad128 — 27-line cleanup reducing to 6 paper principles
  3. 2026-04-17 user report — 71-line drift in a downstream copy
- Rule-level enforcement (ladder 0) has failed three times. Escalation is
  warranted.

### Change

Introduces a Single-Source + Generated-Derivative pattern for the
methodology-to-user-env pipeline, at ladder level 3.

**Source of truth** (repo-owned):
- `docs/methodology.md` — the paper anchor. Editable only by maintainers via PR.
- `docs/reference.md` — same semantics.

**Derivatives in user environment** (locked):
- `~/.claude/rules/common/harness-methodology.md` — `chmod 444` after copy.
- `~/.claude/docs/harness-reference.md` — `chmod 444` after copy.

**User overlay** (editable, never overwritten):
- `~/.claude/rules/common/harness-operations.md` — seeded once from
  `docs/operations-template.md`. Auto-loaded alongside the methodology.

**Structural barrier** (ladder level 3):
- `hooks/protect-global-methodology.sh` — PreToolUse hook matching Edit/Write
  against the locked snapshots. Returns exit 1 with a message directing the
  agent to `harness-operations.md`.
- `hooks/protect-global-methodology-bash.sh` — companion hook catching Bash
  bypass routes (`sed -i`, `>` redirect, `chmod +w` followed by overwrite,
  `python -c "open(...,'w')"`).

**Installer** (replaces the `cp` sequence in README):
- `scripts/install.sh` — idempotent. Overwrites upstream layer on every run
  (with chmod dance to handle pre-existing locked files). Preserves the user
  overlay on re-install. Copies hooks if absent. Prints the settings.json
  registration snippet rather than auto-editing the user's global settings.

### Expected Effect

- Editing the global methodology.md from within a Claude Code session returns
  a clear hook message pointing to the overlay file. No silent drift.
- `chmod +w` bypass requires `Bash` tool, which the companion hook also blocks
  when the target matches a protected path suffix.
- Re-install (`./scripts/install.sh`) updates the upstream layer without
  touching the user's accumulated operational rules in the overlay.
- Role confusion (user-vs-maintainer) becomes a non-issue: user-role sessions
  simply cannot edit the upstream layer; maintainer-role sessions work against
  the repo directly.

### Scope Boundary

This change enforces the user-role "additive-only" model. It does not constrain
the maintainer role — `docs/methodology.md` in the repo remains fully
editable by maintainers via normal git workflow. The two roles are now
separated by filesystem semantics rather than by social convention.

### Limitations

1. **Settings.json auto-registration deferred to user**: The installer prints
   the JSON snippet but does not auto-merge into `~/.claude/settings.json` to
   avoid silent modification of user configuration. Without the hook, `chmod
   444` alone blocks casual edits but not a deliberate `chmod +w && overwrite`.
2. **No CI enforcement yet**: Drift can still be introduced via PR if a
   maintainer adds non-paper content to `docs/methodology.md` itself. A keyword
   blocklist CI check is a possible Iteration 3.
3. **Does not migrate existing global drift**: Users with an already-drifted
   global copy must run the installer manually; the installer will overwrite
   their local changes. Manual diff + selective migration to
   harness-operations.md is recommended before running install on a drifted
   environment.

### Lesson

Meta-Harness's own principles apply recursively. The project had documented P5
for over a year but did not apply it to its own distribution mechanism. Three
cleanup commits should have been the evidence trigger for structural
escalation; instead each cleanup was treated as a one-off. The fix pattern
("truth source, generated derivative, protected") is exactly the pattern the
methodology prescribes — applying it to the methodology document itself is a
small but significant act of self-consistency.
