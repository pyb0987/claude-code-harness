# Maintenance Plan

This repository is a maintainable Meta-Harness artifact, not only a document
collection. The primary maintenance goal is to keep the shared methodology,
runtime adapters, generated bundles, and compatibility surfaces aligned while
the harness evolves.

## Maintenance Model

Maintain the repo as three layers:

| Layer | Owns | Maintenance Rule |
|-------|------|------------------|
| Core | Runtime-neutral methodology, trace semantics, verification policy | Edit once in `core/`; do not fork into adapters unless runtime behavior differs |
| Adapters | Runtime-specific instructions, paths, hooks, install UX, examples | Keep runtime assumptions explicit and backed by smoke tests where possible |
| Generated and compatibility surfaces | Codex plugin bundle, temporary Claude mirrors | Treat as derived artifacts; enforce drift checks in pre-commit and release checks |

The Meta-Harness paper remains the acceptance frame: optimize the environment
around the agent, preserve raw evidence, prefer additive harness changes, keep
the evaluator boundary clean, and measure regressions with executable checks
where possible.

## Backlog Policy

Backlog items are grouped by ownership in `backlog/` and by theme in
`backlog/README.md`.

Use this workflow for backlog work:

1. Pick a theme and one concrete item.
2. Implement the smallest useful contract, document, smoke test, or adapter
   change.
3. Run the relevant checks before review.
4. Use multi-review for adapter behavior, release gates, hook semantics, or
   anything that can steer future work in the wrong direction.
5. If reviewers score below 9, treat it as a veto and iterate.
6. Record reasons for not reaching 10 only when they are actionable future work.

When a backlog item becomes implemented foundation, keep it in place but change
the wording from "Potential improvement" to "Decision implemented" plus
"Remaining follow-up work". This preserves history without making completed
work look unstarted.

## Test Policy

Tests should cover repository contracts, not prose taste.

Add or keep tests for:

- Derived artifact drift, such as compatibility mirrors and generated plugin
  bundles.
- Runtime path contracts, such as `.claude/traces/`, `.claude/hooks/`, and
  `.harness/traces/`.
- Hook and checker output shapes consumed by agent runtimes.
- Evaluator or protected-file boundaries that must not be silently bypassed.
- Index-vs-working-tree behavior for pre-commit checks.
- Install, activation, or target-project smoke tests when the runtime can be
  exercised mechanically.

Do not add tests for:

- Preferred wording, tone, or explanatory style.
- Methodology judgment that needs human review.
- Agent behavior that cannot be observed without a real runtime surface.

Use unit tests for pure validators and temp-repo integration tests for Git
index semantics. Prefer smoke tests when the artifact is a generated bundle or
runtime-facing install surface.

## Standard Verification

Before committing ordinary repository changes, run:

```bash
python3 scripts/check-compat-mirrors.py
python3 scripts/check-claude-adapter-paths.py
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
```

The tracked pre-commit hook runs the drift and smoke checks:

```bash
git config core.hooksPath .githooks
sh .githooks/pre-commit
```

Run targeted tests while iterating, but run the standard verification set before
multi-review and before release-like commits.

## Release Checklist

Use this checklist before tagging, publishing, or treating `main` as a stable
handoff point:

- Compatibility mirrors pass from the Git index.
- Claude adapter path contract check passes.
- Codex plugin sync check passes.
- Codex local plugin artifact smoke test passes.
- Codex hook schema drift check passes; hook-sensitive changes update or
  intentionally re-verify `adapters/codex/hook-schema.md`.
- Unit and integration tests pass for root, Claude adapter, and Codex adapter
  test suites.
- README repository name, install commands, and adapter paths match the current
  repo layout.
- Backlog entries touched by the change are updated from potential work to
  implemented foundation when appropriate.
- Multi-review is recorded or summarized for high-impact adapter or release-gate
  changes.

## Multi-Review Use

Use multi-review when a change affects:

- Adapter direction or install/distribution UX.
- Hook enforcement or protected-file semantics.
- Release gates and pre-commit behavior.
- Core methodology boundaries.
- Anything that future harness-engineer or autoresearch work will build on.

Reviewer scores below 9 are vetoes. Scores of 9 mean the change is acceptable
with remaining risk tracked. Scores of 10 should be rare and reserved for cases
where there is no meaningful known follow-up.

## Near-Term Maintenance Sequence

The next high-leverage sequence is:

1. Finish release-gate clarity: choose semantics for generated artifact checks
   in `scripts/sync-codex-plugin.py`.
2. Add Claude `/init-harness` fixture smoke coverage.
3. Strengthen Codex install/activation smoke once the local plugin activation
   path is mechanically known.
4. Consolidate trace lifecycle rules in core, then keep Codex-specific
   `.claude/traces` to `.harness/traces` migration behavior in the Codex
   adapter.
5. Add realistic Codex examples only after one or more real project dry runs.
