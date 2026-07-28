from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deepseek_runtime import (
    NoIsolationLocalAdapter,
    RestrictedSubprocessAdapter,
    Risk,
    WorkspaceSandbox,
)


class ExecutionBoundaryClaimTests(unittest.TestCase):
    def test_tc_sec_007_wrapped_network_commands_are_not_an_isolation_boundary(self) -> None:
        commands = (
            ("bash", "-c", "curl https://example.invalid"),
            ("python", "-c", "import socket"),
            ("env", "curl", "https://example.invalid"),
        )
        with tempfile.TemporaryDirectory() as root:
            sandbox = WorkspaceSandbox(Path(root))
            for command in commands:
                with self.subTest(command=command[0]):
                    self.assertIs(sandbox.classify_command(command), Risk.SHELL_SAFE)

        self.assertFalse(NoIsolationLocalAdapter.capabilities.kernel_isolation)
        self.assertFalse(RestrictedSubprocessAdapter.capabilities.kernel_isolation)
        self.assertEqual(
            RestrictedSubprocessAdapter.capabilities.isolation.value,
            "process-restricted",
        )


if __name__ == "__main__":
    unittest.main()
