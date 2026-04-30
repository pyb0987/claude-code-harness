#!/usr/bin/env python3
"""Check that Codex hook schema assumptions are recorded and refreshed.

The script has two jobs:
- validate the adapter's hook schema reference contains the currently expected
  contract markers; and
- in pre-commit, require that hook-sensitive staged changes are accompanied by
  a staged update to the schema reference.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PATH = Path("adapters/codex/hook-schema.md")
VERIFIED_DATE = "2026-04-30"
CODEX_CLI_VERSION = "0.126.0-alpha.8"
PRIMARY_SOURCE = "https://developers.openai.com/codex/hooks"
CONFIG_SOURCE = "https://developers.openai.com/codex/config-reference"

HOOK_SENSITIVE_PATHS = {
    "adapters/codex/hook-schema.md",
    "adapters/codex/scripts/check-autoresearch-protected.py",
    "adapters/codex/scripts/check-codex-hook-schema-drift.py",
    "adapters/codex/scripts/smoke-autoresearch-hooks.py",
    "adapters/codex/skills/autoresearch/SKILL.md",
    "adapters/codex/templates/hooks/agents-autoresearch-protection.md",
    "adapters/codex/templates/hooks/codex-hooks.json.template",
}

REQUIRED_REFERENCE_MARKERS = (
    f"Verified date: {VERIFIED_DATE}",
    f"Codex CLI checked: {CODEX_CLI_VERSION}",
    PRIMARY_SOURCE,
    CONFIG_SOURCE,
    '"hookEventName": "PreToolUse"',
    '"permissionDecision": "deny"',
    '"permissionDecisionReason"',
    '"hookEventName": "PermissionRequest"',
    '"decision"',
    '"behavior": "deny"',
    '"message"',
    'legacy top-level `{"decision": "block"}` shape',
    "does not prove hook event coverage",
)

SMOKE_SCRIPT_PATH = Path("adapters/codex/scripts/smoke-autoresearch-hooks.py")
REQUIRED_SMOKE_MARKERS = (
    'HOOK_SCHEMA_REFERENCE = "adapters/codex/hook-schema.md"',
    f'HOOK_SCHEMA_VERIFIED_DATE = "{VERIFIED_DATE}"',
    f'HOOK_SCHEMA_CODEX_CLI_VERSION = "{CODEX_CLI_VERSION}"',
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_reference_text(text: str) -> list[str]:
    return [f"missing hook schema reference marker: {marker}" for marker in REQUIRED_REFERENCE_MARKERS if marker not in text]


def read_worktree_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_staged_text(path: Path) -> str:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise FileNotFoundError(result.stderr.strip() or f"missing staged file: {path}")
    return result.stdout


def text_for_validation(path: Path, staged_paths: list[str] | None) -> str:
    if staged_paths is not None and str(path) in staged_paths:
        return read_staged_text(path)
    return read_worktree_text(ROOT / path)


def reference_text_for_validation(staged_paths: list[str] | None) -> str:
    return text_for_validation(REFERENCE_PATH, staged_paths)


def validate_reference_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"missing hook schema reference: {rel(path)}"]
    except OSError as exc:
        return [f"unreadable hook schema reference: {rel(path)}: {exc}"]
    return validate_reference_text(text)


def validate_reference_source(staged_paths: list[str] | None) -> list[str]:
    try:
        text = reference_text_for_validation(staged_paths)
    except FileNotFoundError as exc:
        return [f"missing hook schema reference: {REFERENCE_PATH}: {exc}"]
    except OSError as exc:
        return [f"unreadable hook schema reference: {REFERENCE_PATH}: {exc}"]
    return validate_reference_text(text)


def validate_smoke_metadata_text(text: str) -> list[str]:
    return [f"missing hook smoke metadata marker: {marker}" for marker in REQUIRED_SMOKE_MARKERS if marker not in text]


def validate_smoke_metadata(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"missing hook smoke script: {rel(path)}"]
    except OSError as exc:
        return [f"unreadable hook smoke script: {rel(path)}: {exc}"]
    return validate_smoke_metadata_text(text)


def validate_smoke_metadata_source(staged_paths: list[str] | None) -> list[str]:
    try:
        text = text_for_validation(SMOKE_SCRIPT_PATH, staged_paths)
    except FileNotFoundError as exc:
        return [f"missing hook smoke script: {SMOKE_SCRIPT_PATH}: {exc}"]
    except OSError as exc:
        return [f"unreadable hook smoke script: {SMOKE_SCRIPT_PATH}: {exc}"]
    return validate_smoke_metadata_text(text)


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --cached failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def validate_staged_policy(paths: list[str]) -> list[str]:
    changed_sensitive = sorted(HOOK_SENSITIVE_PATHS.intersection(paths) - {str(REFERENCE_PATH)})
    if not changed_sensitive or str(REFERENCE_PATH) in paths:
        return []
    changed = ", ".join(changed_sensitive)
    return [
        "hook-sensitive staged changes require a staged "
        f"{REFERENCE_PATH} update or re-verification: {changed}"
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-staged-policy", action="store_true", help="only validate the reference content")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    staged_paths = None
    if not args.skip_staged_policy:
        try:
            staged_paths = staged_files()
        except RuntimeError as exc:
            staged_paths = []
            errors = [str(exc)]
        else:
            errors = []
    else:
        errors = []

    errors.extend(validate_reference_source(staged_paths))
    errors.extend(validate_smoke_metadata_source(staged_paths))
    if not args.skip_staged_policy:
        errors.extend(validate_staged_policy(staged_paths or []))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Codex hook schema drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
