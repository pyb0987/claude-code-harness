# Codex Adapter Backlog

Codex-specific backlog for adapter behavior that should not be pushed into the shared core. Core methodology follow-ups live in `backlog/core.md`.

## Priority Candidates

### 1. Add Codex sandbox/escalation recording template

The Codex `harness-engineer` skill says sandbox, permission, and network outcomes are first-class verification outcomes, but it does not give a compact recording template.

Potential improvement:

```markdown
- command: `{command}`
- status: PASS | FAIL | SKIPPED
- blocked_by: sandbox | permission | network | unsafe_side_effect | missing_dependency | none
- escalation_required: yes | no
- approval_reason: {short reason, if escalation is needed}
- rerun_status: {what should happen after approval or environment change}
```

Keep actual approval mechanics in Codex runtime instructions rather than duplicating them in the skill.

### 2. Clarify Codex trace-root migration behavior

Codex prefers `.harness/traces/`, but may need to reuse existing `.claude/traces/` history when a project is migrated from Claude Code.

Potential improvement:

- Define when Codex should continue using `.claude/traces/` temporarily.
- Define when it should propose migration into `.harness/traces/`.
- Define the minimum migration plan: copy/move strategy, search-set preservation, and a trace entry recording the migration.

### 3. Harden Codex hook enforcement templates

Codex has project/user hooks, but hook interception should be treated as a guardrail rather than the only enforcement boundary. Adapter docs should keep concrete templates aligned with current Codex hook behavior.

Potential improvement:

- Level 1 warning: AGENTS.md reminder plus explicit verify command.
- Level 2 guardrail: Codex `PreToolUse` and `PermissionRequest` hooks calling a shared checker.
- Level 2 hard block: project-local script, pre-commit hook, and CI using the same checker.
- Level 3 structural impossibility: single source, generator, protected generated derivatives, and CI/git-hook drift check.
- Revisit templates when Codex hook interception semantics change.

### 4. Implement the chosen Codex distribution path

Decision: use a **local Codex plugin bundle** as the primary distribution path.

Status of paths:

- Local plugin bundle: primary path for normal local development and dogfooding.
- Direct skill copy: development fallback for fast skill text iteration only.
- Marketplace/plugin bundle: future release path after local plugin layout stabilizes.
- `skill-installer`: compatibility investigation for skill-only degraded installs.

Follow-up work:

- Scaffold the plugin layout with `.codex-plugin/plugin.json`.
- Move or mirror skills, hooks, scripts, assets, and templates into the plugin bundle.
- Add a local plugin install smoke test.
- Decide how the fallback direct-copy path reports missing hooks/checker assets.
- Keep README install instructions aligned with the plugin layout.

### 5. Define Codex plugin bundle scope

Decision: Codex support should become a local plugin bundle. The remaining question is what ships in the first bundle.

Potential improvement:

- Add `.codex-plugin/plugin.json` under the chosen plugin root.
- Include skills, Codex hook templates, protection checker templates, AGENTS template, and example docs.
- Define which files are canonical in `adapters/codex/` and which are generated or mirrored into the plugin layout.
- Keep direct skill-copy installation only as a documented degraded path for skill text iteration.

### 6. Standardize Codex verify command discovery

Claude-oriented flows often center hook recipes. Codex harnesses rely more heavily on `search-set.md` Active verify commands and explicit terminal verification.

Potential improvement:

- Define project command discovery order: package scripts, test config, CI jobs, README docs, existing AGENTS/CLAUDE instructions.
- Define how to choose the initial Active verify command for TypeScript, Python, research, and mixed projects.
- Require verify commands to be deterministic, non-interactive, and non-network by default unless explicitly marked.
- Record sandbox, permission, or network requirements in the search-set entry.

### 7. Document sub-agent capability matrix by Codex surface

Codex sub-agent availability may differ across Desktop, CLI, API, and future surfaces.

Potential improvement:

- Document which surfaces support sub-agents today.
- For `multi-review`, define fallback to a sequential review checklist when sub-agents are unavailable.
- For evaluator independence, prefer fixed evaluator scripts when sub-agents are unavailable.
- For explorer/evaluator patterns, document what degrades and what must stop.

### 8. Expand Codex permission and escalation guidance

Codex execution depends on sandbox mode, approval policy, writable roots, and network restrictions. This differs from Claude hook/permission assumptions.

Potential improvement:

- Add a more concrete Codex Permission Notes section to the AGENTS template.
- Include fields for sandbox mode, writable roots, network availability, escalation request policy, and commands that are safe/unsafe to run.
- Define how skipped verification due to permission/network limits should be recorded.

### 9. Codexize MCP and tool-use policy

The core principle favors CLI and direct filesystem access unless an external system requires a tool. Codex has additional surfaces such as tool search, MCP resources, browser plugin, and local browser workflows.

Potential improvement:

- Define when to use shell/CLI, MCP resources, tool_search, browser plugin, and web search.
- Keep external-system access explicit and source-backed.
- Prefer repo-local files and commands for harness diagnosis unless the task requires live external state.
- Document how tool limitations or sandbox restrictions affect verification outcomes.

### 10. Add Codex examples

Claude has a `CLAUDE.md.example`; Codex currently has an `AGENTS.md.template` but not a completed example.

Potential improvement:

- Add `adapters/codex/examples/AGENTS.md.example` for a realistic project.
- Include trace root, search-set policy, permission notes, verify commands, and autoresearch pointer.
- Keep the example distinct from the template: template is a scaffold, example is an onboarding reference.

### 11. Test Codex adapter on real project types

The Codex skills should be exercised on representative projects and refined from traces.

Potential improvement:

- Apply `init-codex-harness` to a TypeScript app.
- Apply it to a Python research repo.
- Apply it to an existing project with `.claude/traces/` history.
- Review the generated traces and search-set entries, then update skill docs based on observed failures.

### 12. Provide a Codex autoresearch protection checker reference implementation

The `autoresearch` skill now defines the checker contract, but does not ship a reference implementation.

Potential improvement:

- Provide `scripts/check-autoresearch-protected.py` as a template or skill asset.
- Support Codex `PreToolUse`, Codex `PermissionRequest`, pre-commit, and CI modes.
- Parse protected paths from `.harness/autoresearch-protected.txt`.
- Include tests for exact path/prefix matching and protected-path violations.

### 13. Make Codex hook smoke tests mechanically assert output

The skill lists smoke-test commands and expected fields, but not assertion commands that fail when the returned JSON shape is wrong.

Potential improvement:

- Add `python -c` or `jq -e` assertions for `hookSpecificOutput.permissionDecision == "deny"`.
- Add assertions for `hookSpecificOutput.decision.behavior == "deny"` in `PermissionRequest`.
- Ensure smoke tests fail non-zero when the checker returns legacy or malformed JSON.

### 14. Track Codex hook schema drift

Codex hook output shapes may change over time. The adapter now depends on current `PreToolUse` and `PermissionRequest` semantics.

Potential improvement:

- Add a note to check official Codex hooks docs before changing hook templates.
- Record the verified hook schema date or Codex version in release notes when templates change.
- Add a backlog review item whenever Codex hook interception semantics change.

### 15. Clarify local-only protection reporting

The `autoresearch` skill allows local-only protection when CI is unavailable, but the reporting format can be more explicit.

Potential improvement:

- Add `Protection level: local-only | shared-repo | structural | incomplete` to setup output.
- Treat skipped minimum local protection as incomplete/unsafe, not merely skipped.
- Treat skipped CI as local-only with explicit reason.

## Current Status

- Source reviews: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` and `adapters/codex/skills/autoresearch/SKILL.md`.
- Last reviewed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
