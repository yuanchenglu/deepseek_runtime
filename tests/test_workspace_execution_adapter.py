from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from deepseek_runtime import (
    Decision,
    FakeExecutionAdapter,
    PermissionPolicy,
    PermissionRule,
    Risk,
    WorkspaceSandbox,
)
from deepseek_runtime.contracts import ContractViolation, ErrorCode
from deepseek_runtime.security import PermissionDenied


def allow_shell() -> PermissionPolicy:
    return PermissionPolicy(
        [PermissionRule(Risk.SHELL_SAFE, Decision.ALLOW, path_glob="*")]
    )


class WorkspaceSandboxAdapterTests(unittest.TestCase):
    def test_injected_adapter_is_the_only_command_execution_path(self) -> None:
        adapter = FakeExecutionAdapter(
            (
                {
                    "returncode": 0,
                    "stdout": "adapter-output",
                    "stderr": "",
                    "truncated": False,
                },
            )
        )
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(
                Path(root),
                policy=allow_shell(),
                execution_adapter=adapter,
            )
            result = sandbox.run(("not-a-real-executable", "private-argument"))

        self.assertEqual(result.stdout, "adapter-output")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(adapter.calls[0]["tool"], "workspace_command")
        self.assertEqual(adapter.calls[0]["arguments"], {})

    def test_policy_denial_prevents_adapter_execution(self) -> None:
        adapter = FakeExecutionAdapter(
            ({"returncode": 0, "stdout": "", "stderr": "", "truncated": False},)
        )
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(Path(root), execution_adapter=adapter)
            with self.assertRaises(PermissionDenied):
                sandbox.run((sys.executable, "-c", "print('unexpected')"))

        self.assertEqual(adapter.calls, [])

    def test_default_restricted_adapter_executes_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as root_value:
            root = Path(root_value)
            child = root / "child"
            child.mkdir()
            sandbox = WorkspaceSandbox(root, policy=allow_shell())
            result = sandbox.run(
                (sys.executable, "-c", "import os;print(os.getcwd())"),
                cwd="child",
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(Path(result.stdout.strip()), child.resolve())
        self.assertFalse(result.truncated)

    def test_default_restricted_adapter_enforces_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(Path(root), policy=allow_shell())
            with self.assertRaises(ContractViolation) as captured:
                sandbox.run(
                    (sys.executable, "-c", "import time;time.sleep(5)"),
                    timeout=0.1,
                )

        self.assertEqual(captured.exception.error.code, ErrorCode.TOOL_TIMEOUT)

    def test_adapter_result_shape_is_validated(self) -> None:
        adapter = FakeExecutionAdapter(({"returncode": "wrong"},))
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(
                Path(root),
                policy=allow_shell(),
                execution_adapter=adapter,
            )
            with self.assertRaises(ContractViolation) as captured:
                sandbox.run((sys.executable, "-c", "print('unused')"))

        self.assertEqual(captured.exception.error.code, ErrorCode.TOOL_RESULT_INVALID)

    def test_timeout_and_output_limits_validate_types(self) -> None:
        adapter = FakeExecutionAdapter(())
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(
                Path(root),
                policy=allow_shell(),
                execution_adapter=adapter,
            )
            for value in (0, -1, True, float("inf")):
                with self.subTest(timeout=value):
                    with self.assertRaises(ValueError):
                        sandbox.run((sys.executable, "-c", "pass"), timeout=value)  # type: ignore[arg-type]
            for value in (0, -1, True):
                with self.subTest(max_output=value):
                    with self.assertRaises(ValueError):
                        sandbox.run((sys.executable, "-c", "pass"), max_output=value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
