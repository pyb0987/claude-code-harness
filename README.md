# Claude Code Harness

A practical framework for building reliable AI-assisted development environments with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), inspired by the [Meta-Harness](https://arxiv.org/abs/2603.28052) paper (Lee et al., Stanford 2026).

Meta-Harness demonstrated that **the environment around an LLM matters as much as the model itself** — changing only the harness can produce a 6× performance gap on the same benchmark. This project takes the paper's key experimental findings and applies them to everyday Claude Code development workflows.

## What's Inside

| Component | Description | Path |
|-----------|-------------|------|
| **Methodology** | Core principles loaded every session | `docs/methodology.md` |
| **Reference** | Detailed trace formats, analysis workflows | `docs/reference.md` |
| **autoresearch** | Autonomous experiment loop (Karpathy pattern) — invoke with `/autoresearch` | `skills/autoresearch/` |
| **harness-engineer** | Failure diagnosis + harness evolution | `skills/harness-engineer/` |
| **multi-review** | Parallel independent critics for high-stakes decisions — invoke with `/multi-review` | `skills/multi-review/` |
| **init-harness** | Project harness bootstrap command | `commands/init-harness.md` |

## Core Principles

All principles come directly from Meta-Harness experiments and ablation studies:

- **Raw traces over summaries** — Full trace access achieved 56.7% accuracy vs 38.7% with summaries (Table 3). Agents diagnose failures by reading raw execution logs via `grep` and `cat`, not by ingesting compressed summaries. Trace files use YAML frontmatter for programmatic querying — `grep -l 'verdict: regressed' traces/evolution/` instantly filters regression cases.
- **Additive modification** — 6 consecutive iterations regressed when modifying control flow or prompts (Appendix A.2). Iteration 7 won by *adding information* (environment bootstrap) without touching existing logic. Adding is safer than restructuring.
- **Code-space search** — Agents explore by modifying code and configuration files, not by rewriting natural language prompts. "Try harder" is noise; a 3-line config change is search.
- **Minimal outer loop** — The search loop is deliberately simple: propose → evaluate → log → repeat. Complex orchestration increases outer loop cost without proportional benefit.
- **Skill document quality as highest leverage** — "Iterating on the skill text had a larger effect on search quality than changing iteration count or population size" (Appendix D). Define goals and prohibitions; leave diagnosis free.
- **Confounding variable isolation** — Prompt changes were confounded with structural fixes (Appendix A.2, iteration 3), leading to misattributed regressions. One change at a time.

## Installation

### Global setup (once)

```bash
git clone https://github.com/pyb0987/claude-code-harness.git
cd claude-code-harness
./scripts/install.sh
```

The installer separates the harness into two layers:

- **Upstream layer (locked)** — written read-only (`chmod 444`) into `~/.claude`.
  This is a snapshot of the repo's `docs/` and `skills/`. Re-running the
  installer updates it; manual edits are discouraged and blocked by the
  protect-files hook (see below).
- **User overlay (editable)** — `~/.claude/rules/common/harness-operations.md`
  is seeded once from `docs/operations-template.md`. The installer never
  overwrites this file. Put your personal operational rules here.

Both files are auto-loaded every session, so extensions accumulate in the
overlay without mutating the upstream anchor.

After installation, your `~/.claude/` should include:
```
~/.claude/
├── rules/common/
│   ├── harness-methodology.md     # Upstream, chmod 444 (auto-loaded)
│   └── harness-operations.md      # User overlay, editable (auto-loaded)
├── docs/
│   └── harness-reference.md       # Upstream, chmod 444 (on-demand)
├── skills/
│   ├── autoresearch/SKILL.md
│   ├── harness-engineer/SKILL.md
│   └── multi-review/SKILL.md
├── commands/
│   └── init-harness.md
└── hooks/
    ├── protect-global-methodology.sh       # Blocks Edit/Write on upstream
    └── protect-global-methodology-bash.sh  # Blocks Bash-based bypass
```

### Activate the protect hook

`chmod 444` stops casual edits but not `chmod +w` followed by overwrite. The
installer prints the hook registration snippet on first run. To close the
bypass, add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/protect-global-methodology.sh"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/protect-global-methodology-bash.sh"}]
      }
    ]
  }
}
```

This enforces P5 ladder level 3 on the methodology snapshot itself: editing
the upstream file becomes structurally impossible, not merely discouraged.
See `traces/evolution/002-self-apply-p5-to-methodology.md` for the rationale.

### Per-project setup

Run the bootstrap command in any project:

```
> /init-harness
```

This analyzes your project and generates:

```
your-project/
├── .claude/
│   ├── traces/
│   │   ├── evolution/            # Harness change history
│   │   ├── failures/             # Failure diagnosis records
│   │   ├── experiments/          # Autoresearch episodes
│   │   └── search-set.md        # Verification test cases
│   ├── hooks/                    # Project-specific hook scripts
│   └── skills/                   # Domain-specific skills (if needed)
├── CLAUDE.md                     # Project instructions (≤100 lines)
└── settings.local.json           # Hook configuration
```

### Verify installation

```bash
# Check methodology loads
claude "What are the core harness methodology principles?"

# Check init-harness is available
claude "/init-harness"
```

## How It Works

### Daily development flow

```
1. Start session → methodology.md auto-loads
2. Work normally with Claude Code
3. On failure → harness-engineer diagnoses from traces
4. Fix applied → recorded in traces/evolution/
5. Harness gradually improves over time
```

### Multi-review flow (for high-stakes or multi-perspective decisions)

```
1. /multi-review → frame the decision (what, stakes, constraints, input)
2. Design 2-4 disjoint critics on the spot (each with explicit scope + anti-scope)
3. Run critics in parallel as independent sub-agents (no result sharing)
4. Convergence check → PASS / VETO / MIXED → Synthesis if needed
5. Present table + final verdict; user retains final decision authority
```

Multi-review is the tactical mechanism for the *qualitative multi-perspective judgment* trigger documented in `docs/methodology.md` "Sub-Agent Invocation". Use it for hard-to-reverse decisions, regressions with suspected confounders, and domains where single-perspective evaluation has missed things before. Iterations 2+ require a Convergence vs Drift meta-critic to detect mechanism-on-mechanism stacking.

### Autoresearch flow (for optimization tasks)

```
1. /autoresearch → setup 3-file architecture
   program.md (direction) + evaluate.py (immutable judge) + genome (mutable code)
2. Agent runs autonomous experiment loop:
   hypothesis → implement → evaluate → ADOPT or REJECT → repeat
3. Results logged to experiments.jsonl + episode traces
4. After 100 experiments or 20 consecutive rejects → escalate
```

## Example: Trace-Based Diagnosis

When an agent repeatedly fails at TypeScript type errors:

```markdown
# traces/failures/001-type-error-loop.md
---
date: "2026-04-01"
escalated_to: hook
search_set_id: "SS-001"
resolved: true
---

## Failure: Agent ignores tsc errors and continues coding

### Observation
Agent edited 3 files, each introducing type errors. Continued to next task
without running tsc. Build failed in CI 20 minutes later.

### Root Cause
No automated type check on file edit. Agent relies on self-discipline
to run tsc, which is unreliable under context pressure.

### Fix
Added PostToolUse hook: `tsc --noEmit` runs after every Edit|Write on *.ts files.

### Prevention
Hook in settings.local.json — agent cannot proceed past type errors.
```

The harness-engineer reads this trace. If similar failures recur despite the hook, it diagnoses *why* the prevention failed rather than starting from scratch.

## Example: Evolution Log

```markdown
# traces/evolution/002-add-tsc-hook.md
---
iteration: 2
date: "2026-04-01"
type: additive
verdict: improved
files_changed: ["settings.local.json"]
refs: []
---

## Iteration 2: Add TypeScript type check hook

Trigger: Agent repeatedly introduced type errors (see failures/001)

### Diagnosis
- Agent cannot reliably self-enforce type checking under context pressure
- Solution: external enforcement via hook

### Change
- Added PostToolUse hook for Edit|Write on *.ts files
- Runs `tsc --noEmit 2>&1 | tail -20`, exits 1 on failure

### Result
- Before: ~3 type errors per session, caught only in CI
- After: 0 type errors escape to CI (hook blocks immediately)

### Lesson
Self-discipline constraints should be converted to hooks when programmatically enforceable.
This aligns with the transfer principle: linter/CI-enforceable rules → tooling, not CLAUDE.md.
```

## Design Decisions

**Why not `.claude/agents/`?** Meta-Harness focuses on single-agent environment optimization. Subagents are used as tools (evaluator, Explore for codebase scanning) for context isolation, not as collaborating personas.

**Why YAML frontmatter in traces?** Enables programmatic querying: `grep -l 'verdict: regressed'` instantly filters regression cases across hundreds of traces. This mirrors the paper's filesystem-based access pattern.

**Why 100-line CLAUDE.md limit?** Every token in CLAUDE.md is loaded every session. Verbose instructions waste context budget. Detailed docs go in `docs/`; CLAUDE.md is the table of contents.

**Why immutable evaluate.py?** The paper principle: if the agent can modify its own evaluator, it contaminates the feedback signal. Evaluator protection hooks enforce this boundary.

**Why transfer rules to tooling?** Rules enforceable by linters/CI should live in tooling, not CLAUDE.md. CLAUDE.md should contain only intent and judgment criteria that tools cannot enforce. This keeps agent instructions high-signal.

## Acknowledgments

Core principles are derived from:
- [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/abs/2603.28052) (Lee et al., 2026)
- [Effective Harnesses for Long-Running Agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic, 2025)

## License

MIT
