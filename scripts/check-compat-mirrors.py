#!/usr/bin/env python3
"""Check temporary compatibility mirrors against canonical files.

The repository keeps old Claude-facing paths working for one transition period.
Those mirrors are allowed to add a short HTML comment banner and, for docs/*,
installed-Claude wording in the opening paragraph. Everything else should stay
in sync with its canonical source.
"""

from pathlib import Path
import difflib
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


def main() -> int:
    failed = False
    for canonical_path, mirror_path in MIRRORS:
        canonical_file = ROOT / canonical_path
        mirror_file = ROOT / mirror_path
        if not canonical_file.exists() or not mirror_file.exists():
            print(f"MISSING: {canonical_path} or {mirror_path}", file=sys.stderr)
            failed = True
            continue
        canonical = canonical_file.read_text(encoding="utf-8")
        mirror = mirror_file.read_text(encoding="utf-8")
        canonical_norm, mirror_norm = normalize_pair(canonical_path, mirror_path, canonical, mirror)
        if canonical_norm != mirror_norm:
            failed = True
            print(f"OUT OF SYNC: {mirror_path} (canonical: {canonical_path})", file=sys.stderr)
            diff = difflib.unified_diff(
                canonical_norm.splitlines(),
                mirror_norm.splitlines(),
                fromfile=canonical_path,
                tofile=mirror_path,
                lineterm="",
            )
            for line in list(diff)[:80]:
                print(line, file=sys.stderr)
    if failed:
        return 1
    print("Compatibility mirrors are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
