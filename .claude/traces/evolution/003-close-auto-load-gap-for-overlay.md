---
iteration: 3
date: "2026-04-17"
type: additive
verdict: improved
principle: P5
refs:
  - ".claude/traces/evolution/002-self-apply-p5-to-methodology.md"
files_changed:
  - "scripts/install.sh"
  - "README.md"
  - "docs/operations-template.md"
  - ".claude/traces/evolution/003-close-auto-load-gap-for-overlay.md"
---

## Iteration 3: Close the auto-load gap for harness-operations.md

Trigger: Immediately after iteration 002 shipped, the maintainer (same person
as user in this case) asked whether Claude Code could access both files
(methodology.md and operations.md) without problems in a new session.
Investigation revealed that the installer in 002 created the overlay file
physically on disk but did not register it in `~/.claude/CLAUDE.md`, which
is the manifest Claude Code consults to decide which rules files to inject
into each session.

### Diagnosis

Iteration 002 established the correct filesystem layout:
- `~/.claude/rules/common/harness-methodology.md` — chmod 444, upstream
- `~/.claude/rules/common/harness-operations.md` — rw, user overlay

It failed to update the auto-load mechanism. Claude Code loads:
1. `~/.claude/CLAUDE.md` (always)
2. Any file explicitly referenced from CLAUDE.md with a parseable "auto-load"
   signal (the actual mechanism is LLM-driven inference from CLAUDE.md content,
   but in practice a line like `- path (auto-loaded)` reliably triggers it)

The 002 installer assumed existing users already had `methodology.md`
referenced in their CLAUDE.md (true for this maintainer, since the prior
`cp`-based install workflow had trained users to add that line). It made no
equivalent provision for the new `operations.md` file. A fresh install on a
user without an existing CLAUDE.md, or the maintainer's own upgrade, would
leave operations.md physically present but invisible to sessions.

This is a regression: before 002, a single methodology.md held everything and
auto-loaded under a single CLAUDE.md reference. After 002, the split required
two references, but only one was documented.

### Evidence

- 2026-04-17 user question on whether both files were accessible. In this
  session, the maintainer's operations.md content was migrated but the
  session observed that it was not in its system-reminder-injected context,
  because CLAUDE.md only referenced methodology.md at that point.
- Maintainer's CLAUDE.md was manually patched mid-session to add the
  operations.md reference. This patch was a user action, not part of the
  install pipeline — another user running the same install would not receive
  it.

One evidence item is not the P5 escalation threshold (which requires ≥3), so
this iteration stays within additive territory: add missing documentation and
a detection step, not a structural barrier.

### Change

Three additive documentation/automation changes. No existing behavior is
modified.

1. **`scripts/install.sh`** now prints a CLAUDE.md registration snippet and
   detects three states:
   - CLAUDE.md absent → print a minimum template (Harness section with both
     references)
   - CLAUDE.md present but missing one or both references → warn per-file and
     print the suggested format
   - Both references present → print a success line
   Print-only; no auto-edit of CLAUDE.md. Consistent with how 002 handled
   `~/.claude/settings.json` registration.

2. **`README.md`** — adds a dedicated "auto-load requires CLAUDE.md
   registration" paragraph under the installation section, with the exact
   snippet users must add. Explicitly states that a file in
   `~/.claude/rules/common/` is not auto-loaded by itself.

3. **`docs/operations-template.md`** — adds a header warning at the top of
   the seeded overlay file. Users who open the overlay to add rules will
   immediately see the auto-load requirement. This backstops the install-time
   message for users who skip the installer output.

### Scope Boundary

This iteration does not:
- Auto-edit CLAUDE.md (user asset; install remains print-only, matching the
  settings.json pattern from 002)
- Add a pre-session validation hook that enforces the references (possible
  future iteration if registration failures recur)
- Migrate existing drifted user environments (same boundary as 002; users
  must run install and follow its prompts)

### Expected Effect

- Fresh install on a new user: installer's terminal output makes the
  registration step unmissable
- Upgrade from 002 on existing users: same output path; one-line manual
  addition to CLAUDE.md
- Users who only read files (not installer output): warning header in
  operations-template.md surfaces the requirement when they open the file

### Lesson

When splitting a previously monolithic artifact into two pieces, the
auto-load manifest is part of the artifact — not a side concern. Iteration
002 treated CLAUDE.md as "user territory, don't touch" (correct) but did not
add a visibility check for the dependency it introduced (incorrect). The
print-only + detection pattern gives both respect for user configuration
ownership and confidence that the user can see what's missing.

Generalization: when an installer introduces a new file that another
user-owned file must reference, the installer should surface the
registration status even if it cannot make the edit itself.
