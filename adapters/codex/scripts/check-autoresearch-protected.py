#!/usr/bin/env python3
"""Protect immutable autoresearch evaluator files.

Install this script into a project as scripts/check-autoresearch-protected.py and
list immutable paths in .harness/autoresearch-protected.txt. The same checker is
intended for Codex hooks, local pre-commit hooks, and CI checks.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any, Iterable

DEFAULT_PROTECTED_FILE = ".harness/autoresearch-protected.txt"
PATH_BOUNDARY = r"A-Za-z0-9_./-"


class CheckerError(Exception):
    """Configuration or environment problem that prevents a valid check."""


class ProtectedPaths:
    def __init__(self, entries: Iterable[str]) -> None:
        exact: set[str] = set()
        prefixes: set[str] = set()
        for entry in entries:
            normalized = normalize_path(entry)
            if normalized.endswith("/"):
                prefixes.add(normalized)
            else:
                exact.add(normalized)
        self.exact = exact
        self.prefixes = prefixes

    def match_path(self, path: str) -> str | None:
        normalized = normalize_path(path)
        if normalized in self.exact:
            return normalized
        for prefix in sorted(self.prefixes):
            if normalized.startswith(prefix):
                return prefix
        return None

    def find_in_text(self, text: str) -> set[str]:
        found: set[str] = set()
        for path in self.exact:
            pattern = rf"(?<![{PATH_BOUNDARY}]){re.escape(path)}(?![{PATH_BOUNDARY}])"
            if re.search(pattern, text):
                found.add(path)
        for prefix in self.prefixes:
            pattern = rf"(?<![{PATH_BOUNDARY}]){re.escape(prefix)}[^\s'\"`]*"
            if re.search(pattern, text):
                found.add(prefix)
        return found


def normalize_path(value: str) -> str:
    path = value.strip().replace("\\", "/")
    is_prefix = path.endswith("/")
    while path.startswith("./"):
        path = path[2:]
    path = re.sub(r"/+", "/", path)
    parts: list[str] = []
    for part in path.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            else:
                parts.append(part)
        else:
            parts.append(part)
    normalized = "/".join(parts)
    if is_prefix and normalized and not normalized.endswith("/"):
        return normalized + "/"
    return normalized


def normalize_candidate(value: str, root: Path) -> str:
    raw = value.strip().strip("'\"")
    path = Path(raw)
    if path.is_absolute():
        try:
            return normalize_path(str(path.resolve().relative_to(root.resolve())))
        except ValueError:
            return normalize_path(raw)
    return normalize_path(raw)


def project_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def load_protected(path: Path) -> ProtectedPaths:
    if not path.exists():
        raise CheckerError(f"missing protected path file: {path}")
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped)
    if not entries:
        raise CheckerError(f"protected path file has no active entries: {path}")
    return ProtectedPaths(entries)


def protected_file_path(args: argparse.Namespace, root: Path) -> Path:
    path = Path(args.protected_file)
    if path.is_absolute():
        return path
    return root / path


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def paths_from_apply_patch(command: str) -> set[str]:
    paths: set[str] = set()
    for line in command.splitlines():
        match = re.match(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", line)
        if match:
            paths.add(normalize_path(match.group(1)))
            continue
        match = re.match(r"^\*\*\* Move to: (.+)$", line)
        if match:
            paths.add(normalize_path(match.group(1)))
    return paths


def bash_looks_mutating(command: str) -> bool:
    mutating_patterns = (
        r"(^|[;&|\s])(rm|mv|cp|touch|install|truncate)\s+",
        r"(^|[;&|\s])(tee)\s+",
        r"(^|[;&|\s])sed\s+[^\n;]*\s-i(\s|$)",
        r"(^|[;&|\s])perl\s+[^\n;]*\s-pi",
        r">>?",
        r"open\([^)]*,\s*['\"][wax+][^'\"]*['\"]",
        r"write_text\(",
        r"write_bytes\(",
    )
    return any(re.search(pattern, command) for pattern in mutating_patterns)


def path_field_candidates(value: Any, root: Path) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if isinstance(item, str) and key_lower in {"file_path", "filepath", "path", "target_path"}:
                yield normalize_candidate(item, root)
            yield from path_field_candidates(item, root)
    elif isinstance(value, list):
        for item in value:
            yield from path_field_candidates(item, root)


def shell_path_candidates(command: str, root: Path) -> Iterable[str]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    for token in tokens:
        if not token or token.startswith("-"):
            continue
        if "/" in token or "." in token:
            yield normalize_candidate(token, root)


def match_candidates(candidates: Iterable[str], protected: ProtectedPaths) -> set[str]:
    found: set[str] = set()
    for candidate in candidates:
        if match := protected.match_path(candidate):
            found.add(match)
    return found


def hook_violations(payload: dict[str, Any], protected: ProtectedPaths, root: Path | None = None) -> set[str]:
    root = root or project_root()
    tool_name = str(payload.get("tool_name", "")).lower()
    tool_input = payload.get("tool_input", {})
    strings = list(iter_strings(tool_input))
    violations: set[str] = set()

    if "apply_patch" in tool_name:
        for value in strings:
            for path in paths_from_apply_patch(value):
                match = protected.match_path(normalize_candidate(path, root))
                if match:
                    violations.add(match)
        return violations

    try:
        serialized = json.dumps(tool_input, sort_keys=True)
    except TypeError:
        serialized = str(tool_input)

    if tool_name in {"edit", "write"}:
        violations.update(match_candidates(path_field_candidates(tool_input, root), protected))
        violations.update(protected.find_in_text(serialized))
        return violations

    if tool_name == "bash":
        for value in strings:
            if bash_looks_mutating(value):
                violations.update(match_candidates(shell_path_candidates(value, root), protected))
                violations.update(protected.find_in_text(value))
        return violations

    violations.update(match_candidates(path_field_candidates(tool_input, root), protected))
    violations.update(protected.find_in_text(serialized))
    return violations


def violation_message(paths: Iterable[str]) -> str:
    joined = ", ".join(sorted(paths))
    return f"Autoresearch evaluator boundary violation: protected path {joined} would be modified."


def print_pre_tool_deny(paths: Iterable[str]) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": violation_message(paths),
        }
    }))


def print_permission_deny(paths: Iterable[str]) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "deny",
                "message": violation_message(paths),
            },
        }
    }))


def run_hook_mode(mode: str, protected: ProtectedPaths) -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"invalid hook JSON: {exc}", file=sys.stderr)
        return 2
    violations = hook_violations(payload, protected, project_root())
    if not violations:
        return 0
    if mode == "pre-tool":
        print_pre_tool_deny(violations)
    else:
        print_permission_deny(violations)
    return 0


def git_paths(args: list[str]) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {normalize_path(line) for line in result.stdout.splitlines() if line.strip()}


def changed_paths_pre_commit() -> set[str]:
    paths = git_paths(["diff", "--name-only", "--cached", "--"])
    paths.update(git_paths(["diff", "--name-only", "--"]))
    return paths


def ci_base_ref(cli_base_ref: str | None) -> str:
    if cli_base_ref:
        return cli_base_ref
    env_base = os.environ.get("BASE_REF") or os.environ.get("GITHUB_BASE_REF")
    if env_base:
        if env_base.startswith("origin/") or env_base.startswith("refs/"):
            return env_base
        return f"origin/{env_base}"
    return "origin/main"


def merge_base(base_ref: str) -> str:
    try:
        result = subprocess.run(
            ["git", "merge-base", "HEAD", base_ref],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise CheckerError(f"could not determine CI comparison base from {base_ref!r}") from exc


def changed_paths_ci(base_ref: str | None) -> set[str]:
    base = merge_base(ci_base_ref(base_ref))
    return git_paths(["diff", "--name-only", f"{base}..HEAD", "--"])


def report_git_violations(paths: Iterable[str], mode: str) -> int:
    listed = sorted(paths)
    if not listed:
        return 0
    print(f"autoresearch protected-path violation in {mode} mode:", file=sys.stderr)
    for path in listed:
        print(f"- {path}", file=sys.stderr)
    return 1


def git_mode(mode: str, protected: ProtectedPaths, base_ref: str | None) -> int:
    try:
        changed = changed_paths_pre_commit() if mode == "pre-commit" else changed_paths_ci(base_ref)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise CheckerError(f"git check failed: {exc}") from exc
    violations = {match for path in changed if (match := protected.match_path(path))}
    return report_git_violations(violations, mode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--codex-pre-tool-use", action="store_true")
    modes.add_argument("--codex-permission-request", action="store_true")
    modes.add_argument("--pre-commit", action="store_true")
    modes.add_argument("--ci", action="store_true")
    parser.add_argument("--protected-file", default=DEFAULT_PROTECTED_FILE)
    parser.add_argument("--base-ref", default=None, help="CI comparison base, default: BASE_REF/GITHUB_BASE_REF/origin/main")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    try:
        protected = load_protected(protected_file_path(args, root))
        if args.codex_pre_tool_use:
            return run_hook_mode("pre-tool", protected)
        if args.codex_permission_request:
            return run_hook_mode("permission", protected)
        if args.pre_commit:
            return git_mode("pre-commit", protected, args.base_ref)
        return git_mode("ci", protected, args.base_ref)
    except CheckerError as exc:
        print(f"check-autoresearch-protected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
