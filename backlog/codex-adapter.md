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

- Scaffold `plugins/ai-agent-meta-harness/.codex-plugin/plugin.json`.
- Implement adapter-canonical sync from `adapters/codex/` into `plugins/ai-agent-meta-harness/` using `python3 scripts/sync-codex-plugin.py`.
- Add or extend a drift check so generated plugin files cannot silently diverge from canonical adapter files.
- Add a local plugin install smoke test.
- Decide how the fallback direct-copy path reports missing hooks/checker assets.
- Keep README install instructions aligned with the plugin layout.

### 5. Define Codex plugin bundle scope

Decision: Codex support should become a local plugin bundle. The remaining question is what ships in the first bundle.

Potential improvement:

- Add `.codex-plugin/plugin.json` under `plugins/ai-agent-meta-harness/`.
- Include skills, Codex hook templates, protection checker templates, AGENTS template, and example docs.
- Keep `adapters/codex/` canonical and generate plugin files from it.
- Define the generated path mapping, then add a drift check for those paths.
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

### 16. Implement the Codex plugin layout decision

Decision: use `plugins/ai-agent-meta-harness/` as the generated local plugin root, with `adapters/codex/` remaining canonical.

Follow-up work:

- Scaffold `plugins/ai-agent-meta-harness/.codex-plugin/plugin.json`.
- Implement `python3 scripts/sync-codex-plugin.py` to generate plugin files from canonical adapter files.
- Define sync modes, at minimum `--write` to materialize files and `--check` to fail on drift without modifying files.
- Use `--check` from pre-commit and release checks; it should fail when generated files are missing, stale, extra, or mapped to no canonical source.
- Define the generated path mapping for skills, hook templates, protection checker templates, AGENTS template, and examples.
- Decide how `.codex-plugin/plugin.json` metadata is authored versus generated.
- Extend compatibility checks so generated plugin files cannot drift from `adapters/codex/`.
- Consolidate overlapping plugin implementation backlog items once scaffolding begins, so item 4 tracks distribution execution and item 16 tracks layout/sync details.
- Document the local plugin install command once the root exists.

### 17. Define Codex plugin marketplace metadata policy

The marketplace path is future work, but plugin metadata choices can leak into local plugin structure if left implicit.

Potential improvement:

- Decide plugin name, display name, category, installation policy, and authentication policy.
- Keep marketplace metadata out of the local-only path unless needed for Codex UI ordering.
- Document when `.agents/plugins/marketplace.json` should be generated or updated.
- Avoid publishing-oriented metadata churn while the local plugin layout is still stabilizing.

### 18. Add local plugin install smoke test

The local plugin path cannot be considered ready until installation can be checked mechanically.

Potential improvement:

- Add a smoke test that validates `.codex-plugin/plugin.json` exists and parses.
- Verify expected skills are visible from the plugin bundle.
- Verify hook/checker assets are present in the bundle.
- Verify direct skill-copy fallback emits or documents a degraded-safety warning.
- Run the smoke test as part of the repository release checklist.

## Current Status

- Source reviews: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` and `adapters/codex/skills/autoresearch/SKILL.md`.
- Last reviewed baselines are the commits linked from the relevant review notes or release notes; avoid keeping a single stale baseline here.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
