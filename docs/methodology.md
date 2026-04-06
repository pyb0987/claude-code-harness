# Harness Engineering Methodology — Core

Core principles applied every session. For detailed reference, see docs/reference.md

> The bottleneck is environment design, not model intelligence.
> Richer diagnostic context produces better harnesses. (Meta-Harness, Lee et al. 2026)

## Trace-Based Diagnosis — The Core of Diagnosis

### Principle: Raw Over Summaries, Traces Over Scores
- LLM summaries compress away details needed for diagnosis (proven by ablation: summary < raw trace)
- When diagnosing failures, read **raw execution logs, code, and scores** directly from the filesystem
- Use `grep`, `cat`, `diff` for selective access — don't dump everything into the prompt

### Trace Filesystem (Required for All Projects)
Every harnessed project must have `.claude/traces/` (auto-created by `/init-harness`):
```
.claude/traces/
├── evolution/           # Harness change history
│   └── NNN-{name}.md   # Changes + reasoning + results (YAML frontmatter)
├── failures/            # Failure diagnosis (with raw context)
│   └── NNN-{name}.md   # Failure situation + cause + fix (YAML frontmatter)
├── experiments/         # Autoresearch episodes (per-session experiment context)
│   └── NNN-{name}.md   # Experiment range + adopted/exhausted axes + lessons (YAML frontmatter)
├── search-set.md        # Past failure cases for verifying harness changes (verify commands included)
```

- YAML frontmatter enables programmatic filtering: `grep -l 'verdict: regressed'` etc.
- Evolution log/failure diagnosis formats: see reference.md
- Preserve: failures requiring causal reasoning, before/after comparisons, confounding variable identification
- Don't preserve: simple typos, obvious fixes
- **search-set**: each entry must have a `verify` field — an auto-executable verification command
- **experiments/**: record episodes immediately at milestones (ADOPT, axis exhaustion, every 10 experiments). Format: see reference.md

## Additive Modification — Change Strategy

Key finding from Meta-Harness experiments:

> Modifying existing working structures introduces confounding variables.
> Adding information is safer than changing structure.

### Rules
1. **Additive first**: Try changes that add new information/context first
2. **Subtractive second**: Removing unnecessary elements comes second
3. **Structural last**: Modifying existing control flow/logic is the last resort
4. **Isolate changes**: One change at a time. Bundling changes introduces confounding variables
   - **Exception — health batch fixes**: Non-functional fixes (dead references, state inconsistencies, missing docs) found via multi-review/audit can be batched. Conditions: (1) each change is independent (no confounders), (2) changes don't alter agent behavior (infrastructure only), (3) individual changes listed in evolution trace. Functional changes must be separated.
5. **Diagnose regressions**: When regression occurs, isolate which part of the change caused it → record in traces

### Confounding Variable Identification Pattern
- Fix A + Fix B applied together → regression
- Fix A applied alone → slight regression or neutral
- → Common factor B is the primary cause
- **When this pattern is recognized**: separate the changes and evaluate each independently

## Context Efficiency — The Context Battlefield

Agent performance degrades as context fills up (Context Rot).

### Successes Silent, Failures Loud
- On success: summary only. On failure: detailed output
- Offload large tool outputs to files; reference only when needed

### Subagents = Context Firewalls
- The value of subagents is not role division but **context isolation**
- They absorb intermediate noise from research/exploration/implementation, passing only results upstream

## Minimal Outer Loop & Code-Space Search — Design Principles

### P3: The outer loop must be simple enough to verify by inspection
- Harness control flow (Sprint Contract, hook chain, evaluator path) must be immediately understandable
- Complex conditional branching, multi-stage orchestration, agent-to-agent protocols increase outer loop cost
- **Self-check**: "Can I explain this harness's entire flow in 5 minutes?" → No means simplify
- **Autoresearch application**: program.md → genome modification → evaluate.py → ADOPT/REJECT is the entire loop. Don't make it more complex

### P4: Agents search in code space
- What agents modify is **code and configuration files**, not natural language prompts
- CLAUDE.md, hooks, skill documents, config files = the agent's search space
- Rewriting prompts in natural language ("try harder") is noise, not search
- **Autoresearch application**: directly modify the genome (Python code) to explore performance. Code changes, not natural language instructions

## Feedback Loop — Evolution Protocol

### Failure → Trace Recording → Rule Addition Loop
1. Agent fails or repeats the same fix
2. **Record in traces**: preserve raw context in `.claude/traces/failures/NNN-{name}.md`
3. Respond: add knowledge to docs, add constraint to CLAUDE.md, or add tooling/hooks as appropriate
4. **Record change in evolution log**: `.claude/traces/evolution/NNN-{name}.md`
5. **Verify with search-set**: confirm past failures in `.claude/traces/search-set.md` don't recur
6. Add new failure to search-set if it has verification value

### Sprint Contract
```
Done when: [specific, verifiable completion condition]
Evaluator: [Tier 0 (fixed evaluator) | multi-review (high-stakes)]
```

### Evaluator Separation

**Tier 0 — Fixed Evaluator (quantitative R&D / autoresearch)**:
- Evaluator: Python script, **immutable**, JSON stdout
- Verdict: binary (ADOPT/REJECT), REJECT → auto revert
- Escalation: 20 consecutive REJECTs → multi-review

**For high-stakes qualitative decisions**: use /multi-review (parallel independent critics).

### Hooks vs Backpressure
- **Hooks**: enforced externally (type checks, formatters)
- **Backpressure**: agent self-verification (tests, coverage)

### Rule Quality Criteria
- **Specific**: "clean code" ✗ → "functions under 50 lines" ✓
- **Verifiable**: prefer rules checkable by linters/tests
- **Just enough**: excessive rules waste tokens

## Skill Document — The Highest-Leverage Investment

> Skill document quality has a larger impact on performance than iteration count or population size.

### Skill Document Writing Principles
- **State prohibitions and goals**, leave diagnosis methods free (agent decides)
- Define role, directory structure, CLI commands, output format
- Debug skill documents with 3-5 short test iterations before production runs
- After enough iterations, **accumulated traces shape behavior more strongly than the skill document itself**

### Knowledge Escalation
When CLAUDE.md grows too large, split detailed content to docs/. For recurring domain expertise, consider a dedicated skill in `.claude/skills/`.

