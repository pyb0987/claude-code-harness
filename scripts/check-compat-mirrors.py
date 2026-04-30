#!/usr/bin/env python3
"""Check temporary compatibility mirrors against canonical files.

The repository keeps old Claude-facing paths working for one transition period.
Those mirrors are allowed to add a short HTML comment banner and, for docs/*,
installed-Claude wording in the opening paragraph. Everything else should stay
in sync with its canonical source.

This check validates the Git index, not the working tree, so pre-commit reports
what will actually be committed.
"""

from __future__ import annotations

from pathlib import Path
import difflib
from collections.abc import Callable
import sys

ROOT = Path(__file__).resolve().parents[1]

MIRRORS = [
    ("core/methodology.md", "docs/methodology.md"),
    ("core/reference.md", "docs/reference.md"),
    ("adapters/claude/commands/init-harness.md", "commands/init-harness.md"),
    ("adapters/claude/skills/autoresearch/SKILL.md", "skills/autoresearch/SKILL.md"),
    ("adapters/claude/skills/harness-engineer/SKILL.md", "skills/harness-engineer/SKILL.md"),
    ("adapters/claude/skills/multi-review/SKILL.md", "skills/multi-review/SKILL.md"),
    ("adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template", "adapters/codex/templates/AGENTS.md.template"),
]

BANNER_PREFIX = "<!-- Compatibility mirror of `"


def strip_banner(text: str) -> str:
    marker = "-->\n\n"
    if text.startswith(BANNER_PREFIX):
        end = text.find(marker)
        if end != -1:
            return text[end + len(marker):]
    # Commands and skills must keep YAML frontmatter first, so their mirror
    # banner appears immediately after the closing frontmatter delimiter.
    needle = "\n\n" + BANNER_PREFIX
    start = text.find(needle)
    if start != -1:
        end = text.find(marker, start)
        if end != -1:
            return text[:start] + "\n\n" + text[end + len(marker):]
    return text


def normalize_pair(canonical_path: str, mirror_path: str, canonical: str, mirror: str) -> tuple[str, str]:
    mirror = strip_banner(mirror)
    if canonical_path == "core/methodology.md":
        canonical = canonical.replace(
            "Runtime-neutral core principles. For detailed reference, see core/reference.md.",
            "Runtime-neutral core principles. For detailed reference in an installed Claude setup, see `~/.claude/docs/harness-reference.md`. Repository source: `core/reference.md`.",
        )
    elif canonical_path == "core/reference.md":
        canonical = canonical.replace(
            "Not auto-loaded every session. Core principles are in core/methodology.md.",
            "Not auto-loaded every session. In an installed Claude setup, core principles are in `~/.claude/rules/common/harness-methodology.md`. Repository source: `core/methodology.md`.",
        )
    return canonical, mirror


def indexed_files() -> set[str]:
    paths = sorted({path for pair in MIRRORS for path in pair})
    result = subprocess_run(["git", "ls-files", "--", *paths])
    return {line.strip() for line in result.splitlines() if line.strip()}


def read_index_text(path: str) -> str:
    return subprocess_run(["git", "show", f":{path}"])


def subprocess_run(args: list[str]) -> str:
    import subprocess

    result = subprocess.run(
        args,
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
    return result.stdout


def validate_mirrors(
    *,
    mirrors: list[tuple[str, str]] = MIRRORS,
    indexed: set[str] | None = None,
    read_text: Callable[[str], str] = read_index_text,
) -> list[str]:
    if indexed is None:
        indexed = indexed_files()
    errors: list[str] = []
    for canonical_path, mirror_path in mirrors:
        if canonical_path not in indexed or mirror_path not in indexed:
            errors.append(f"MISSING: {canonical_path} or {mirror_path}")
            continue
        try:
            canonical = read_text(canonical_path)
            mirror = read_text(mirror_path)
        except RuntimeError as exc:
            errors.append(f"UNREADABLE: {canonical_path} or {mirror_path}: {exc}")
            continue
        canonical_norm, mirror_norm = normalize_pair(canonical_path, mirror_path, canonical, mirror)
        if canonical_norm != mirror_norm:
            errors.append(f"OUT OF SYNC: {mirror_path} (canonical: {canonical_path})")
            diff = difflib.unified_diff(
                canonical_norm.splitlines(),
                mirror_norm.splitlines(),
                fromfile=canonical_path,
                tofile=mirror_path,
                lineterm="",
            )
            for line in list(diff)[:80]:
                errors.append(line)
    return errors


def main() -> int:
    try:
        errors = validate_mirrors()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Compatibility mirrors are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
