#!/usr/bin/env python3
"""Smoke-test the generated local Codex plugin bundle.

This does not claim that Codex has activated the plugin in a running session.
It verifies the repo-local plugin artifact that a Codex install flow would
consume: manifest, skills, bootstrap assets, protection assets, and the
documented degraded direct-copy fallback warning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PLUGIN_ROOT = ROOT / "plugins" / "ai-agent-meta-harness"

EXPECTED_SKILLS = (
    "autoresearch",
    "harness-engineer",
    "init-codex-harness",
    "multi-review",
)

EXPECTED_ASSETS = (
    "README.md",
    "plugin-scope.md",
    "templates/AGENTS.md.template",
    "templates/autoresearch-protected.txt",
    "templates/hooks/agents-autoresearch-protection.md",
    "templates/hooks/codex-hooks.json.template",
    "templates/hooks/github-actions-autoresearch-protected.yml",
    "templates/hooks/pre-commit-autoresearch-protected.sh",
    "scripts/check-autoresearch-protected.py",
    "scripts/smoke-autoresearch-hooks.py",
    "scripts/smoke-local-plugin.py",
)

DEGRADED_FALLBACK_PHRASES = (
    "degraded direct-copy fallback",
    "does not install Codex hooks",
    "Do not treat it as the full autoresearch safety path.",
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_manifest(plugin_root: Path) -> tuple[dict[str, object] | None, list[str]]:
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"MISSING MANIFEST: {rel(manifest_path)}"]
    except json.JSONDecodeError as exc:
        return None, [f"INVALID MANIFEST JSON: {rel(manifest_path)}: {exc}"]
    except OSError as exc:
        return None, [f"UNREADABLE MANIFEST: {rel(manifest_path)}: {exc}"]
    if not isinstance(manifest, dict):
        return None, [f"INVALID MANIFEST: {rel(manifest_path)} must contain a JSON object"]
    return manifest, []


def parse_skill_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def validate_manifest(plugin_root: Path, manifest: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if manifest.get("name") != "ai-agent-meta-harness":
        errors.append("plugin.json name must be ai-agent-meta-harness")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin.json skills must point to ./skills/")
    if "hooks" in manifest:
        errors.append("plugin.json must not advertise runtime hooks until activation coverage is smoke-tested")
    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        errors.append(f"MISSING SKILLS DIR: {rel(skills_dir)}")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json interface must be an object")
    elif not interface.get("displayName"):
        errors.append("plugin.json interface.displayName is required")
    return errors


def validate_skills(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    for skill in EXPECTED_SKILLS:
        skill_md = plugin_root / "skills" / skill / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"MISSING SKILL: {rel(skill_md)}")
            continue
        try:
            declared_name = parse_skill_name(skill_md)
        except OSError as exc:
            errors.append(f"UNREADABLE SKILL: {rel(skill_md)}: {exc}")
            continue
        if declared_name != skill:
            errors.append(f"SKILL NAME MISMATCH: {rel(skill_md)} declares {declared_name!r}, expected {skill!r}")
    return errors


def validate_assets(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    for asset in EXPECTED_ASSETS:
        path = plugin_root / asset
        if not path.is_file():
            errors.append(f"MISSING ASSET: {rel(path)}")
            continue
        try:
            if not path.read_bytes().strip():
                errors.append(f"EMPTY ASSET: {rel(path)}")
        except OSError as exc:
            errors.append(f"UNREADABLE ASSET: {rel(path)}: {exc}")
    return errors


def validate_degraded_fallback_warning(plugin_root: Path) -> list[str]:
    readme = plugin_root / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"UNREADABLE README: {rel(readme)}: {exc}"]
    return [
        f"README must document degraded fallback warning phrase: {phrase}"
        for phrase in DEGRADED_FALLBACK_PHRASES
        if phrase not in text
    ]


def validate_plugin(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    if not plugin_root.is_dir():
        return [f"MISSING PLUGIN ROOT: {rel(plugin_root)}"]

    manifest, manifest_errors = load_manifest(plugin_root)
    errors.extend(manifest_errors)
    if manifest is not None:
        errors.extend(validate_manifest(plugin_root, manifest))
    errors.extend(validate_skills(plugin_root))
    errors.extend(validate_assets(plugin_root))
    errors.extend(validate_degraded_fallback_warning(plugin_root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=DEFAULT_PLUGIN_ROOT,
        help="generated Codex plugin root to smoke-test",
    )
    args = parser.parse_args(argv)

    errors = validate_plugin(args.plugin_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Local Codex plugin smoke test passed: {rel(args.plugin_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
