from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from deepseek_runtime.runtime import WorkspaceTools
from deepseek_runtime.security import SandboxViolation, WorkspaceSandbox
from deepseek_runtime.workspace import WorkspaceResolver, WorkspaceViolation


class WorkspaceSecurityTests(unittest.TestCase):
    def _symlink(self, target: Path, link: Path, *, directory: bool = False) -> None:
        try:
            os.symlink(target, link, target_is_directory=directory)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")

    def test_traversal_and_absolute_external_paths_are_rejected_repeatedly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside-secret", encoding="utf-8")
            resolver = WorkspaceResolver(workspace)
            sandbox = WorkspaceSandbox(workspace)

            for _ in range(20):
                with self.assertRaises(WorkspaceViolation):
                    resolver.resolve("../outside.txt", must_exist=True)
                with self.assertRaises(WorkspaceViolation):
                    resolver.resolve(outside, must_exist=True)
                with self.assertRaises(SandboxViolation):
                    sandbox.resolve("../outside.txt")

    def test_internal_regular_file_is_read_and_searched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "src"
            source.mkdir()
            target = source / "main.py"
            target.write_text("needle = 'inside'\n", encoding="utf-8")
            tools = WorkspaceTools(workspace)

            read_result = tools.read_file({"input": "src/main.py"})
            self.assertEqual(read_result["status"], "ok")
            self.assertEqual(read_result["content"], "needle = 'inside'\n")
            self.assertEqual(read_result["path"], "src/main.py")

            search_result = tools.search({"input": "needle"})
            self.assertEqual(search_result["status"], "ok")
            self.assertTrue(
                any(
                    item["path"] == "src/main.py"
                    and item["line"] == 1
                    and "needle = 'inside'" in str(item["text"])
                    for item in search_result["matches"]
                )
            )

    def test_external_file_symlink_is_never_read_or_searched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside.txt"
            outside.write_text("external-secret-marker", encoding="utf-8")
            link = workspace / "linked.txt"
            self._symlink(outside, link)
            tools = WorkspaceTools(workspace)

            for _ in range(20):
                with self.assertRaises(WorkspaceViolation):
                    tools.read_file({"input": "linked.txt"})
                result = tools.search({"input": "external-secret-marker"})
                self.assertEqual(result["matches"], [])
                self.assertGreaterEqual(result["skipped"]["links"], 1)

    def test_external_directory_symlink_is_never_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text(
                "directory-secret-marker", encoding="utf-8"
            )
            link = workspace / "linked-dir"
            self._symlink(outside, link, directory=True)
            tools = WorkspaceTools(workspace)

            for _ in range(20):
                result = tools.search({"input": "directory-secret-marker"})
                self.assertEqual(result["matches"], [])
                self.assertGreaterEqual(result["skipped"]["links"], 1)
                with self.assertRaises(WorkspaceViolation):
                    tools._path("linked-dir/secret.txt")

    def test_nonexistent_leaf_below_symlink_parent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside"
            outside.mkdir()
            link = workspace / "linked-dir"
            self._symlink(outside, link, directory=True)
            resolver = WorkspaceResolver(workspace)

            with self.assertRaises(WorkspaceViolation):
                resolver.resolve("linked-dir/new.txt")

    def test_git_directory_and_links_are_excluded_from_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            git_dir = workspace / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("hidden-marker", encoding="utf-8")
            (workspace / "visible.txt").write_text("visible-marker", encoding="utf-8")
            tools = WorkspaceTools(workspace)

            hidden = tools.search({"input": "hidden-marker"})
            self.assertEqual(hidden["matches"], [])
            visible = tools.search({"input": "visible-marker"})
            self.assertTrue(any(item["path"] == "visible.txt" for item in visible["matches"]))

    def test_windows_reparse_attribute_is_classified_as_link(self) -> None:
        value = SimpleNamespace(st_file_attributes=1024)
        self.assertTrue(WorkspaceResolver.is_reparse_stat(value))  # type: ignore[arg-type]
        self.assertFalse(
            WorkspaceResolver.is_reparse_stat(
                SimpleNamespace(st_file_attributes=0)  # type: ignore[arg-type]
            )
        )

    @unittest.skipUnless(os.name == "nt", "Windows junction verification")
    def test_windows_junction_is_not_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text(
                "junction-secret-marker", encoding="utf-8"
            )
            junction = workspace / "junction"
            completed = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                self.skipTest(f"junction creation unavailable: {completed.stderr}")
            tools = WorkspaceTools(workspace)
            result = tools.search({"input": "junction-secret-marker"})
            self.assertEqual(result["matches"], [])
            self.assertGreaterEqual(result["skipped"]["links"], 1)
            with self.assertRaises(WorkspaceViolation):
                tools._path("junction/secret.txt")


if __name__ == "__main__":
    unittest.main()
