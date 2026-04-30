#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = ROOT / "plugins" / "ai-agent-meta-harness"
SMOKE = ROOT / "adapters" / "codex" / "scripts" / "smoke-local-plugin.py"


class LocalPluginSmokeTests(unittest.TestCase):
    def run_smoke(self, plugin_root: Path = PLUGIN_ROOT):
        return subprocess.run(
            ["python3", str(SMOKE), "--plugin-root", str(plugin_root)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def copy_plugin(self, tmp: str) -> Path:
        target = Path(tmp) / "ai-agent-meta-harness"
        shutil.copytree(PLUGIN_ROOT, target)
        return target

    def test_repo_plugin_bundle_passes(self):
        result = self.run_smoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Local Codex plugin smoke test passed", result.stdout)

    def test_rejects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            (plugin / ".codex-plugin" / "plugin.json").unlink()
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING MANIFEST", result.stderr)

    def test_rejects_invalid_manifest_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            (plugin / ".codex-plugin" / "plugin.json").write_text("{not json", encoding="utf-8")
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INVALID MANIFEST JSON", result.stderr)

    def test_rejects_wrong_skills_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            manifest_path = plugin / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skills"] = "./not-skills/"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("skills must point to ./skills/", result.stderr)

    def test_rejects_runtime_hooks_in_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            manifest_path = plugin / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["hooks"] = "./hooks/"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must not advertise runtime hooks", result.stderr)

    def test_rejects_missing_expected_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            shutil.rmtree(plugin / "skills" / "autoresearch")
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING SKILL", result.stderr)

    def test_rejects_missing_protection_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            (plugin / "scripts" / "check-autoresearch-protected.py").unlink()
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING ASSET", result.stderr)

    def test_rejects_missing_plugin_smoke_script_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            (plugin / "scripts" / "smoke-local-plugin.py").unlink()
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING ASSET", result.stderr)

    def test_rejects_missing_degraded_fallback_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.copy_plugin(tmp)
            readme = plugin / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(text.replace("does not install Codex hooks", "omits runtime setup"), encoding="utf-8")
            result = self.run_smoke(plugin)
        self.assertEqual(result.returncode, 1)
        self.assertIn("degraded fallback warning phrase", result.stderr)


if __name__ == "__main__":
    unittest.main()
