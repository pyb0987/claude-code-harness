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
- **failures/ recording triggers** (objective criteria):
  1. New guard violation type (a guard failure not seen before)
  2. Result opposite to hypothesis (e.g., expected improvement → degradation)
  3. Structural code change failure (logic change, not parameter tuning)
  Simple threshold misses (REJECT_THRESHOLD) don't need recording — experiments/ episode tables suffice
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
   - **Exception — health batch fixes**: Non-functional fixes (dead references, state inconsistencies, missing docs) found via audit can be batched. Conditions: (1) each change is independent (no confounders), (2) changes don't alter agent behavior (infrastructure only), (3) individual changes listed in evolution trace. Functional changes must be separated.
5. **Diagnose regressions**: When regression occurs, isolate which part of the change caused it → record in traces

### Confounding Variable Identification Pattern
- Fix A + Fix B applied together → regression
- Fix A applied alone → slight regression or neutral
- → Common factor B is the primary cause
- **When this pattern is recognized**: separate the changes and evaluate each independently

### Surgical Diff Discipline (within a single edit)

Additive Modification governs change strategy *across iterations*. This rule governs diff shape *within a single edit*:

- **Diff self-check**: after editing, every changed line must trace directly to the user's request. If a line doesn't, remove it.
- **Pre-existing dead code** (not orphaned by your change) is mentioned, not removed — removal requires explicit request.
- **No drive-by cleanups**: don't reformat, rename, or "improve" unrelated code while solving a different problem. Bundled cleanups become confounding variables when regressions appear.

Why this sits next to Additive Modification: both stem from the same finding — touching more than necessary introduces confounders. This rule is the single-edit corollary of the multi-iteration principle above.

## Minimal Outer Loop & Code-Space Search — Design Principles

### P3: The outer loop must be simple enough to verify by inspection
- Harness control flow (hook chain, evaluator path, done conditions) must be immediately understandable
- Complex conditional branching, multi-stage orchestration, agent-to-agent protocols increase outer loop cost
- **Self-check**: "Can I explain this harness's entire flow in 5 minutes?" → No means simplify
- **Autoresearch application**: program.md → genome modification → evaluate.py → ADOPT/REJECT is the entire loop. Don't make it more complex

### P4: Agents search in code space
- What agents modify is **code and configuration files**, not natural language prompts
- CLAUDE.md, hooks, skill documents, config files = the agent's search space
- Rewriting prompts in natural language ("try harder") is noise, not search
- **Autoresearch application**: directly modify the genome (Python code) to explore performance. Code changes, not natural language instructions

### P5: Recurring failures are absorbed by structure, not rules

> "Don't do this" fails. "Can't do this" succeeds.

When the same failure category repeats, move beyond telling the agent what not to do — make **violation structurally impossible**.

**Escalation ladder** (stronger going down):

| Level | Mechanism | Enforcement | Limitation |
|-------|-----------|-------------|------------|
| 0. Rule | CLAUDE.md constraint | Voluntary compliance | Leaks via context rot |
| 1. Warning | PostToolUse hook (soft) | Reminder | Can be ignored |
| 2. Block | PreToolUse hook (exit 2) | Direct modification blocked | Bypass routes may exist |
| 3. **Structural impossibility** | Single Source + Codegen + Protect | **Drift itself is impossible** | Initial setup cost |

**Single Source + Generated Derivatives pattern**:
```
Human-editable truth (YAML / schema / config)
    → Generator (codegen / template / build script)
        → Derived artifact (code / docs / UI text)
            → Protection (chmod 444 + blocking hook)
```

**When to apply**:
- Same failure category with 3+ evidence items → structural elimination review is mandatory
- Truth source exists in 2+ places → apply Single Source + Codegen + Protect pattern
- Only judgment-dependent domains (aesthetics, trade-offs) should remain as rules

**Self-check**: "Can this failure category be eliminated by structure rather than rules?" If yes, aim for ladder level 3.

## Sub-Agent Invocation — Tactical Mechanism

Meta-Harness is the **policy layer** (when to isolate, when to learn). Sub-agents are the **tactical mechanism** (how to isolate). The two are orthogonal: invoking sub-agents does not violate the single-agent principle as long as no `.claude/agents/` definition files or persistent multi-persona orchestrators are created. Sub-agents are tools, not teammates.

### Four trigger categories

| Trigger | Mechanism | When |
|---------|-----------|------|
| **Qualitative multi-perspective judgment** | `multi-review` skill (parallel critics with role separation) | Hard-to-reverse decisions, regressions with suspected confounders, domains where single-perspective evaluation has failed before |
| **Parallel independent exploration** | Multiple `Explore` sub-agents in one message | Comparing 2+ libraries / hypotheses / approaches where each branch is independent and would otherwise serialize |
| **Context firewall** | Generic sub-agent (Explore or task-specific) | Investigations expected to consume large context (long log analysis, deep codebase walks) where the parent only needs the conclusion |
| **Evaluator independence** | Dedicated Evaluator sub-agent OR Fixed Evaluator (immutable Python script) | High-stakes generation where self-evaluation bias is the primary risk; the generator must not score its own output. Fixed Evaluator is the cheapest and strongest form; a dedicated sub-agent is the alternative when binary verdict is not viable |

The four triggers map directly to the three multi-agent benefits commonly cited in the multi-agent literature:
- *Context separation* → Context firewall
- *Multi-perspective on problems* → Qualitative multi-perspective judgment
- *Self-defense / evaluator independence* → Evaluator independence (dedicated row above)
- *Plus*: Parallel exploration as a tactical efficiency benefit Meta-Harness inherits naturally

This is why Meta-Harness can absorb multi-agent benefits without abandoning the single-agent paradigm: each benefit has a tactical mechanism that does not require persistent agent definitions or multi-persona orchestration.

### Rules
- **Independence**: parallel sub-agents must not share intermediate results — independence is the source of value, contamination kills it
- **No orchestrator persistence**: sub-agents are spawned per-task and discarded. Do not create `.claude/agents/` definition files
- **Conclusion-only return**: sub-agents return distilled findings, not raw transcripts — the firewall is the point
- **Trigger threshold**: prefer over-invoking these mechanisms to under-invoking them. The cost of an unnecessary sub-agent call is small; the cost of a contaminated decision or context-rotted parent is large

### Model routing
Explicitly set the `model` parameter when spawning sub-agents:

| Task type | Model | Examples |
|-----------|-------|---------|
| Complex judgment, architecture, irreversible decisions | **opus** | High-stakes multi-review critics, design validation, strategy decisions |
| Standard analysis, exploration, implementation | **sonnet** | Explore agents, code review, standard evaluators, routine critics |
| Mechanical verification (no judgment needed) | **haiku** | Binary pass/fail checks, format validation, file existence checks |

- Default: **sonnet** (when model is omitted)
- Use haiku only for judgment-free mechanical checks
- When uncertain, choose sonnet over haiku (slight cost increase beats quality loss)

### Anti-patterns
- Spawning sub-agents for trivial tasks (3-line edits, single-file reads)
- Using sub-agents to "split work" without independence (sequential dependencies → use the parent agent)
- Creating named persistent agents (Reviewer, Architect, Tester) — this is multi-persona collaboration, not Meta-Harness

## Feedback Loop — Evolution Protocol

### Failure → Trace Recording → Rule Addition Loop
1. Agent fails or repeats the same fix
2. **Record in traces**: preserve raw context in `.claude/traces/failures/NNN-{name}.md`
3. **Structural elimination check** (P5): "Can this category be eliminated by structure, not rules?"
4. Respond: add knowledge to docs, add constraint to CLAUDE.md, add tooling/hooks, or **apply Single Source + Codegen + Protect** (P5 ladder level 3) as appropriate
4. **Record change in evolution log**: `.claude/traces/evolution/NNN-{name}.md`
5. **Verify with search-set**: confirm past failures in `.claude/traces/search-set.md` don't recur
6. Add new failure to search-set if it has verification value

### Completion Criteria
Before starting work, define: `Done when: [specific, verifiable condition]`

### Fixed Evaluator (for autoresearch)
- Evaluator: Python script, **immutable**, JSON stdout
- Verdict: binary (ADOPT/REJECT), REJECT → revert
- **Reject code preservation**: before reverting, capture `git diff HEAD~1` into failures/ trace (when recording triggers apply). Reverting without preserving the diff permanently loses raw context
- Escalation: 20 consecutive REJECTs → manual review

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


