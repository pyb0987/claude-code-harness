#!/usr/bin/env python3
"""Smoke-test autoresearch protection checker hook output shapes.

Run from a target project after installing:
- scripts/check-autoresearch-protected.py
- .harness/autoresearch-protected.txt

This script asserts the Codex hook JSON contract mechanically so malformed or
legacy hook outputs fail with a non-zero exit code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
DEFAULT_CHECKER = Path("scripts/check-autoresearch-protected.py")
DEFAULT_PROTECTED = Path(".harness/autoresearch-protected.txt")
HOOK_SCHEMA_REFERENCE = "adapters/codex/hook-schema.md"
HOOK_SCHEMA_VERIFIED_DATE = "2026-04-30"
HOOK_SCHEMA_CODEX_CLI_VERSION = "0.126.0-alpha.8"


class SmokeFailure(Exception):
    pass


def run_checker(checker: Path, protected_file: Path, mode: str, payload: dict) -> dict:
    result = subprocess.run(
        ["python3", str(checker), mode, "--protected-file", str(protected_file)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SmokeFailure(f"{mode} exited {result.returncode}: {result.stderr.strip()}")
    if not result.stdout.strip():
        raise SmokeFailure(f"{mode} produced no blocking JSON")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{mode} produced invalid JSON: {exc}: {result.stdout!r}") from exc


def assert_no_legacy_top_level_decision(body: dict, mode: str) -> None:
    if "decision" in body:
        raise SmokeFailure(f"{mode} used legacy top-level decision shape")


def assert_pre_tool_use(body: dict) -> None:
    assert_no_legacy_top_level_decision(body, "PreToolUse")
    output = body.get("hookSpecificOutput")
    if not isinstance(output, dict):
        raise SmokeFailure("PreToolUse missing hookSpecificOutput object")
    expected_keys = {"hookEventName", "permissionDecision", "permissionDecisionReason"}
    if set(output) != expected_keys:
        raise SmokeFailure(f"PreToolUse hookSpecificOutput keys differ: {sorted(output)}")
    if output["hookEventName"] != "PreToolUse":
        raise SmokeFailure("PreToolUse hookEventName mismatch")
    if output["permissionDecision"] != "deny":
        raise SmokeFailure("PreToolUse permissionDecision must be deny")
    if "evaluate.py" not in output["permissionDecisionReason"]:
        raise SmokeFailure("PreToolUse deny reason must name evaluate.py")


def assert_permission_request(body: dict) -> None:
    assert_no_legacy_top_level_decision(body, "PermissionRequest")
    output = body.get("hookSpecificOutput")
    if not isinstance(output, dict):
        raise SmokeFailure("PermissionRequest missing hookSpecificOutput object")
    if set(output) != {"hookEventName", "decision"}:
        raise SmokeFailure(f"PermissionRequest hookSpecificOutput keys differ: {sorted(output)}")
    if output["hookEventName"] != "PermissionRequest":
        raise SmokeFailure("PermissionRequest hookEventName mismatch")
    decision = output.get("decision")
    if not isinstance(decision, dict):
        raise SmokeFailure("PermissionRequest decision must be an object")
    if set(decision) != {"behavior", "message"}:
        raise SmokeFailure(f"PermissionRequest decision keys differ: {sorted(decision)}")
    if decision["behavior"] != "deny":
        raise SmokeFailure("PermissionRequest decision.behavior must be deny")
    if "evaluate.py" not in decision["message"]:
        raise SmokeFailure("PermissionRequest deny message must name evaluate.py")


def ensure_protected_file(path: Path) -> None:
    if not path.exists():
        raise SmokeFailure(f"protected path file does not exist: {path}")
    entries = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    active = [line for line in entries if line and not line.startswith("#")]
    if "evaluate.py" not in active:
        raise SmokeFailure(f"{path} must contain evaluate.py for this smoke test")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=Path, default=DEFAULT_CHECKER)
    parser.add_argument("--protected-file", type=Path, default=DEFAULT_PROTECTED)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checker = args.checker
    protected_file = args.protected_file
    try:
        if not checker.exists():
            raise SmokeFailure(f"checker does not exist: {checker}")
        ensure_protected_file(protected_file)
        pre_tool_payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "command": "*** Begin Patch\n*** Update File: evaluate.py\n@@\n-pass\n+pass\n*** End Patch"
            },
        }
        permission_payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {
                "command": "python3 -c \"open('evaluate.py', 'w').write('x')\"",
                "description": "requesting escalation to write evaluator",
            },
        }
        assert_pre_tool_use(run_checker(checker, protected_file, "--codex-pre-tool-use", pre_tool_payload))
        assert_permission_request(run_checker(checker, protected_file, "--codex-permission-request", permission_payload))
    except SmokeFailure as exc:
        print(f"autoresearch hook smoke test failed: {exc}", file=sys.stderr)
        return 1
    print("Autoresearch hook smoke assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
