## Autoresearch Protection

Autoresearch experiments must preserve the immutable evaluator boundary.
Protected paths are listed in `.harness/autoresearch-protected.txt`; exact paths
protect one file, and entries ending in `/` protect a prefix.

Do not edit protected evaluator files, protected evaluator dependencies,
`program.md`, or `best_score.txt` during Run Mode. `best_score.txt` may change
only through `evaluate.py` on an `ADOPT` verdict.

Before committing or escalating an experiment change, run:

```bash
python3 scripts/check-autoresearch-protected.py --pre-commit
```

Codex hook, pre-commit, and CI templates should call the same checker. Treat
Codex hooks as guardrails, not the sole security boundary: hook coverage can vary
by Codex surface and version, so pre-commit and CI must remain the hard block. If
any protection layer is unavailable, record the skipped layer and reason in the
experiment or setup trace; do not treat missing enforcement as equivalent to PASS.
