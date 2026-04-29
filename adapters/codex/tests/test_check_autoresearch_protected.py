#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "check-autoresearch-protected.py"

spec = importlib.util.spec_from_file_location("check_autoresearch_protected", SCRIPT)
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(checker)


class ProtectedPathTests(unittest.TestCase):
    def test_exact_paths_do_not_match_substrings(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        self.assertEqual(protected.match_path("evaluate.py"), "evaluate.py")
        self.assertIsNone(protected.match_path("evaluate.py.bak"))
        self.assertIsNone(protected.match_path("src/evaluate.py"))

    def test_prefix_paths_match_only_children(self):
        protected = checker.ProtectedPaths(["evaluator_deps/"])
        self.assertEqual(protected.match_path("evaluator_deps/model.py"), "evaluator_deps/")
        self.assertIsNone(protected.match_path("evaluator_deps_old/model.py"))

    def test_apply_patch_hook_denies_protected_update(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "command": "*** Begin Patch\n*** Update File: evaluate.py\n@@\n-pass\n+pass\n*** End Patch"
            },
        }
        self.assertEqual(checker.hook_violations(payload, protected), {"evaluate.py"})

    def test_bash_read_only_reference_is_allowed(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "cat evaluate.py"},
        }
        self.assertEqual(checker.hook_violations(payload, protected), set())

    def test_bash_mutating_redirect_is_denied(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf x > evaluate.py"},
        }
        self.assertEqual(checker.hook_violations(payload, protected), {"evaluate.py"})

    def test_bash_mutating_redirect_normalizes_dot_slash(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf x > ./evaluate.py"},
        }
        self.assertEqual(checker.hook_violations(payload, protected), {"evaluate.py"})

    def test_write_payload_normalizes_file_path(self):
        protected = checker.ProtectedPaths(["evaluate.py"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "./evaluate.py", "content": "x"},
        }
        self.assertEqual(checker.hook_violations(payload, protected), {"evaluate.py"})

    def test_absolute_project_path_is_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protected = checker.ProtectedPaths(["evaluate.py"])
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(root / "evaluate.py"), "content": "x"},
            }
            self.assertEqual(checker.hook_violations(payload, protected, root), {"evaluate.py"})

    def test_prefix_dot_slash_is_matched(self):
        protected = checker.ProtectedPaths(["evaluator_deps/"])
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "./evaluator_deps/file.py", "content": "x"},
        }
        self.assertEqual(checker.hook_violations(payload, protected), {"evaluator_deps/"})


class CliTests(unittest.TestCase):
    def run_checker(self, cwd: Path, args: list[str], stdin: str = ""):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            input=stdin,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_pre_tool_use_outputs_codex_deny_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            protected = cwd / "protected.txt"
            protected.write_text("evaluate.py\n", encoding="utf-8")
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n*** Update File: evaluate.py\n@@\n-x\n+y\n*** End Patch"},
            }
            result = self.run_checker(cwd, ["--codex-pre-tool-use", "--protected-file", str(protected)], json.dumps(payload))
            self.assertEqual(result.returncode, 0, result.stderr)
            body = json.loads(result.stdout)
            self.assertNotIn("decision", body)
            output = body["hookSpecificOutput"]
            self.assertEqual(set(output), {"hookEventName", "permissionDecision", "permissionDecisionReason"})
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("evaluate.py", output["permissionDecisionReason"])

    def test_permission_request_outputs_codex_deny_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            protected = cwd / "protected.txt"
            protected.write_text("evaluate.py\n", encoding="utf-8")
            payload = {
                "hook_event_name": "PermissionRequest",
                "tool_name": "Bash",
                "tool_input": {"command": "python3 -c \"open('evaluate.py','w').write('x')\""},
            }
            result = self.run_checker(cwd, ["--codex-permission-request", "--protected-file", str(protected)], json.dumps(payload))
            self.assertEqual(result.returncode, 0, result.stderr)
            body = json.loads(result.stdout)
            self.assertNotIn("decision", body)
            output = body["hookSpecificOutput"]
            self.assertEqual(set(output), {"hookEventName", "decision"})
            self.assertEqual(set(output["decision"]), {"behavior", "message"})
            self.assertEqual(output["hookEventName"], "PermissionRequest")
            self.assertEqual(output["decision"]["behavior"], "deny")
            self.assertIn("evaluate.py", output["decision"]["message"])

    def test_pre_commit_detects_staged_exact_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            subprocess.run(["git", "init"], cwd=cwd, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
            protected = cwd / ".harness" / "autoresearch-protected.txt"
            protected.parent.mkdir()
            protected.write_text("evaluate.py\n", encoding="utf-8")
            (cwd / "evaluate.py").write_text("print('x')\n", encoding="utf-8")
            subprocess.run(["git", "add", "evaluate.py", ".harness/autoresearch-protected.txt"], cwd=cwd, check=True)
            result = self.run_checker(cwd, ["--pre-commit"])
            self.assertEqual(result.returncode, 1)
            self.assertIn("evaluate.py", result.stderr)

    def test_ci_fails_closed_when_base_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            subprocess.run(["git", "init"], cwd=cwd, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
            protected = cwd / ".harness" / "autoresearch-protected.txt"
            protected.parent.mkdir()
            protected.write_text("evaluate.py\n", encoding="utf-8")
            (cwd / "evaluate.py").write_text("print('x')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=cwd, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=cwd, check=True, stdout=subprocess.DEVNULL)
            result = self.run_checker(cwd, ["--ci", "--base-ref", "missing/base"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("could not determine CI comparison base", result.stderr)


if __name__ == "__main__":
    unittest.main()
