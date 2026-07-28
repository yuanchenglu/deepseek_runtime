from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepseek_runtime import (
    WorkspaceResolver,
    WorkspaceSearchBudgets,
    WorkspaceTools,
    WorkspaceViolation,
)


class WorkspaceP1Tests(unittest.TestCase):
    def test_utf8_multibyte_boundary_is_valid_and_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "utf8.txt").write_bytes("A€B".encode("utf-8"))
            result = WorkspaceResolver(root).read_bounded("utf8.txt", max_bytes=3)

            self.assertEqual(result.status, "truncated")
            self.assertEqual(result.content, "A")
            self.assertEqual(result.bytes_read, 3)
            self.assertEqual(result.file_bytes, 5)
            self.assertTrue(result.truncated)
            result.content.encode("utf-8", errors="strict")

    def test_exact_byte_boundary_is_not_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = "甲乙".encode("utf-8")
            (root / "exact.txt").write_bytes(payload)
            result = WorkspaceResolver(root).read_bounded(
                "exact.txt", max_bytes=len(payload)
            )

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.content, "甲乙")
            self.assertEqual(result.bytes_read, len(payload))
            self.assertFalse(result.truncated)

    def test_invalid_utf8_and_nul_are_structured_binary_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "invalid.bin").write_bytes(b"text\xfftail")
            (root / "nul.bin").write_bytes(b"text\x00tail")
            resolver = WorkspaceResolver(root)

            invalid = resolver.read_bounded("invalid.bin", max_bytes=100)
            nul = resolver.read_bounded("nul.bin", max_bytes=100)

            for result in (invalid, nul):
                self.assertEqual(result.status, "binary")
                self.assertEqual(result.content, "")
                self.assertEqual(result.error_code, "WORKSPACE_BINARY_FILE")

    def test_permission_disappearance_and_io_error_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("payload", encoding="utf-8")
            resolver = WorkspaceResolver(root)

            with patch(
                "deepseek_runtime.workspace.os.open",
                side_effect=PermissionError("redacted"),
            ):
                denied = resolver.read_bounded("target.txt", max_bytes=100)
            with patch(
                "deepseek_runtime.workspace.os.open",
                side_effect=FileNotFoundError("redacted"),
            ):
                disappeared = resolver.read_bounded("target.txt", max_bytes=100)
            with patch(
                "deepseek_runtime.workspace.os.open",
                side_effect=OSError("redacted"),
            ):
                io_error = resolver.read_bounded("target.txt", max_bytes=100)

            self.assertEqual(denied.status, "permission-denied")
            self.assertEqual(denied.error_code, "WORKSPACE_PERMISSION_DENIED")
            self.assertEqual(disappeared.status, "disappeared")
            self.assertEqual(
                disappeared.error_code, "WORKSPACE_FILE_DISAPPEARED"
            )
            self.assertEqual(io_error.status, "io-error")
            self.assertEqual(io_error.error_code, "WORKSPACE_IO_ERROR")
            for result in (denied, disappeared, io_error):
                self.assertNotIn("redacted", str(result.to_dict()))

    def test_missing_contained_file_is_structured_but_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resolver = WorkspaceResolver(root)

            missing = resolver.read_bounded("missing.txt", max_bytes=100)
            self.assertEqual(missing.status, "disappeared")
            with self.assertRaises(WorkspaceViolation):
                resolver.read_bounded("../outside.txt", max_bytes=100)

    def test_search_stops_at_file_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(5):
                (root / f"{index}.txt").write_text(
                    f"needle {index}\n", encoding="utf-8"
                )
            result = WorkspaceResolver(root).search_text(
                "needle",
                budgets=WorkspaceSearchBudgets(
                    max_files=2,
                    max_bytes=10_000,
                    max_seconds=5.0,
                    max_matches=100,
                    max_file_bytes=1_000,
                ),
            )

            self.assertEqual(result.status, "budget-exhausted")
            self.assertEqual(result.stop_reason, "file-limit")
            self.assertEqual(result.files_scanned, 2)
            self.assertLessEqual(len(result.matches), 2)

    def test_search_stops_at_total_byte_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.txt").write_text("needle" * 10, encoding="utf-8")
            result = WorkspaceResolver(root).search_text(
                "needle",
                budgets=WorkspaceSearchBudgets(
                    max_files=10,
                    max_bytes=4,
                    max_seconds=5.0,
                    max_matches=100,
                    max_file_bytes=1_000,
                ),
            )

            self.assertEqual(result.status, "budget-exhausted")
            self.assertEqual(result.stop_reason, "byte-limit")
            self.assertEqual(result.bytes_scanned, 4)
            self.assertEqual(result.skipped["truncated-files"], 1)

    def test_search_stops_at_time_budget_with_fake_clock(self) -> None:
        class Clock:
            def __init__(self) -> None:
                self.value = 0.0

            def __call__(self) -> float:
                current = self.value
                self.value += 0.2
                return current

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.txt").write_text("needle", encoding="utf-8")
            result = WorkspaceResolver(root).search_text(
                "needle",
                budgets=WorkspaceSearchBudgets(
                    max_files=10,
                    max_bytes=1_000,
                    max_seconds=0.1,
                    max_matches=100,
                    max_file_bytes=1_000,
                ),
                clock=Clock(),
            )

            self.assertEqual(result.status, "budget-exhausted")
            self.assertEqual(result.stop_reason, "time-limit")
            self.assertEqual(result.files_scanned, 0)
            self.assertGreaterEqual(result.elapsed_ms, 100)

    def test_search_reports_binary_without_exposing_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "binary.dat").write_bytes(b"needle\xffredacted")
            result = WorkspaceResolver(root).search_text("needle")

            self.assertEqual(result.status, "ok")
            self.assertEqual(result.matches, [])
            self.assertEqual(result.skipped["binary"], 1)
            self.assertNotIn("redacted", str(result.to_dict()))

    def test_production_workspace_tools_return_structured_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.txt").write_text("needle line\n", encoding="utf-8")
            tools = WorkspaceTools(
                root,
                read_max_bytes=6,
                search_budgets=WorkspaceSearchBudgets(
                    max_files=10,
                    max_bytes=1_000,
                    max_seconds=5.0,
                    max_matches=10,
                    max_file_bytes=1_000,
                ),
            )

            read_result = tools.read_file({"input": "sample.txt"})
            search_result = tools.search({"input": "needle"})

            self.assertEqual(read_result["status"], "truncated")
            self.assertEqual(read_result["content"], "needle")
            self.assertTrue(search_result["matches"])
            self.assertIn("files_scanned", search_result)
            self.assertIn("bytes_scanned", search_result)

    def test_budget_validation_is_fail_closed(self) -> None:
        invalid_values = (
            {"max_files": 0},
            {"max_bytes": -1},
            {"max_seconds": float("nan")},
            {"max_matches": True},
            {"max_file_bytes": 0},
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    WorkspaceSearchBudgets(**values)


if __name__ == "__main__":
    unittest.main()
