# Tests

The test suite treats this repository as a harness artifact. Tests protect
machine-checkable contracts; multi-review protects judgment-heavy methodology
and adapter direction.

## Test Areas

| Area | Path | Purpose |
|------|------|---------|
| Repository contracts | `tests/` | Cross-cutting repo checks, Git index semantics, compatibility mirrors |
| Claude adapter | `adapters/claude/tests/` | Claude Code path contracts and adapter-specific validators |
| Codex adapter | `adapters/codex/tests/` | Codex hook/checker/plugin/template contracts |

## Run Tests

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
```

Run the tracked pre-commit hook for drift and smoke checks:

```bash
sh .githooks/pre-commit
```

## Add Tests When

- A rule can be checked deterministically.
- A generated or mirrored artifact can drift.
- A hook/checker output shape is consumed by an agent runtime.
- A pre-commit or release gate depends on Git index behavior.
- A target-project smoke test can prove install or initialization output.

Prefer temp-repo integration tests for Git behavior and pure unit tests for
text validators.
