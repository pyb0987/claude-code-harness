# Codex Adapter

Codex support is an adapter over the shared harness core, not a fork of the methodology.

## Current Scope

The first Codex adapter layer provides:

- `init-codex-harness` skill for project bootstrap
- `harness-engineer` skill for Codex harness evolution
- `AGENTS.md` template for project-local instructions
- Trace filesystem guidance using `.harness/traces/` by default
- Explicit verify-command discipline in place of Claude Code `PostToolUse` hooks

## Design Choices

- Shared principles stay in `core/methodology.md` and `core/reference.md`.
- Codex-specific behavior lives here: skill trigger wording, project instruction filenames, verification workflow, and sub-agent usage.
- Claude Code hook schemas are not copied into Codex. Codex enforcement should be implemented through CI, git hooks, project-local scripts, or future Codex plugin hooks.

## Local Development Install

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
```

Then ask Codex:

```text
apply codex-harness to this project
```
