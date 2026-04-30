#!/usr/bin/env python3
"""Validate Claude adapter trace and hook path contracts.

The shared core may use runtime-neutral examples such as `traces/evolution/`.
Claude adapter files must resolve those examples to concrete Claude Code paths:
`.claude/traces/`, `.claude/hooks/`, and `.claude/settings.local.json`.
This is an index-oriented lexical documentation guardrail for pre-commit. It
does not prove Claude Code runtime hook activation, settings schema acceptance,
or generated project output.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

EXTRA_CHECKED_FILES = ("README.md",)

BARE_TRACE_RE = re.compile(r"(?:^|[^.A-Za-z0-9_/-])(traces/|failures/)")
BARE_SETTINGS_RE = re.compile(r"(?<!\.claude/)settings\.local\.json\b")
BARE_HOOKS_RE = re.compile(r"(?:^|[^.A-Za-z0-9_/-])(hooks/)")

README_CLAUDE_START = "## Claude Code Adapter"
README_CODEX_START = "## Codex Adapter"


def is_checked_path(path: str) -> bool:
    return path in EXTRA_CHECKED_FILES or (
        path.startswith("adapters/claude/") and path.endswith(".md")
    )


def indexed_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", "README.md", "adapters/claude"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def discover_checked_files(indexed: set[str] | None = None) -> list[str]:
    if indexed is None:
        indexed = indexed_files()
    return sorted(path for path in indexed if is_checked_path(path))


def lines_with_matches(
    lines: list[tuple[int, str]], pattern: re.Pattern[str]
) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for lineno, line in lines:
        checked = re.sub(r"\.claude/traces/[A-Za-z0-9_./{}*-]*", ".claude-traces", line)
        checked = re.sub(r"\.claude/hooks/[A-Za-z0-9_.-]*", ".claude-hooks", checked)
        if pattern.search(checked):
            matches.append((lineno, line.strip()))
    return matches


def scoped_lines(path: str, text: str) -> list[tuple[int, str]]:
    lines = list(enumerate(text.splitlines(), start=1))
    if path != "README.md":
        return lines
    start = next(
        (lineno for lineno, line in lines if line.strip() == README_CLAUDE_START),
        None,
    )
    end = next(
        (lineno for lineno, line in lines if line.strip() == README_CODEX_START),
        None,
    )
    if start is None or end is None or end <= start:
        return lines
    return [(lineno, line) for lineno, line in lines if start <= lineno < end]


def validate_text(path: str, text: str) -> list[str]:
    lines = scoped_lines(path, text)
    checks = (
        (BARE_TRACE_RE, "bare trace path; use .claude/traces/... in Claude adapter docs"),
        (BARE_SETTINGS_RE, "bare settings.local.json path; use .claude/settings.local.json"),
        (BARE_HOOKS_RE, "bare hooks path; use .claude/hooks/..."),
    )
    errors: list[str] = []
    for pattern, message in checks:
        for lineno, line in lines_with_matches(lines, pattern):
            if path == "README.md" and "│   ├── settings.local.json" in line:
                continue
            if path == "README.md" and ("│   ├── traces/" in line or "│   │   ├── failures/" in line or "│   ├── hooks/" in line):
                continue
            errors.append(f"{path}:{lineno}: {message}: {line}")
    return errors


def read_index_text(path: str) -> str:
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


def main() -> int:
    errors: list[str] = []
    try:
        paths = discover_checked_files()
    except RuntimeError as exc:
        errors.append(str(exc))
        paths = []
    for path in paths:
        try:
            text = read_index_text(path)
        except FileNotFoundError:
            errors.append(f"MISSING: {path}")
            continue
        except OSError as exc:
            errors.append(f"UNREADABLE: {path}: {exc}")
            continue
        errors.extend(validate_text(path, text))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Claude adapter lexical path docs are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
