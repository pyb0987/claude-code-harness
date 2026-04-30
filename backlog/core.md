# Core Backlog

Agent-agnostic quality backlog for the shared Meta-Harness methodology. These items came from the strict multi-review of the Codex `harness-engineer` skill, but their ownership belongs in the shared core because they apply across agents.

## Priority Candidates

### 1. Add autoresearch detection heuristics

Current adapter wording says "if the project uses autoresearch", which leaves detection to the agent.

Potential improvement:

- Treat a project as autoresearch when two or more of these are present: `program.md`, `evaluate.py`, `experiments.jsonl`, `auto-search/session-*`, `{trace_root}/experiments/`.
- If only one signal exists, inspect nearby docs before deciding.
- If signals conflict, record uncertainty in the proposal instead of applying autoresearch-specific changes blindly.

### 2. Define meaningful trace history tie-breakers

When more than one trace root or trace history exists, the harness should define how to choose the active history.

Potential improvement:

- Prefer roots with `search-set.md` and Active cases.
- Prefer roots with unresolved failures, recent evolution entries, or experiment episodes relevant to the current issue.
- Treat divergent non-empty roots as a migration question, not as a normal write target.

### 3. Strengthen Active seed verification quality rules

The methodology requires auto-executable verify commands, but should define what makes one good enough.

Potential improvement:

- Verify commands should be deterministic, non-interactive, and fail with a non-zero exit code on regression.
- Prefer local commands that avoid network and high cost.
- Record sandbox, permission, or network requirements explicitly when applicable.
- Avoid verify commands that only print information without checking the failure pattern.

## Later Improvements

### 4. Handle partially initialized trace roots

A trace root may exist while one or more required subdirectories or files are missing.

Potential improvement:

- After selecting a trace root, check for `evolution/`, `failures/`, `experiments/`, and `search-set.md`.
- For applied harness changes, create missing minimum directories/files before writing traces.
- For diagnosis-only requests, report missing trace infrastructure in the proposal.

### 5. Specify Archived case restore and re-archive workflow

The methodology allows restoring Archived search-set cases but should define when to re-archive them.

Potential improvement:

- Restore Archived cases when the same failure class recurs or when validating a harness change that touches the same prevention.
- Re-archive after the new prevention has passed and the case no longer needs active regression coverage.
- Update `archived_reason` with the date and reason for re-archive.

### 6. Expand standalone autoresearch reference details

Standalone users may benefit from a short relationship map around autoresearch trace artifacts.

Potential improvement:

- State that `experiments.jsonl` records machine-readable "what" and episode traces record diagnostic "why".
- Include a minimum `program.md ## Rejection History` example.
- Clarify that episode traces may be written multiple times in one session.

### 7. Define documentation abstraction boundaries

The repository now has a shared core plus runtime adapters. The boundary should be made explicit so future work does not duplicate methodology across adapters.

Potential improvement:

- Core owns what/why: methodology principles, trace semantics, verification policy, general failure recording, and agent-agnostic workflow contracts.
- Adapters own how: runtime-specific instruction files, hook schemas, permission models, install paths, tool surfaces, and examples.
- Add a short document-writing rule that says adapter docs may reference core rules but should not fork them unless runtime behavior truly differs.
- During review, flag copied methodology blocks in adapters as possible drift risks.

### 8. Plan compatibility mirror removal

Temporary top-level Claude paths are currently retained as compatibility mirrors. They need a removal plan before they become permanent accidental API.

Potential improvement:

- Define the removal milestone or release window.
- Add a warning strategy before removal, such as README notice, release note, or pre-commit warning period.
- Decide whether old install commands should fail fast with guidance or keep thin redirect docs.
- Document the migration path for users with scripts that still read `docs/`, `commands/`, or `skills/`.

### 9. Define repository release checklist

Release readiness should be verified with a stable checklist instead of ad hoc manual review.

Potential improvement:

- Mirror sync check.
- README URL and repository-name check.
- Skill frontmatter validation.
- Adapter install smoke tests.
- Old Claude install command smoke test while compatibility mirrors exist.
- Codex install smoke test for the chosen primary distribution path.
- Release note entry for adapter/core behavior changes.

### 10. Make repository drift checks staged-content-aware

Pre-commit checks should validate the content that will actually be committed,
not only the current working tree. The Claude adapter path checker already reads
indexed files, but other repository drift checks should converge on the same
semantics.

Decision implemented for compatibility mirrors:

- `scripts/check-compat-mirrors.py` now checks the fixed required mirror path
  list against the Git index and reads canonical/mirror contents with
  `git show :path`.
- Unstaged working-tree drift does not affect pre-commit results.
- Staged mirror drift and staged deletion of required canonical/mirror files
  fail the check.
- Temp-git integration tests cover unstaged drift, staged modified mirrors, and
  staged deleted mirrors.

Remaining follow-up work:

- Decide whether generated artifact checks should use index content, working
  tree content, or an explicit mode flag.
- Add tests for staged-added, staged-modified, and staged-deleted paths that are
  relevant to generated-artifact drift.
- Add temp-git staged-added coverage if the compatibility mirror contract starts
  accepting newly introduced mirror pairs during the transition period.

## Current Status

- Source review: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md`.
- Last reviewed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Recommended next quality pass: start with autoresearch detection heuristics, then trace-history tie-breakers, then verify-command quality rules.
