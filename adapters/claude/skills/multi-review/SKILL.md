---
name: multi-review
description: "Dynamic multi-perspective review: spawn parallel critics with role separation for high-stakes decisions. Use when a decision needs validation from multiple independent viewpoints."
---

# Multi-Review Protocol

For important decisions, run independent-perspective Critics in parallel to perform multi-angle validation.
The protocol is fixed; Critic composition is designed dynamically per problem.

## When to Activate

### User trigger
`/multi-review`, or phrases like "validate this from multiple angles", "review from several perspectives".

### Claude auto-suggest (suggestion only, not mandatory)
Suggest multi-review to the user when these signals are detected:
- Hard-to-reverse decisions (locking in strategy parameters, live deployments, application submissions)
- High-uncertainty judgments (insufficient data, unclear trade-offs)
- Domains where single-perspective evaluation has missed things before

## Protocol

### Phase 1: Problem Framing

Structure the decision under review:

```
Decision: [what is being decided]
Stakes: [what is the cost if it goes wrong]
Constraints: [already-fixed constraints]
Presuppositions: [what this question silently assumes — list 2-3 items]
Input: [materials to pass to the Critics]
```

**About Presuppositions (required, not optional)**:

A question's presuppositions are claims it treats as given without evaluating. Critics narrowly scoped around the decision will leave these unexamined, allowing flawed premises to reach verdicts unchallenged. Surface them here before critic design.

Examples:
- "Which benchmark should we use?" — presupposes we need a benchmark at all
- "What's the best storage schema?" — presupposes we need persistent storage
- "How should we structure the plugin API?" — presupposes plugins are the right abstraction

Rule: include at least one critic whose scope is "evaluate whether one of the listed presuppositions is actually warranted," OR explicitly allow all critics in their prompt to flag "the question itself is wrongly framed" as a valid verdict.

If Phase 1's Presuppositions block is empty or vague, Phase 2 critic design is incomplete — critics will optimize within the presupposed frame and systematically miss frame-level errors. This is the canonical failure mode of multi-review: N iterations of "which option is best?" when the question itself was wrong.

### Phase 2: Critic Design (Dynamic)

Design 2-4 Critics fitted to the problem on the spot.

**Design principles**:
- Each Critic's evaluation scope must be **explicitly disjoint** (overlap creates redundancy, not consensus)
- Assign each Critic a **natural persona** (a perspective, not a role title)
- One Critic may hold **Veto authority** (forcing rejection if its perspective sees a fatal flaw)

**Critic design template**:
```
Critic N: [name]
  Persona: [whose perspective this is]
  Scope: [evaluation scope — only this is examined]
  Anti-scope: [explicitly excluded — what is NOT evaluated]
  Veto: [if any, under what condition it triggers]
```

**Model assignment criteria**:
- High-stakes / complex judgment (architecture, strategy, irreversible decisions) → **opus**
- Standard analysis / code review → **sonnet**
- Checklist / format verification (binary pass/fail only) → **haiku**
- Default: **sonnet**

### Phase 3: Parallel Execution

Run each Critic as an **independent sub-agent** (Agent tool).

**Prompt structure passed to each Critic**:
```
## Your Role
You are [Persona].

## Your Scope
You evaluate ONLY [Scope].
Do NOT evaluate [Anti-scope].

## Input
[Problem framing + relevant materials]

## Output Format (JSON)
{
  "score": 1-10,
  "verdict": "pass" | "concern" | "veto",
  "key_findings": ["up to 3 key findings"],
  "evidence": ["supporting evidence for each finding"],
  "veto_reason": null | "veto rationale (if applicable)"
}
```

**Execution rules**:
- Run all Critics **simultaneously** (parallel Agent tool calls)
- Each Critic must NOT see other Critics' results (independence guarantee)
- Constrain Critics in the prompt to not opine outside their scope

### Phase 4: Convergence Check

| Condition | Verdict |
|-----------|---------|
| All Critics ≥ 7 AND no veto | **PASS** — report with one-line summary |
| Any Critic vetoes | **VETO** — present veto rationale + that Critic's full output |
| Mean ≥ 7 BUT some < 7 | **MIXED** → Phase 5 Synthesis |
| Mean < 7 | **FAIL** → Phase 5 Synthesis |

### Phase 5: Synthesis (when MIXED/FAIL)

Identify conflicts between Critic results and produce an integrated judgment:

```
## Conflicts
- Critic A judged [X], Critic B judged [Y]
- Source of conflict: [why they reached different conclusions]

## Unified Assessment
- [integrated judgment + rationale]
- Residual risk: [unresolved concerns]

## Recommendation
- [concrete action proposal]
- Conditional go-ahead viability: [if any, specify the conditions]
```

### Phase 6: Present to User

**Result table**:
```
| Critic | Score | Verdict | Key Finding |
|--------|-------|---------|-------------|
| ...    | ...   | ...     | ...         |
```

**Final verdict**: PASS / VETO / MIXED + integrated recommendation
**User decision**: Human-in-the-loop — the final decision is always the user's

## Harness Feedback Loop

After review completion, learn:
- If a Critic missed a perspective → add that perspective for similar problems next time
- If the user overruled a Critic's judgment → revisit that Critic's prompt / scope
- If the domain recurs → promote that Critic to a dedicated skill in `.claude/skills/` (Level 3)

Learning feedback recording paths:
- **Project-specific learning** → that project's memory/ (e.g., `feedback_review_*.md`)
- **Multi-review protocol improvement itself** → add to this SKILL.md's Anti-Patterns
- Scope discrimination: "Does this learning apply to other projects?" → Yes = SKILL.md, No = project memory

## Anti-Patterns

- Overusing multi-review on trivial decisions (4 Critics for a 3-line code change is overkill)
- Critic scopes overlapping such that they repeat the same point
- Using the same model for every Critic (reduces perspective diversity)
- Averaging scores without Synthesis to reach a verdict
- Ignoring user decision authority (Critic consensus ≠ final decision)
- **Iteration drift**: when iterating on the same problem 3+ times, if complexity (number of changes / number of mechanisms) is increasing, that is divergence, not convergence. Stop the mechanism-on-mechanism stacking and revert to the minimal-viable. No global interventions without root-cause diagnosis. At every iteration ask: "Does this change resolve the absence of an existing rule, or compensate for a violation of an existing rule?" — if the latter, do NOT strengthen the rule; **diagnose the cause of the violation first**.
- **Convergence Critic always included**: any multi-review iterating 2+ times must include a Convergence vs Drift meta-Critic to monitor iteration health.
- **Unexamined presuppositions**: critics scoped narrowly will evaluate the decision as posed and miss frame-level errors in the question itself. If after multiple iterations a reframing by the user (not the critics) reveals that the question was wrong, Phase 1's Presuppositions block was probably empty or vague. Fix: surface presuppositions explicitly in Phase 1 and either assign a critic to attack one, or grant all critics permission to verdict "question is wrongly framed."
