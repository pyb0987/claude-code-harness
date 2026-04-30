# Codex Adapter

Codex support is an adapter over the shared harness core, not a fork of the methodology.

## Current Scope

The first Codex adapter layer provides:

- `init-codex-harness` skill for project bootstrap
- `harness-engineer` skill for Codex harness evolution
- `autoresearch` skill for measurable autonomous experiment loops
- `AGENTS.md` template for project-local instructions
- Trace filesystem guidance using `.harness/traces/` by default
- Codex hook enforcement strategy plus explicit verify-command discipline in place of Claude Code hook assumptions

## Design Choices

- Shared principles stay in `core/methodology.md` and `core/reference.md`.
- Codex-specific behavior lives here: skill trigger wording, project instruction filenames, verification workflow, and sub-agent usage.
- Claude Code hook schemas are not copied into Codex. Codex enforcement should use Codex hooks where available, backed by CI, git hooks, and project-local scripts for hard enforcement.
- Non-blocking adapter follow-up work is tracked in `backlog/codex-adapter.md`; shared methodology follow-ups live in `backlog/core.md`.

## Distribution Decision

Primary distribution path: **local Codex plugin bundle**.

Rationale: the Codex adapter now includes more than standalone skill text. Autoresearch protection needs hooks, checker scripts, templates, and examples to travel together. A plugin bundle is the smallest distribution unit that can carry those assets without turning the adapter into a fork of the core methodology.

Source-of-truth rule: `adapters/codex/` is the canonical editable Codex adapter source. The local plugin bundle will be generated from it; manual dual-editing between adapter files and plugin files is not allowed.

Plugin layout decision:

- Plugin root: `plugins/ai-agent-meta-harness/`
- Canonical source: `adapters/codex/`
- Generated output: `plugins/ai-agent-meta-harness/`
- Sync command: `python3 scripts/sync-codex-plugin.py --write`
- Drift check: pre-commit/release checks must verify generated plugin files match canonical adapter files

Supported paths:

| Path | Status | Use |
|------|--------|-----|
| Local plugin bundle | Primary bundle artifact, scaffolded | Generated at `plugins/ai-agent-meta-harness/`; activation smoke test still pending |
| Direct skill copy | Development fallback | Fast iteration on skill text only |
| Marketplace/plugin bundle | Future release path | Published distribution after plugin layout stabilizes |
| `skill-installer` | Compatibility investigation | Skill-only install if safe degraded behavior is documented |

## Bundle Scope

The bundle scope is staged so packaging does not outrun tested behavior. Full details live in `plugin-scope.md`.

| Stage | Includes | Status |
|-------|----------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, and CI template implemented; install docs planned | Partial |
| Later release | Examples, marketplace metadata, richer install validation | Planned |

The Meta-Harness paper informs the acceptance criteria for this scope, but its methodology remains in `core/`; the plugin should not copy core content into a Codex-specific fork.

## Autoresearch Protection Assets

The generated plugin now carries a reference checker at `scripts/check-autoresearch-protected.py`, hook JSON smoke assertions at `scripts/smoke-autoresearch-hooks.py`, a protected-path template at `templates/autoresearch-protected.txt`, and enforcement templates plus an AGENTS reminder snippet under `templates/hooks/`. These are project assets to copy during autoresearch setup; they are not advertised as active plugin runtime hooks until local activation smoke tests exist.

Hook schema drift is tracked in `hook-schema.md`. Before changing Codex hook templates, checker hook output, or autoresearch hook instructions, re-check the official Codex hooks documentation and run `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`.

## Local Development Install

Generate and verify the repo-local plugin bundle before artifact-level dogfooding:

```bash
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py --skip-staged-policy
python3 adapters/codex/scripts/smoke-local-plugin.py
```

The generated plugin lives at `plugins/ai-agent-meta-harness/`. The smoke test validates the bundle artifact: manifest, expected skills, checker/hook/template assets, and degraded fallback warnings. The exact Codex local-plugin activation command is intentionally not documented here until Codex activation can be exercised mechanically; track that in `backlog/codex-adapter.md`.

Until the activation workflow is validated, use the degraded direct-copy fallback for executable local skill iteration:

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
```

This fallback does not install Codex hooks, checker scripts, templates outside bundled skill assets, or plugin metadata. Do not treat it as the full autoresearch safety path.

Then ask Codex:

```text
apply codex-harness to this project
```
