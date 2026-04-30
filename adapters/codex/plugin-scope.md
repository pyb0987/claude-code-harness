# Codex Plugin Bundle Scope

This document defines what belongs in the Codex plugin bundle and what remains
outside it. The shared harness methodology stays in `core/`; this bundle carries
only the Codex runtime adapter surfaces needed to apply that methodology.

## Scope Stages

| Stage | Bundle contents | Status |
|-------|-----------------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, and CI template implemented; install docs planned | Partial |
| Later release | Examples, marketplace metadata, richer install validation, optional generated assets | Planned |

## Current Generated Contents

The generated plugin at `plugins/ai-agent-meta-harness/` currently includes:

- `.codex-plugin/plugin.json`
- `README.md`
- `hook-schema.md`
- `plugin-scope.md`
- `skills/autoresearch/SKILL.md`
- `skills/harness-engineer/SKILL.md`
- `skills/init-codex-harness/SKILL.md`
- `skills/multi-review/SKILL.md`
- `templates/AGENTS.md.template`
- `templates/autoresearch-protected.txt`
- `templates/hooks/codex-hooks.json.template`
- `templates/hooks/pre-commit-autoresearch-protected.sh`
- `templates/hooks/github-actions-autoresearch-protected.yml`
- `templates/hooks/agents-autoresearch-protection.md`
- `scripts/check-autoresearch-protected.py`
- `scripts/check-codex-hook-schema-drift.py`
- `scripts/smoke-autoresearch-hooks.py`
- `scripts/smoke-local-plugin.py`

The sync map copies only explicitly listed template and script files. Future templates or scripts must be added to this scope document and the sync map before they ship in the generated plugin.

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

## v1 Canonical Path Policy

| Asset class | Canonical source | Generated plugin path | Notes |
|-------------|------------------|-----------------------|-------|
| Codex hook templates | `adapters/codex/templates/hooks/codex-hooks.json.template` | `templates/hooks/codex-hooks.json.template` | Template-only guardrail; hard enforcement stays in pre-commit/CI until activation and tool coverage are smoke-tested |
| Pre-commit template | `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` | `templates/hooks/pre-commit-autoresearch-protected.sh` | Hard local guardrail using the shared checker |
| CI template | `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml` | `templates/hooks/github-actions-autoresearch-protected.yml` | Pull-request guardrail using the shared checker |
| AGENTS reminder snippet | `adapters/codex/templates/hooks/agents-autoresearch-protection.md` | `templates/hooks/agents-autoresearch-protection.md` | Level 1 instruction layer for target projects |
| Runtime Codex hook config | `adapters/codex/hooks/` | `hooks/` plus manifest `hooks` field | Only after local activation smoke test passes |
| Autoresearch checker reference | `adapters/codex/scripts/check-autoresearch-protected.py` | `scripts/check-autoresearch-protected.py` | Shared by Codex hooks, pre-commit, and CI templates |
| Hook schema drift reference | `adapters/codex/hook-schema.md` | `hook-schema.md` | Records verified Codex hook output assumptions and official source URLs |
| Hook schema drift checker | `adapters/codex/scripts/check-codex-hook-schema-drift.py` | `scripts/check-codex-hook-schema-drift.py` | Fails when hook-sensitive staged changes omit schema re-verification |
| Hook smoke assertions | `adapters/codex/scripts/smoke-autoresearch-hooks.py` | `scripts/smoke-autoresearch-hooks.py` | Mechanically asserts Codex hook deny JSON shapes |
| Local plugin artifact smoke test | `adapters/codex/scripts/smoke-local-plugin.py` | `scripts/smoke-local-plugin.py` | Verifies manifest, expected skills, protection assets, and degraded fallback warning |
| Protected-path template | `adapters/codex/templates/autoresearch-protected.txt` | `templates/autoresearch-protected.txt` | Project bootstrap asset copied to `.harness/autoresearch-protected.txt` |
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
- Immutable evaluator protection uses a shared checker plus structural templates in v1.
- Enforcement assets should be shared by hooks, pre-commit, and CI where possible.
- Scope should grow additively: ship v0, add v1 protection assets, then add release metadata.
