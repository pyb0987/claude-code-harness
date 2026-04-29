# Codex Plugin Bundle Scope

This document defines what belongs in the Codex plugin bundle and what remains
outside it. The shared harness methodology stays in `core/`; this bundle carries
only the Codex runtime adapter surfaces needed to apply that methodology.

## Scope Stages

| Stage | Bundle contents | Status |
|-------|-----------------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Codex hook templates, autoresearch checker template, protected-path template, install/smoke-test docs | Planned |
| Later release | Examples, marketplace metadata, richer install validation, optional generated assets | Planned |

## Current v0 Contents

The generated plugin at `plugins/ai-agent-meta-harness/` currently includes:

- `.codex-plugin/plugin.json`
- `README.md`
- `plugin-scope.md`
- `skills/autoresearch/SKILL.md`
- `skills/harness-engineer/SKILL.md`
- `skills/init-codex-harness/SKILL.md`
- `skills/multi-review/SKILL.md`
- `templates/AGENTS.md.template`

The v0 sync map copies only explicitly listed template files. The only required v0 template is `AGENTS.md.template`. Future templates must be added to this scope document and the sync map before they ship in the generated plugin.

`adapters/codex/` remains the editable canonical source. Generated plugin files
must be updated with `python3 scripts/sync-codex-plugin.py --write` and checked
with `python3 scripts/sync-codex-plugin.py --check`.

## Inclusion Rules

Include a file in the plugin bundle when all of these are true:

- It is Codex-specific adapter surface, not shared methodology.
- It is useful at install or project bootstrap time.
- It can be generated from `adapters/codex/` without manual dual-editing.
- Its safety behavior is either executable now or explicitly marked as a template.

Do not include:

- Core methodology copies from `core/`.
- Claude adapter files or Claude hook schemas.
- Project-specific traces, evaluator outputs, or local secrets.
- Marketplace metadata until local activation is smoke-tested.

## Planned v1 Canonical Paths

| Asset class | Canonical source | Generated plugin path | Notes |
|-------------|------------------|-----------------------|-------|
| Codex hook templates | `adapters/codex/templates/hooks/` | `templates/hooks/` | Template-only until activation semantics are smoke-tested |
| Runtime Codex hook config | `adapters/codex/hooks/` | `hooks/` plus manifest `hooks` field | Only after local activation smoke test passes |
| Autoresearch checker template | `adapters/codex/scripts/` | `scripts/` | Shared by Codex hooks, pre-commit, and CI templates |
| Protected-path template | `adapters/codex/templates/` | `templates/` | Project bootstrap asset |
| Completed Codex example | `adapters/codex/examples/` | `examples/` | Added after a real project dry run |

## Manifest Rules

The manifest exposes only `skills` in v0 because the plugin currently ships
skills and static templates. Add manifest fields such as `hooks` only when the
repo has an executable hook config under `adapters/codex/hooks/` that is
smoke-tested through the local plugin activation path. Template-only files under
`templates/hooks/` should not be advertised as active runtime hooks.

## Methodology Boundary

Meta-Harness paper principles are acceptance criteria here, not duplicated
content. For this bundle, that means:

- Raw traces remain project files, not plugin state.
- Immutable evaluator protection needs structural templates in v1.
- Enforcement assets should be shared by hooks, pre-commit, and CI where possible.
- Scope should grow additively: ship v0, add v1 protection assets, then add release metadata.
