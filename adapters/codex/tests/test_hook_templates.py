#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
HOOKS = ROOT / "adapters" / "codex" / "templates" / "hooks"


class HookTemplateTests(unittest.TestCase):
    def test_codex_hooks_template_uses_shared_checker(self):
        template = json.loads((HOOKS / "codex-hooks.json.template").read_text(encoding="utf-8"))
        hooks = template["hooks"]
        self.assertEqual(set(hooks), {"PreToolUse", "PermissionRequest"})
        pre_tool = hooks["PreToolUse"][0]["hooks"][0]
        permission = hooks["PermissionRequest"][0]["hooks"][0]
        self.assertEqual(pre_tool["type"], "command")
        self.assertEqual(permission["type"], "command")
        self.assertIn("check-autoresearch-protected.py", pre_tool["command"])
        self.assertIn("--codex-pre-tool-use", pre_tool["command"])
        self.assertIn("check-autoresearch-protected.py", permission["command"])
        self.assertIn("--codex-permission-request", permission["command"])

    def test_codex_hooks_template_is_template_only(self):
        template_text = (HOOKS / "codex-hooks.json.template").read_text(encoding="utf-8")
        self.assertNotIn('"hooks": "./hooks', template_text)
        self.assertIn("PreToolUse", template_text)
        self.assertIn("PermissionRequest", template_text)

    def test_pre_commit_template_uses_pre_commit_mode(self):
        text = (HOOKS / "pre-commit-autoresearch-protected.sh").read_text(encoding="utf-8")
        self.assertIn("check-autoresearch-protected.py --pre-commit", text)
        self.assertIn("set -eu", text)

    def test_github_actions_template_uses_ci_mode_and_fetch_depth_zero(self):
        text = (HOOKS / "github-actions-autoresearch-protected.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("pull_request", text)
        self.assertNotIn("push:", text)
        self.assertIn("BASE_REF", text)
        self.assertIn("github.base_ref", text)
        self.assertIn("check-autoresearch-protected.py --ci", text)

    def test_agents_snippet_names_protection_command(self):
        text = (HOOKS / "agents-autoresearch-protection.md").read_text(encoding="utf-8")
        self.assertIn(".harness/autoresearch-protected.txt", text)
        self.assertIn("check-autoresearch-protected.py --pre-commit", text)
        self.assertIn("best_score.txt", text)

    def test_plugin_manifest_does_not_expose_runtime_hooks(self):
        manifest = json.loads((ROOT / "adapters" / "codex" / "plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["skills"], "./skills/")


if __name__ == "__main__":
    unittest.main()
