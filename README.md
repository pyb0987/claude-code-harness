# AI Agent Meta-Harness

A practical framework for building reliable AI-assisted development environments across coding agents, inspired by the [Meta-Harness](https://arxiv.org/abs/2603.28052) paper (Lee et al., Stanford 2026).

Meta-Harness demonstrated that **the environment around an LLM matters as much as the model itself** — changing only the harness can produce a 6x performance gap on the same benchmark. This project takes the paper's key experimental findings and applies them to everyday agentic development workflows.

The repository is split into a shared core plus thin runtime adapters. The methodology should be edited once in `core/`; Claude Code and Codex integration details live under `adapters/`.

## What's Inside

| Component | Description | Path |
|-----------|-------------|------|
| **Core methodology** | Runtime-neutral principles and trace formats | `core/` |
| **Claude adapter** | Claude Code commands, skills, examples, hooks guidance | `adapters/claude/` |
| **Codex adapter** | Codex skills and project instruction templates | `adapters/codex/` |
| **Backlog** | Non-blocking core and adapter improvement items | `backlog/` |

## Core Principles

Core principles come directly from Meta-Harness experiments and ablation studies:

- **Raw traces over summaries** — Full trace access achieved 56.7% accuracy vs 38.7% with summaries (Table 3). Agents diagnose failures by reading raw execution logs via `grep` and `cat`, not by ingesting compressed summaries. Trace files use YAML frontmatter for programmatic querying — `grep -l 'verdict: regressed' traces/evolution/` instantly filters regression cases.
- **Additive modification** — 6 consecutive iterations regressed when modifying control flow or prompts (Appendix A.2). Iteration 7 won by adding information (environment bootstrap) without touching existing logic. Adding is safer than restructuring.
- **Code-space search** — Agents explore by modifying code and configuration files, not by rewriting natural language prompts. "Try harder" is noise; a 3-line config change is search.
- **Minimal outer loop** — The search loop is deliberately simple: propose → evaluate → log → repeat. Complex orchestration increases outer loop cost without proportional benefit.
- **Skill document quality as highest leverage** — "Iterating on the skill text had a larger effect on search quality than changing iteration count or population size" (Appendix D). Define goals and prohibitions; leave diagnosis free.
- **Confounding variable isolation** — Prompt changes were confounded with structural fixes (Appendix A.2, iteration 3), leading to misattributed regressions. One change at a time.

## Repository Layout

```text
core/
├── methodology.md          # Runtime-neutral principles
└── reference.md            # Trace formats and analysis workflow
backlog/
├── README.md               # Backlog ownership guide
├── core.md                 # Agent-agnostic follow-ups
└── codex-adapter.md        # Codex-specific follow-ups
adapters/
├── claude/
│   ├── commands/
│   ├── examples/
│   └── skills/
└── codex/
    ├── skills/
    └── templates/
```

## Claude Code Adapter

### Global setup

```bash
# Clone the repo
git clone https://github.com/pyb0987/ai-agent-meta-harness.git
cd ai-agent-meta-harness

# Copy core docs (loaded every session)
mkdir -p ~/.claude/rules/common
cp core/methodology.md ~/.claude/rules/common/harness-methodology.md

# Copy reference docs (loaded on demand)
mkdir -p ~/.claude/docs
cp core/reference.md ~/.claude/docs/harness-reference.md

# Copy skills (autoresearch + harness-engineer + multi-review)
# multi-review is a global dependency consumed from ~/.claude/skills/multi-review/
mkdir -p ~/.claude/skills
cp -r adapters/claude/skills/* ~/.claude/skills/

# Copy commands
mkdir -p ~/.claude/commands
cp adapters/claude/commands/init-harness.md ~/.claude/commands/
```

### Per-project setup

Run the bootstrap command in any project:

```text
> /init-harness
```

This analyzes your project and generates:

```text
your-project/
├── .claude/
│   ├── traces/
│   │   ├── evolution/            # Harness change history
│   │   ├── failures/             # Failure diagnosis records
│   │   ├── experiments/          # Autoresearch episodes
│   │   └── search-set.md         # Verification test cases
│   ├── hooks/                    # Project-specific hook scripts
│   └── skills/                   # Domain-specific skills (if needed)
├── CLAUDE.md                     # Project instructions
└── settings.local.json           # Hook configuration
```

## Codex Adapter

Codex support is intentionally an adapter, not a fork. Shared methodology stays in `core/`; Codex-specific skills describe how Codex should apply it using `AGENTS.md`, `.harness/traces/` by default, existing `.claude/traces/` when present, terminal verification, and Codex sub-agents.

Initial Codex adapter contents:

| Component | Path |
|-----------|------|
| Bootstrap skill | `adapters/codex/skills/init-codex-harness/SKILL.md` |
| Project instruction template | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` |
| Harness-engineer skill | `adapters/codex/skills/harness-engineer/SKILL.md` |
| Multi-review skill | `adapters/codex/skills/multi-review/SKILL.md` |

Suggested local install while developing the adapter:

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
# Optional while developing from the repo: keep adapters/codex/templates as a compatibility mirror for humans.
```

Use the skill by asking Codex to "init codex harness" or "apply codex-harness to this project". Use Codex multi-review by asking for a multi-perspective review.

Codex does not consume Claude Code slash commands or `.claude/settings.local.json` hooks. The adapter therefore starts with explicit verify commands and trace discipline; stronger enforcement should be added through Codex plugins, CI, git hooks, or project-local scripts where appropriate.

## Migration Notes

Top-level `docs/`, `commands/`, and `skills/` paths are retained as temporary compatibility mirrors for one transition period. Old install commands continue to install working Claude Code assets, but new work should edit `core/` and `adapters/`; mirror files are only there to protect existing bookmarks, scripts, and user muscle memory.

Compatibility mirror mapping:

| Old path | New source of truth |
|----------|---------------------|
| `docs/methodology.md` | `core/methodology.md` |
| `docs/reference.md` | `core/reference.md` |
| `commands/init-harness.md` | `adapters/claude/commands/init-harness.md` |
| `skills/*` | `adapters/claude/skills/*` |
| `adapters/codex/templates/AGENTS.md.template` | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` |

Run `python3 scripts/check-compat-mirrors.py` before committing changes that touch mirrored paths.

### Pre-commit Hook

Enable the tracked git hook in local clones:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs `python3 scripts/check-compat-mirrors.py` so temporary compatibility mirrors cannot silently drift from their canonical files.

## How It Works

### Daily development flow

```text
1. Start session → project instructions and relevant skills load
2. Work normally with the coding agent
3. On failure → harness-engineer diagnoses from traces
4. Fix applied → recorded in traces/evolution/
5. Harness gradually improves over time
```

### Multi-review flow

```text
1. Frame the decision (what, stakes, constraints, input)
2. Design 2-4 disjoint critics on the spot
3. Run critics in parallel as independent sub-agents
4. Convergence check → PASS / VETO / MIXED
5. Present table + final verdict; user retains final decision authority
```

### Autoresearch flow

```text
1. Set up program.md (direction) + evaluate.py (immutable judge) + genome (mutable code)
2. Agent runs autonomous experiment loop: hypothesis → implement → evaluate → ADOPT or REJECT
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
Added a structural verification path for `tsc --noEmit`.

### Prevention
The project harness now makes typecheck failures visible before completion.
```

## Design Decisions

**Why adapters?** The methodology should not be duplicated across agent runtimes. Runtime-specific details such as slash commands, hook schemas, project instruction filenames, and sub-agent model names belong in adapters.

**Why YAML frontmatter in traces?** Enables programmatic querying: `grep -l 'verdict: regressed'` instantly filters regression cases across hundreds of traces. This mirrors the paper's filesystem-based access pattern.

**Why concise project instructions?** Every token loaded every session competes with task context. Detailed docs go in project documentation or adapter references; project instructions are the table of contents.

**Why immutable evaluate.py?** The paper principle: if the agent can modify its own evaluator, it contaminates the feedback signal. Adapters choose the runtime-appropriate enforcement mechanism.

**Why transfer rules to tooling?** Rules enforceable by linters/CI should live in tooling, not agent instructions. Project instruction files should contain only intent and judgment criteria that tools cannot enforce.

## Acknowledgments

Core principles are derived from:

- [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/abs/2603.28052) (Lee et al., 2026)
- [Effective Harnesses for Long-Running Agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic, 2025)

## License

MIT
