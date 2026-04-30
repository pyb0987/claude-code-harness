# Codex Hook Schema Reference

This reference records the Codex hook contract that the Codex adapter currently
depends on. It is an adapter-maintainer guardrail, not shared Meta-Harness core
methodology.

This drift check validates documented output-shape assumptions only. It does not prove hook event coverage, command interception coverage, or Codex plugin runtime activation.

## Verification Metadata

- Verified date: 2026-04-30
- Codex CLI checked: 0.126.0-alpha.8
- Primary source: https://developers.openai.com/codex/hooks
- Config source: https://developers.openai.com/codex/config-reference

Before changing Codex hook templates, hook checker output, or autoresearch hook
instructions, check the official Codex hooks documentation again and update this
file if the contract changed or was re-verified.

## Expected Blocking Output Shapes

### PreToolUse

The adapter expects protected-path denials to return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Autoresearch evaluator boundary violation: protected path evaluate.py would be modified."
  }
}
```

Expected `hookSpecificOutput` keys:

- `hookEventName`
- `permissionDecision`
- `permissionDecisionReason`

### PermissionRequest

The adapter expects escalation denials to return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Autoresearch evaluator boundary violation: protected path evaluate.py would be modified."
    }
  }
}
```

Expected `hookSpecificOutput` keys:

- `hookEventName`
- `decision`

Expected nested `decision` keys:

- `behavior`
- `message`

Do not use the legacy top-level `{"decision": "block"}` shape for this adapter.

## Drift Procedure

When a hook-sensitive adapter file changes:

1. Re-check the official Codex hooks and config documentation.
2. Update `Verified date` and `Codex CLI checked` above if the schema was
   re-verified.
3. Re-run `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py` in a
   target-project fixture with `.harness/autoresearch-protected.txt`.
4. Re-run `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`.
5. If Codex interception semantics changed, add or update a backlog item before
   enabling runtime hook manifest fields.
