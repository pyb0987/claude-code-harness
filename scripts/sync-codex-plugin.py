#!/usr/bin/env python3
"""Generate and verify the repo-local Codex plugin bundle.

The editable Codex adapter source lives under adapters/codex/. The plugin under
plugins/ai-agent-meta-harness/ is generated output so Codex can consume the
adapter as a local plugin without creating a second manually edited copy.
"""

from __future__ import annotations

import argparse
import difflib
import json
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "adapters" / "codex"
PLUGIN_ROOT = ROOT / "plugins" / "ai-agent-meta-harness"
IGNORED_FILE_NAMES = {".DS_Store"}
REQUIRED_SKILL_FILES = (
    "autoresearch/SKILL.md",
    "harness-engineer/SKILL.md",
    "init-codex-harness/SKILL.md",
    "multi-review/SKILL.md",
)
REQUIRED_TEMPLATE_FILES = (
    "AGENTS.md.template",
    "autoresearch-protected.txt",
    "hooks/codex-hooks.json.template",
    "hooks/pre-commit-autoresearch-protected.sh",
    "hooks/github-actions-autoresearch-protected.yml",
    "hooks/agents-autoresearch-protection.md",
)
REQUIRED_SCRIPT_FILES = (
    "check-autoresearch-protected.py",
    "smoke-autoresearch-hooks.py",
    "smoke-local-plugin.py",
)


@dataclass(frozen=True)
class Mapping:
    source: Path
    dest: Path


def _iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.name not in IGNORED_FILE_NAMES:
            yield path


def validate_source_tree() -> list[str]:
    errors: list[str] = []
    required = (
        ("skills", REQUIRED_SKILL_FILES),
        ("templates", REQUIRED_TEMPLATE_FILES),
        ("scripts", REQUIRED_SCRIPT_FILES),
    )
    for directory, files in required:
        base = SOURCE_ROOT / directory
        if not base.is_dir():
            errors.append(f"MISSING SOURCE DIR: {base.relative_to(ROOT)}")
            continue
        discovered = [path for path in _iter_files(base)]
        if not discovered:
            errors.append(f"EMPTY SOURCE DIR: {base.relative_to(ROOT)}")
        for file_name in files:
            path = base / file_name
            if not path.is_file():
                errors.append(f"MISSING REQUIRED SOURCE: {path.relative_to(ROOT)}")
    return errors


def build_mappings() -> list[Mapping]:
    mappings = [
        Mapping(
            SOURCE_ROOT / "plugin" / ".codex-plugin" / "plugin.json",
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        ),
        Mapping(SOURCE_ROOT / "README.md", PLUGIN_ROOT / "README.md"),
        Mapping(SOURCE_ROOT / "plugin-scope.md", PLUGIN_ROOT / "plugin-scope.md"),
    ]
    skills_root = SOURCE_ROOT / "skills"
    for source in _iter_files(skills_root):
        mappings.append(Mapping(source, PLUGIN_ROOT / "skills" / source.relative_to(skills_root)))

    templates_root = SOURCE_ROOT / "templates"
    for file_name in REQUIRED_TEMPLATE_FILES:
        mappings.append(Mapping(templates_root / file_name, PLUGIN_ROOT / "templates" / file_name))

    scripts_root = SOURCE_ROOT / "scripts"
    for file_name in REQUIRED_SCRIPT_FILES:
        mappings.append(Mapping(scripts_root / file_name, PLUGIN_ROOT / "scripts" / file_name))
    return mappings


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"MISSING MANIFEST: {path.relative_to(ROOT)}"]
    except OSError as exc:
        return [f"UNREADABLE MANIFEST: {path.relative_to(ROOT)}: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"INVALID JSON: {path.relative_to(ROOT)}: {exc}"]

    if manifest.get("name") != "ai-agent-meta-harness":
        errors.append("plugin.json name must be ai-agent-meta-harness")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin.json skills must point to ./skills/")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json interface must be an object")
    elif not interface.get("displayName"):
        errors.append("plugin.json interface.displayName is required")
    return errors


def render_diff(source_path: Path, dest_path: Path, source: bytes, dest: bytes) -> list[str]:
    try:
        source_text = source.decode("utf-8")
        dest_text = dest.decode("utf-8")
    except UnicodeDecodeError:
        return ["Binary files differ"]
    return list(
        difflib.unified_diff(
            source_text.splitlines(),
            dest_text.splitlines(),
            fromfile=str(source_path.relative_to(ROOT)),
            tofile=str(dest_path.relative_to(ROOT)),
            lineterm="",
        )
    )


def find_extra_files(expected: set[Path]) -> list[Path]:
    if not PLUGIN_ROOT.exists():
        return []
    return [path for path in _iter_files(PLUGIN_ROOT) if path not in expected]


def write_files(mappings: list[Mapping]) -> int:
    source_errors = validate_source_tree()
    if source_errors:
        for error in source_errors:
            print(error, file=sys.stderr)
        return 1

    missing_sources = [m.source for m in mappings if not m.source.exists()]
    if missing_sources:
        for path in missing_sources:
            print(f"MISSING SOURCE: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    manifest_errors = validate_manifest(SOURCE_ROOT / "plugin" / ".codex-plugin" / "plugin.json")
    if manifest_errors:
        for error in manifest_errors:
            print(error, file=sys.stderr)
        return 1

    for mapping in mappings:
        mapping.dest.parent.mkdir(parents=True, exist_ok=True)
        mapping.dest.write_bytes(mapping.source.read_bytes())

    extra = find_extra_files({m.dest for m in mappings})
    if extra:
        print("Generated plugin contains extra files not owned by the sync map:", file=sys.stderr)
        for path in extra:
            print(f"EXTRA: {path.relative_to(ROOT)}", file=sys.stderr)
        print("Remove or add these files to the sync map before --check can pass.", file=sys.stderr)
        return 1

    print(f"Synced {len(mappings)} files into {PLUGIN_ROOT.relative_to(ROOT)}.")
    return 0


def check_files(mappings: list[Mapping]) -> int:
    failed = False
    expected = {m.dest for m in mappings}

    for error in validate_source_tree():
        print(error, file=sys.stderr)
        failed = True

    for mapping in mappings:
        if not mapping.source.exists():
            print(f"MISSING SOURCE: {mapping.source.relative_to(ROOT)}", file=sys.stderr)
            failed = True
            continue
        if not mapping.dest.exists():
            print(f"MISSING GENERATED: {mapping.dest.relative_to(ROOT)}", file=sys.stderr)
            failed = True
            continue
        source = mapping.source.read_bytes()
        dest = mapping.dest.read_bytes()
        if source != dest:
            failed = True
            print(
                f"OUT OF SYNC: {mapping.dest.relative_to(ROOT)} "
                f"(canonical: {mapping.source.relative_to(ROOT)})",
                file=sys.stderr,
            )
            for line in render_diff(mapping.source, mapping.dest, source, dest)[:80]:
                print(line, file=sys.stderr)

    for path in find_extra_files(expected):
        print(f"EXTRA GENERATED: {path.relative_to(ROOT)}", file=sys.stderr)
        failed = True

    for error in validate_manifest(PLUGIN_ROOT / ".codex-plugin" / "plugin.json"):
        print(error, file=sys.stderr)
        failed = True

    if failed:
        return 1
    print("Codex plugin bundle is in sync.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="materialize generated plugin files")
    mode.add_argument("--check", action="store_true", help="verify generated plugin files without modifying them")
    args = parser.parse_args(argv)

    mappings = build_mappings()
    if args.write:
        return write_files(mappings)
    return check_files(mappings)


if __name__ == "__main__":
    raise SystemExit(main())
