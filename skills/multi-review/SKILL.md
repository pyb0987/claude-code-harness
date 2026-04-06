---
name: multi-review
description: "Dynamic multi-perspective review: spawn parallel critics with role separation for high-stakes decisions. Use when a decision needs validation from multiple independent viewpoints."
---

# Multi-Review Protocol

Run independent Critics in parallel for multi-perspective validation of important decisions.
The protocol is fixed; Critic composition is dynamically designed per problem.

## When to Activate

### User trigger
`/multi-review` or "validate from multiple perspectives", "multi-angle review"

### Claude auto-suggest (suggestion only, not forced)
Suggest multi-review to the user when these signals are detected:
- Hard-to-reverse decisions (strategy parameter finalization, live deployment, application submission)
- High-uncertainty judgments (insufficient data, unclear tradeoffs)
- Domains where single-perspective evaluation has previously missed issues

## Protocol

### Phase 1: Problem Framing

Structure the decision target:

Decision: [what is being decided]
Stakes: [what cost if wrong]
Constraints: [already-fixed constraints]
Input: [materials to pass to Critics]

### Phase 2: Critic Design (Dynamic)

Design 2-4 Critics suited to the problem on the spot.

**Design principles**:
- Each Critic's evaluation scope must be **explicitly separated** (overlap produces duplication, not consensus)
- Critics are assigned **natural personas** (perspectives, not roles)
- One Critic may hold **Veto authority** (forced rejection if critical flaw found in their scope)

**Critic design template**:
Critic N: [name]
  Persona: [whose perspective]
  Scope: [evaluation scope — only examines this]
  Anti-scope: [what is NOT evaluated — explicit exclusion]
  Veto: [if applicable, under what conditions does it trigger]

**Model assignment criteria**:
- Deep analysis/judgment → opus or sonnet
- Checklist/format verification → haiku
- Default: sonnet (cost-quality balance)

### Phase 3: Parallel Execution

Execute each Critic as an **independent subagent** (Agent tool).

**Prompt structure for each Critic**:
## Your Role
You are [Persona].

## Your Scope
You evaluate ONLY [Scope].
Do NOT evaluate [Anti-scope].

## Input
[Problem framing + related materials]

## Output Format (JSON)
{
  "score": 1-10,
  "verdict": "pass" | "concern" | "veto",
  "key_findings": ["up to 3 key findings"],
  "evidence": ["evidence for each finding"],
  "veto_reason": null | "veto reason (if applicable)"
}

**Execution rules**:
- All Critics run **simultaneously** (parallel Agent tool calls)
- Each Critic cannot see other Critics' results (independence guaranteed)
- Critics are constrained in prompts not to opine outside their scope

### Phase 4: Convergence Check

| Condition | Verdict |
|-----------|---------|
| All Critics ≥ 7 AND no veto | **PASS** — report in 1-line summary |
| Any Critic vetoes | **VETO** — show veto reason + full Critic output |
| Average ≥ 7 BUT some < 7 | **MIXED** → Phase 5 Synthesis |
| Average < 7 | **FAIL** → Phase 5 Synthesis |

### Phase 5: Synthesis (on MIXED/FAIL)

Identify conflicts between Critic results and produce unified judgment:

## Conflicts
- Critic A judged [X], Critic B judged [Y]
- Conflict cause: [why they reached different conclusions]

## Unified Assessment
- [Integrated judgment + evidence]
- Residual risk: [unresolved concerns]

## Recommendation
- [Specific action proposal]
- Conditional proceed: [conditions if applicable]

### Phase 6: Present to User

**Results table**:
| Critic | Score | Verdict | Key Finding |
|--------|-------|---------|-------------|
| ...    | ...   | ...     | ...         |

**Final verdict**: PASS / VETO / MIXED + integrated recommendation
**User decides**: Human-in-the-loop — final decision is always the user's

## Harness Feedback Loop

Post-review learning:
- If a Critic missed a perspective → add that perspective for similar future problems
- If the user overrode a Critic's judgment → review that Critic's prompt/scope
- If a domain recurs → promote that Critic to a dedicated skill in `.claude/skills/` (Level 3)

Learning record paths:
- **Project-specific learning** → project memory/ (e.g., `feedback_review_*.md`)
- **Multi-review protocol improvements** → add to this SKILL.md's Anti-Patterns
- Scope judgment: "Does this learning apply to other projects?" → Yes=SKILL.md, No=project memory

## Anti-Patterns

- Overusing multi-review for trivial decisions (4-Critic review for a 3-line code change is excessive)
- Overlapping scope between Critics causing repetitive findings
- Using the same model for all Critics (reduces perspective diversity)
- Averaging scores without synthesis for judgment
- Ignoring user's decision authority (Critic consensus ≠ final decision)
