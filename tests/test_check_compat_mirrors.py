#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-compat-mirrors.py"


spec = importlib.util.spec_from_file_location("check_compat_mirrors", SCRIPT)
assert spec and spec.loader
check_compat_mirrors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_compat_mirrors)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CompatMirrorUnitTests(unittest.TestCase):
    def test_validate_mirrors_detects_indexed_drift(self):
        mirrors = [("canonical.md", "mirror.md")]
        indexed = {"canonical.md", "mirror.md"}
        contents = {"canonical.md": "same\n", "mirror.md": "different\n"}

        errors = check_compat_mirrors.validate_mirrors(
            mirrors=mirrors,
            indexed=indexed,
            read_text=contents.__getitem__,
        )

        self.assertTrue(any("OUT OF SYNC" in error for error in errors))

    def test_validate_mirrors_detects_index_missing_canonical_or_mirror(self):
        mirrors = [("canonical.md", "mirror.md")]

        errors = check_compat_mirrors.validate_mirrors(
            mirrors=mirrors,
            indexed={"canonical.md"},
            read_text=lambda path: "same\n",
        )

        self.assertEqual(errors, ["MISSING: canonical.md or mirror.md"])

    def test_validate_mirrors_accepts_index_added_pair(self):
        mirrors = [("canonical.md", "mirror.md")]
        indexed = {"canonical.md", "mirror.md"}

        errors = check_compat_mirrors.validate_mirrors(
            mirrors=mirrors,
            indexed=indexed,
            read_text=lambda path: "same\n",
        )

        self.assertEqual(errors, [])


class CompatMirrorIndexIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "scripts").mkdir()
        shutil.copy2(SCRIPT, self.repo / "scripts" / "check-compat-mirrors.py")
        run(["git", "init"], self.repo)
        for canonical, mirror in check_compat_mirrors.MIRRORS:
            write(self.repo / canonical, "same\n")
            write(self.repo / mirror, "same\n")
        self.assertEqual(run(["git", "add", "-A"], self.repo).returncode, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return run(["python3", "scripts/check-compat-mirrors.py"], self.repo)

    def test_checker_reads_index_not_unstaged_working_tree(self):
        write(self.repo / "commands" / "init-harness.md", "unstaged drift\n")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Compatibility mirrors are in sync", result.stdout)

    def test_checker_fails_on_staged_modified_mirror(self):
        write(self.repo / "commands" / "init-harness.md", "staged drift\n")
        self.assertEqual(
            run(["git", "add", "commands/init-harness.md"], self.repo).returncode,
            0,
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OUT OF SYNC: commands/init-harness.md", result.stderr)

    def test_checker_fails_on_staged_modified_canonical(self):
        write(
            self.repo / "adapters" / "claude" / "commands" / "init-harness.md",
            "staged drift\n",
        )
        self.assertEqual(
            run(
                ["git", "add", "adapters/claude/commands/init-harness.md"],
                self.repo,
            ).returncode,
            0,
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OUT OF SYNC: commands/init-harness.md", result.stderr)

    def test_checker_fails_on_staged_deleted_required_mirror(self):
        self.assertEqual(
            run(["git", "rm", "-f", "commands/init-harness.md"], self.repo).returncode,
            0,
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "MISSING: adapters/claude/commands/init-harness.md or commands/init-harness.md",
            result.stderr,
        )

    def test_checker_fails_on_staged_deleted_required_canonical(self):
        self.assertEqual(
            run(
                ["git", "rm", "-f", "adapters/claude/commands/init-harness.md"],
                self.repo,
            ).returncode,
            0,
        )

        result = self.run_checker()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "MISSING: adapters/claude/commands/init-harness.md or commands/init-harness.md",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
