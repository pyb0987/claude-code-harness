#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "check-codex-hook-schema-drift.py"


spec = importlib.util.spec_from_file_location("hook_schema_drift", SCRIPT)
assert spec and spec.loader
hook_schema_drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook_schema_drift)


class HookSchemaDriftTests(unittest.TestCase):
    def test_reference_file_passes_content_check(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--skip-staged-policy"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Codex hook schema drift check passed", result.stdout)

    def test_reference_text_requires_verified_metadata(self):
        text = (ROOT / hook_schema_drift.REFERENCE_PATH).read_text(encoding="utf-8")
        errors = hook_schema_drift.validate_reference_text(text.replace("Verified date: 2026-04-30", "Verified date: TODO"))
        self.assertTrue(any("Verified date" in error for error in errors))

    def test_reference_text_names_output_scope_limit(self):
        text = (ROOT / hook_schema_drift.REFERENCE_PATH).read_text(encoding="utf-8")
        self.assertEqual(hook_schema_drift.validate_reference_text(text), [])
        errors = hook_schema_drift.validate_reference_text(text.replace("does not prove hook event coverage", "does not prove coverage"))
        self.assertTrue(any("hook event coverage" in error for error in errors))

    def test_staged_reference_text_is_validated_when_reference_is_staged(self):
        original_reader = hook_schema_drift.read_staged_text
        try:
            hook_schema_drift.read_staged_text = lambda path: "Verified date: TODO\n"
            errors = hook_schema_drift.validate_reference_source(["adapters/codex/hook-schema.md"])
        finally:
            hook_schema_drift.read_staged_text = original_reader
        self.assertTrue(any("missing hook schema reference marker" in error for error in errors))

    def test_smoke_metadata_matches_schema_reference(self):
        errors = hook_schema_drift.validate_smoke_metadata(ROOT / hook_schema_drift.SMOKE_SCRIPT_PATH)
        self.assertEqual(errors, [])

    def test_staged_smoke_metadata_is_validated_when_smoke_script_is_staged(self):
        original_reader = hook_schema_drift.read_staged_text
        try:
            hook_schema_drift.read_staged_text = lambda path: 'HOOK_SCHEMA_REFERENCE = "adapters/codex/hook-schema.md"\n'
            errors = hook_schema_drift.validate_smoke_metadata_source([
                "adapters/codex/scripts/smoke-autoresearch-hooks.py",
            ])
        finally:
            hook_schema_drift.read_staged_text = original_reader
        self.assertTrue(any("HOOK_SCHEMA_VERIFIED_DATE" in error for error in errors))

    def test_staged_policy_requires_reference_for_hook_sensitive_changes(self):
        errors = hook_schema_drift.validate_staged_policy([
            "adapters/codex/scripts/smoke-autoresearch-hooks.py",
        ])
        self.assertEqual(len(errors), 1)
        self.assertIn("hook-sensitive staged changes", errors[0])

    def test_staged_policy_covers_hook_templates_and_instructions(self):
        for path in [
            "adapters/codex/templates/hooks/agents-autoresearch-protection.md",
            "adapters/codex/templates/hooks/codex-hooks.json.template",
            "adapters/codex/scripts/check-codex-hook-schema-drift.py",
        ]:
            with self.subTest(path=path):
                errors = hook_schema_drift.validate_staged_policy([path])
                self.assertEqual(len(errors), 1)
                self.assertIn(path, errors[0])

    def test_staged_policy_allows_reference_update(self):
        errors = hook_schema_drift.validate_staged_policy([
            "adapters/codex/scripts/smoke-autoresearch-hooks.py",
            "adapters/codex/hook-schema.md",
        ])
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
