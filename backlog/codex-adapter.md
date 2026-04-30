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

Decision implemented: ship template-only Codex hook, pre-commit, and CI guardrails that call the shared autoresearch checker without advertising active runtime hooks in the plugin manifest.

Implemented foundation:

- `adapters/codex/templates/hooks/codex-hooks.json.template` calls the checker from Codex `PreToolUse` and `PermissionRequest`.
- `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` provides the local hard-block layer.
- `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml` provides a pull-request CI guardrail with full checkout history and explicit `BASE_REF`.
- `adapters/codex/templates/hooks/agents-autoresearch-protection.md` provides the Level 1 project-instruction reminder layer.
- `adapters/codex/tests/test_hook_templates.py` validates that templates call the shared checker in the expected modes.
- The plugin sync map generates these templates into `plugins/ai-agent-meta-harness/templates/hooks/`.

Remaining follow-up work:

- Add install/smoke-test docs that show exactly where to copy each template in a target project.
- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks` only after local plugin activation and tool-event coverage are smoke-tested.
- Revisit templates when Codex hook interception semantics change, especially whether file-edit tools emit `PreToolUse`.

### 4. Implement the chosen Codex distribution path

Decision: use a **local Codex plugin bundle** as the primary distribution path.

Status of paths:

- Local plugin bundle: primary bundle target for normal local development and dogfooding; activation smoke test still pending.
- Direct skill copy: development fallback for fast skill text iteration only.
- Marketplace/plugin bundle: future release path after local plugin layout stabilizes.
- `skill-installer`: compatibility investigation for skill-only degraded installs.

Implemented foundation:

- `plugins/ai-agent-meta-harness/.codex-plugin/plugin.json` is generated from canonical adapter metadata.
- `scripts/sync-codex-plugin.py --write` materializes the local plugin bundle from `adapters/codex/`.
- `scripts/sync-codex-plugin.py --check` fails on missing, stale, extra, invalid, binary-different, or semantically empty required plugin surfaces.
- `.githooks/pre-commit` runs the plugin drift check alongside compatibility mirror checks.
- README install guidance now points to the generated local plugin bundle first, with direct skill copy as a degraded fallback.

Remaining follow-up work:

- Add a real local plugin install smoke test once the exact Codex local-plugin activation workflow is documented.
- Decide how the fallback direct-copy path reports missing hooks/checker assets at runtime.
- Keep README install instructions aligned as hook/checker assets are added to the plugin bundle.

### 5. Define Codex plugin bundle scope

Decision implemented: use staged plugin scope so the bundle carries tested Codex adapter surfaces without copying shared core methodology. Details live in `adapters/codex/plugin-scope.md` and the generated plugin copy.

Implemented v0 scope:

- Include skills, explicitly mapped AGENTS template, README, plugin manifest, and plugin scope document.
- Keep `adapters/codex/` canonical and generate plugin files from it.
- Keep direct skill-copy installation only as a documented degraded path for skill text iteration.
- Treat Meta-Harness paper principles as acceptance criteria, not duplicated plugin content.

Remaining follow-up work:

- Runtime hook config under `adapters/codex/hooks/` and manifest `hooks` field are still gated on a local activation smoke test and verified Codex tool-event coverage; template hook/pre-commit/CI/AGENTS assets already exist under `adapters/codex/templates/hooks/`.
- Add completed Codex examples after a real project dry run.
- Expand `plugin.json` beyond `skills` only after runtime assets are executable and smoke-tested.
- Keep marketplace metadata deferred until local plugin activation is proven.

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

Decision implemented: ship a reference checker as a Codex plugin asset, plus a protected-path template and unit tests for the matcher and hook outputs.

Implemented foundation:

- `adapters/codex/scripts/check-autoresearch-protected.py` supports Codex `PreToolUse`, Codex `PermissionRequest`, pre-commit, and CI modes.
- `adapters/codex/templates/autoresearch-protected.txt` provides the project-local `.harness/autoresearch-protected.txt` starting point.
- `adapters/codex/tests/test_check_autoresearch_protected.py` covers exact path matching, prefix matching, Codex deny JSON shapes, and pre-commit violation detection.
- The plugin sync map generates checker and protected-path template assets into `plugins/ai-agent-meta-harness/`.

Remaining follow-up work:

- Add install/smoke-test docs that wire the checker and templates into a target project.
- Add a non-GitHub CI variant or document how to set `BASE_REF` outside GitHub Actions.

### 13. Make Codex hook smoke tests mechanically assert output

Decision implemented: ship an executable smoke assertion script that fails non-zero when Codex hook output JSON drifts from the expected event-specific deny shapes.

Implemented foundation:

- `adapters/codex/scripts/smoke-autoresearch-hooks.py` runs checker hook modes with protected `evaluate.py` payloads.
- The smoke script asserts `PreToolUse` returns `hookSpecificOutput.permissionDecision == "deny"`.
- The smoke script asserts `PermissionRequest` returns `hookSpecificOutput.decision.behavior == "deny"`.
- The smoke script rejects missing output, invalid JSON, malformed key sets, and the legacy top-level `decision` shape.
- The plugin sync map generates the smoke script into `plugins/ai-agent-meta-harness/scripts/`.

Remaining follow-up work:

- Add install docs that show when to run the smoke script during target-project setup.
- Re-run smoke assertions when Codex hook schemas change.

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

### 16. Extend the Codex plugin layout as assets grow

Decision implemented: `plugins/ai-agent-meta-harness/` is the generated local plugin root, with `adapters/codex/` remaining canonical. `scripts/sync-codex-plugin.py` owns `--write` and `--check`, and pre-commit runs the check.

Remaining follow-up work:

- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks` only after local plugin activation and tool-event coverage are smoke-tested; template hook/pre-commit/CI/AGENTS mappings are already implemented.
- Add examples to the generated path mapping when Codex examples are introduced.
- Decide whether `.codex-plugin/plugin.json` should remain hand-authored canonical metadata or become generated from a smaller metadata source.
- Document and smoke-test the exact local plugin activation command before calling the plugin path fully installed.
- Revisit marketplace metadata only after the local plugin activation path is proven.

### 17. Define Codex plugin marketplace metadata policy

The marketplace path is future work, but plugin metadata choices can leak into local plugin structure if left implicit.

Potential improvement:

- Decide plugin name, display name, category, installation policy, and authentication policy.
- Keep marketplace metadata out of the local-only path unless needed for Codex UI ordering.
- Document when `.agents/plugins/marketplace.json` should be generated or updated.
- Avoid publishing-oriented metadata churn while the local plugin layout is still stabilizing.

### 18. Add local plugin artifact smoke test

The local plugin bundle cannot be considered ready until the artifact can be checked mechanically. This item intentionally validates the generated plugin artifact, not Codex runtime activation.

Decision implemented: ship a local plugin artifact smoke test that validates the generated bundle before Codex dogfooding.

Implemented foundation:

- `adapters/codex/scripts/smoke-local-plugin.py` validates `.codex-plugin/plugin.json` exists, parses, and points skills at `./skills/`.
- The smoke test verifies the expected Codex skills exist and declare matching skill names.
- The smoke test verifies checker, hook smoke, hook templates, AGENTS template, and protected-path template assets are present and non-empty.
- The smoke test fails if the generated plugin README stops documenting the degraded direct-copy fallback safety warning.
- The smoke test rejects a manifest that advertises runtime `hooks` before Codex activation coverage is smoke-tested.
- Unit tests cover the passing bundle and missing-manifest, invalid-manifest, wrong-skills-path, runtime-hooks, missing-skill, missing-asset, and missing-warning failures.
- The tracked pre-commit hook runs the smoke test after the generated plugin sync check.

Remaining follow-up work:

- Add the local plugin artifact smoke test to the formal release checklist when that checklist is introduced.

### 19. Add true Codex local plugin activation smoke test

The artifact smoke test proves the generated plugin bundle is internally coherent, but it does not prove Codex has loaded the plugin in a running session.

Potential improvement:

- Identify the exact local Codex plugin activation command or manifest registration path for the supported Codex surface.
- Add an automated smoke test that installs or activates `plugins/ai-agent-meta-harness/` in an isolated Codex home and verifies the expected skills are discoverable through Codex.
- Keep runtime hook manifest fields gated until activation and tool-event coverage are both smoke-tested.

## Current Status

- Source reviews: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` and `adapters/codex/skills/autoresearch/SKILL.md`.
- Last reviewed baselines are the commits linked from the relevant review notes or release notes; avoid keeping a single stale baseline here.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
