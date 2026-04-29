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
| v1 protection | Autoresearch checker and protected-path template implemented; hook templates and install smoke-test docs planned | Partial |
| Later release | Examples, marketplace metadata, richer install validation | Planned |

The Meta-Harness paper informs the acceptance criteria for this scope, but its methodology remains in `core/`; the plugin should not copy core content into a Codex-specific fork.

## Autoresearch Protection Assets

The generated plugin now carries a reference checker at `scripts/check-autoresearch-protected.py` and a protected-path template at `templates/autoresearch-protected.txt`. These are project assets to copy during autoresearch setup; they are not advertised as active plugin runtime hooks until hook templates and local activation smoke tests exist.

## Local Development Install

Generate and verify the repo-local plugin bundle before local Codex dogfooding:

```bash
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
```

The generated plugin lives at `plugins/ai-agent-meta-harness/`. The exact Codex local-plugin activation command is intentionally not documented here until it has a repo smoke test; track that in `backlog/codex-adapter.md`.

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
