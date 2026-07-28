from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from deepseek_runtime import (
    ExecutionContext,
    FakeExecutionAdapter,
    RecoveryPolicy,
    RestrictedSubprocessAdapter,
    Risk,
    SubprocessRequest,
    ToolSpec,
)
from deepseek_runtime.contracts import ContractViolation, ErrorCode


PARAMETERS = {"type": "object", "additionalProperties": True}


def make_spec(
    handler: Any,
    *,
    timeout_seconds: float = 1.0,
    max_output_bytes: int = 1024,
) -> ToolSpec:
    return ToolSpec(
        "limits",
        "Execution limit test tool.",
        PARAMETERS,
        handler,
        risk=Risk.SHELL_SAFE,
        side_effect=True,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


class ExecutionAdapterLimitTests(unittest.TestCase):
    def test_fake_capabilities_do_not_claim_subprocess_controls(self) -> None:
        capabilities = FakeExecutionAdapter.capabilities
        self.assertFalse(capabilities.timeout_enforced)
        self.assertFalse(capabilities.byte_output_limit)
        self.assertFalse(capabilities.process_tree_cleanup)
        self.assertFalse(capabilities.minimal_environment)
        self.assertFalse(capabilities.kernel_isolation)

    def test_explicit_loader_injection_environment_is_removed(self) -> None:
        code = (
            "import json,os;"
            "print(json.dumps({'pythonpath':os.getenv('PYTHONPATH'),"
            "'preload':os.getenv('LD_PRELOAD'),"
            "'visible':os.getenv('VISIBLE_SETTING')}))"
        )
        request = SubprocessRequest(
            (sys.executable, "-c", code),
            env={
                "PYTHONPATH": "private-python-path",
                "LD_PRELOAD": "private-library",
                "VISIBLE_SETTING": "allowed",
            },
        )
        with tempfile.TemporaryDirectory() as root:
            outcome = RestrictedSubprocessAdapter().execute(
                make_spec(lambda arguments: request),
                {},
                ExecutionContext(Path(root)),
            )

        payload = json.loads(outcome.value["stdout"])
        self.assertIsNone(payload["pythonpath"])
        self.assertIsNone(payload["preload"])
        self.assertEqual(payload["visible"], "allowed")

    def test_host_loader_injection_environment_is_removed(self) -> None:
        code = "import os;print(os.getenv('PYTHONPATH'))"
        request = SubprocessRequest((sys.executable, "-c", code))
        with (
            tempfile.TemporaryDirectory() as root,
            patch.dict(os.environ, {"PYTHONPATH": "host-private-path"}, clear=False),
        ):
            outcome = RestrictedSubprocessAdapter().execute(
                make_spec(lambda arguments: request),
                {},
                ExecutionContext(Path(root)),
            )

        self.assertEqual(outcome.value["stdout"].strip(), "None")

    def test_blocked_stdin_writer_does_not_bypass_timeout(self) -> None:
        request = SubprocessRequest(
            (sys.executable, "-c", "import time;time.sleep(5)"),
            stdin=b"x" * 2_000_000,
        )
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as captured:
                RestrictedSubprocessAdapter(poll_interval=0.01).execute(
                    make_spec(lambda arguments: request, timeout_seconds=0.1),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assertEqual(captured.exception.error.code, ErrorCode.TOOL_TIMEOUT)

    def test_combined_retained_output_never_exceeds_byte_limit(self) -> None:
        code = (
            "import sys;"
            "sys.stdout.buffer.write(b'a'*100);sys.stdout.flush();"
            "sys.stderr.buffer.write(b'b'*100);sys.stderr.flush()"
        )
        request = SubprocessRequest((sys.executable, "-c", code))
        with tempfile.TemporaryDirectory() as root:
            outcome = RestrictedSubprocessAdapter().execute(
                make_spec(lambda arguments: request, max_output_bytes=64),
                {},
                ExecutionContext(Path(root)),
            )

        retained = len(outcome.value["stdout"].encode("utf-8")) + len(
            outcome.value["stderr"].encode("utf-8")
        )
        self.assertLessEqual(retained, 64)
        self.assertTrue(outcome.truncated)
        self.assertGreater(outcome.output_bytes, 64)


if __name__ == "__main__":
    unittest.main()
