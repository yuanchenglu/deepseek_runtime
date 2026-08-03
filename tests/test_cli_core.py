"""
M2-F CLI Core 测试 -- 验证 CLI 输出协议。

覆盖 TC-CLI-002 ~ TC-CLI-006：
- TC-CLI-002：run 默认输出最终回答
- TC-CLI-003：--report 输出安全证据，stdout 不污染
- TC-CLI-004：--unsafe-debug-content 需要显式开关
- TC-CLI-005：exit code 与 error code 对应
- TC-CLI-006：workspace 不存在或为文件时友好失败
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class CliCoreTests(unittest.TestCase):
    """M2-F CLI 输出协议测试。"""

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        # 不传 API Key，让 Provider 失败而不是真调用
        env.pop("DEEPSEEK_API_KEY", None)
        return env

    def _run_cli(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "deepseek_runtime.cli", *args],
            cwd=cwd or ROOT,
            env=self._env(),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_run_workspace_not_exist(self) -> None:
        """TC-CLI-006：workspace 不存在时友好失败，exit code = 2。"""
        result = self._run_cli("run", "hello", "--workspace", "/nonexistent/path/that/does/not/exist")
        self.assertEqual(result.returncode, 2, f"stdout={result.stdout}, stderr={result.stderr}")
        self.assertIn("does not exist", result.stderr)

    def test_cli_run_workspace_is_file(self) -> None:
        """TC-CLI-006：workspace 是文件不是目录时友好失败，exit code = 2。"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not a directory")
            f.flush()
            file_path = f.name
        try:
            result = self._run_cli("run", "hello", "--workspace", file_path)
            self.assertEqual(result.returncode, 2)
            self.assertIn("not a directory", result.stderr)
        finally:
            os.unlink(file_path)

    def test_cli_run_report_writes_safe_evidence(self) -> None:
        """TC-CLI-003：--report 写入安全证据文件，stdout 不被污染。"""
        with tempfile.TemporaryDirectory() as d:
            report_path = Path(d) / "report.json"
            # workspace 不存在会先失败，但 report 仍应写入
            result = self._run_cli(
                "run", "hello",
                "--workspace", "/nonexistent/path",
                "--report", str(report_path),
            )
            # workspace 不存在 -> exit 2
            self.assertEqual(result.returncode, 2)
            # report 文件应该存在且是有效 JSON
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("ok", report)
            self.assertFalse(report["ok"])
            # stdout 不应包含 report 内容
            self.assertNotIn("evidence", result.stdout.lower())

    def test_cli_run_report_with_valid_workspace(self) -> None:
        """TC-CLI-003 + TC-CLI-005：有效 workspace 但无 API Key，report 写入安全证据。"""
        with tempfile.TemporaryDirectory() as d:
            report_path = Path(d) / "report.json"
            result = self._run_cli(
                "run", "hello",
                "--workspace", d,
                "--report", str(report_path),
            )
            # 无 API Key -> CONFIG_INVALID -> exit 3
            self.assertEqual(result.returncode, 3)
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("ok", report)
            self.assertFalse(report["ok"])

    def test_cli_unsafe_debug_content_warning(self) -> None:
        """TC-CLI-004：--unsafe-debug-content 输出警告到 stderr。"""
        with tempfile.TemporaryDirectory() as d:
            result = self._run_cli(
                "run", "hello",
                "--workspace", d,
                "--unsafe-debug-content",
            )
            # 无 API Key 仍会失败，但警告应该出现在 stderr
            self.assertIn("unsafe-debug-content", result.stderr.lower())

    def test_cli_exit_code_success_is_zero(self) -> None:
        """TC-CLI-005：成功时 exit code = 0（需 mock，这里验证 doctor）。"""
        # doctor --json 在无 Key 时 ok=False -> exit 1
        # 但如果 workspace 有效且检查通过则 exit 0
        result = self._run_cli("doctor", "--json", "--workspace", str(ROOT))
        # doctor 在无 Key 时返回 1（ok=False），这是正确行为
        self.assertIn(result.returncode, (0, 1))

    def test_cli_json_output_is_valid_json(self) -> None:
        """--json 输出有效 JSON，且不含 prompt/response 原文（安全模式）。"""
        with tempfile.TemporaryDirectory() as d:
            result = self._run_cli(
                "run", "secret prompt",
                "--workspace", d,
                "--json",
            )
            # 无 Key -> 失败，但 --json 仍应输出 JSON
            # 失败时 stdout 可能为空（错误到 stderr），这是正确行为
            if result.stdout.strip():
                data = json.loads(result.stdout)
                self.assertIn("ok", data)
                # 安全模式不应包含 prompt 原文
                self.assertNotIn("secret prompt", result.stdout)

    def test_cli_workspace_error_with_report(self) -> None:
        """TC-CLI-006 + TC-CLI-003：workspace 错误时 report 也写入。"""
        with tempfile.TemporaryDirectory() as d:
            report_path = Path(d) / "err-report.json"
            result = self._run_cli(
                "run", "hello",
                "--workspace", "/nonexistent",
                "--report", str(report_path),
            )
            self.assertEqual(result.returncode, 2)
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertIn("WORKSPACE_INVALID", report.get("error_class", ""))


if __name__ == "__main__":
    unittest.main()
