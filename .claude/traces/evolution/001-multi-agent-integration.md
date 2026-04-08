---
iteration: 1
date: "2026-04-08"
type: structural
verdict: improved
files_changed:
  - "skills/multi-review/SKILL.md"
  - "docs/methodology.md"
  - "commands/init-harness.md"
  - "skills/autoresearch/SKILL.md"
  - ".claude/traces/evolution/001-multi-agent-integration.md"
refs: []
commits:
  - "38d51fe feat: integrate multi-review skill and sub-agent invocation triggers"
  - "971174d refactor: migrate autoresearch-specific install from init-harness to /autoresearch"
  - "fd8bdc8 docs: translate multi-review SKILL.md to English"
  - "(pending) fix: address iter1 multi-review concerns (O1, O3, O4, G1, M1)"
---

## Iteration 1: Multi-Agent Integration into Meta-Harness

Trigger: User raised the question of whether to revert from Meta-Harness to a multi-agent architecture, given that multi-agent provides three real benefits (context separation, evaluator independence, multi-perspective). The decision was to integrate, not replace — Meta-Harness as policy layer, sub-agents as tactical mechanism.

### Diagnosis

Three gaps identified through dialogue:

1. **Tactical mechanism gap**: The methodology had no documented sub-agent invocation triggers. Single-agent boundary was protected (no `.claude/agents/`) but sub-agents as tools were used implicitly without policy. Reading `docs/methodology.md` (pre-change) showed only one passing reference to "sub-agent = context firewall" with no trigger criteria.

2. **Multi-review absent from repo**: `multi-review` skill existed only at `~/.claude/skills/multi-review/SKILL.md` (user's global config). The harness repo claimed self-containment but a critical mechanism for "qualitative multi-perspective judgment" was a hidden global dependency. `grep -r multi-review` in the repo returned 0 hits before the change.

3. **Autoresearch responsibility misplaced**: `commands/init-harness.md` had four sections marked `(autoresearch projects)` that conditionally installed evaluator protection hooks, autoresearch CLAUDE.md additions, and experiments/ episode format documentation. This required init-harness to *detect* whether the project was autoresearch — but the user's actual workflow on chain-army was "init-harness first, /autoresearch later". The conditional sections never triggered because the project wasn't autoresearch at init time, leaving the Fixed Evaluator pattern's protection unguarded.

### Change

Three commits + an iteration-2 fix commit:

- **38d51fe** (additive): added `Sub-Agent Invocation` section to `docs/methodology.md` with three (later four) trigger categories; copied `multi-review` skill to `skills/multi-review/`; updated `init-harness.md` Step 6.5 to verify global multi-review availability; added sub-agent triggers to CLAUDE.md template requirements; updated completion checklist.

- **971174d** (subtractive + structural): removed four `(autoresearch projects)` sections from `init-harness.md` (Raw Output Preservation, Additional Requirements, Evaluator Protection Hooks, two completion checklist items); added Steps 6-8 to `autoresearch/SKILL.md` Setup Mode (Install Evaluator Protection Hooks, Add Autoresearch Section to CLAUDE.md, Document Episode Format) with explicit idempotency rules for re-entry on already-harnessed projects. This was the sole structural change, justified by workflow mismatch.

- **fd8bdc8** (additive): translated `multi-review` SKILL.md from Korean to English to match repo language convention. Global `~/.claude/skills/multi-review/` synced to prevent drift.

- **(iter2 fix commit, pending at write time)**: addressed five concerns from multi-review iteration 1 — O4 dangling protect-files reference in init-harness Hook Configuration Example, O3 fresh-project install path for Step 6.5, O1+O2 canonical protect-files.sh template + explicit settings.json merge cases, G1 fourth trigger row (evaluator independence), M1 this evolution trace itself.

### Result

- **Before**: 0 references to multi-review in repo; sub-agent invocation undocumented; autoresearch protection unreachable for init-then-autoresearch workflow; methodology repo had no `.claude/traces/`.
- **After**: multi-review shipped as global-dependency skill in `skills/multi-review/`; four sub-agent trigger categories documented in `docs/methodology.md` and mirrored in global `~/.claude/rules/common/harness-methodology.md`; autoresearch responsibility cleanly separated with idempotent re-entry; methodology repo self-applies its own trace filesystem starting with this entry.

Multi-review iteration 1 (3 critics, no convergence critic since first iteration):
- Methodology Coherence: 9 / pass
- Operational Auditor: 7 / concern (5 findings)
- Goal Alignment: 8 / pass (1 gap)
- Mean 8.0, MIXED → Synthesis → 5 fixes applied → iteration 2 planned with Convergence Critic

### Lesson

1. **Confounding-variable check survives multi-agent integration**: The original three sub-agent triggers in 38d51fe missed evaluator independence, even though the user had explicitly named "self-defense removal" as one of three motivating benefits. Single-iteration design without external review missed it. This validates the multi-review-on-integration-work pattern: design mistakes that map cleanly to user-stated requirements are still missed without an external lens.

2. **Subtractive + structural change must be paired with idempotency proof**: Commit 971174d removed four sections from init-harness without a fixed evaluator (Tier 0) to verify the migration preserves behavior. The substitute was Critic 2 (Operational Auditor) walking the chain-army re-entry path mentally. This worked but is not repeatable for projects with no manual auditor available — for autoresearch-style projects, structural refactors should ship with a regression script in `traces/search-set.md`.

3. **Self-application gap**: This methodology repo is itself meta — it generates harnesses for other projects but had not applied its own principles to itself. Critic 1 surfaced this by noting the missing evolution trace for 971174d. The fix is to treat this repo as one of its own consumers: changes to the methodology repo go through the same trace → diagnosis → evolution loop. This entry establishes that practice.

4. **First-iteration heuristic for multi-review**: When designing critic scopes, map each critic 1:1 to a stakeholder concern (philosophy / operations / user goals). Three disjoint critics caught complementary errors that no single reviewer would have caught. The disjoint-scope principle worked exactly as the multi-review SKILL.md anti-patterns predicted.
