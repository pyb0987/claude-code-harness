#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
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

    def run_smoke_with_fake_checker(self, checker_source: str):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            scripts = cwd / "scripts"
            protected_dir = cwd / ".harness"
            scripts.mkdir()
            protected_dir.mkdir()
            checker = scripts / "fake-checker.py"
            checker.write_text(textwrap.dedent(checker_source), encoding="utf-8")
            protected = protected_dir / "autoresearch-protected.txt"
            protected.write_text("evaluate.py\n", encoding="utf-8")
            return subprocess.run(
                [
                    "python3",
                    str(ROOT / "adapters" / "codex" / "scripts" / "smoke-autoresearch-hooks.py"),
                    "--checker",
                    str(checker),
                    "--protected-file",
                    str(protected),
                ],
                cwd=cwd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_smoke_script_rejects_legacy_top_level_decision(self):
        result = self.run_smoke_with_fake_checker(
            'import json\nprint(json.dumps({"decision": "block"}))\n'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("legacy top-level decision", result.stderr)

    def test_smoke_script_rejects_invalid_json(self):
        result = self.run_smoke_with_fake_checker('print("not json")\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)

    def test_smoke_script_rejects_missing_output(self):
        result = self.run_smoke_with_fake_checker('')
        self.assertEqual(result.returncode, 1)
        self.assertIn("produced no blocking JSON", result.stderr)

    def test_smoke_script_rejects_malformed_hook_specific_keys(self):
        result = self.run_smoke_with_fake_checker(
            'import json\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny"}}))\n'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("hookSpecificOutput keys differ", result.stderr)

    def test_plugin_manifest_does_not_expose_runtime_hooks(self):
        manifest = json.loads((ROOT / "adapters" / "codex" / "plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["skills"], "./skills/")


if __name__ == "__main__":
    unittest.main()
