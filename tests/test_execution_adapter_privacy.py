from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import deepseek_runtime.execution as execution
from deepseek_runtime import (
    ExecutionContext,
    NoIsolationLocalAdapter,
    RecoveryPolicy,
    RestrictedSubprocessAdapter,
    Risk,
    ToolSpec,
)
from deepseek_runtime.contracts import ContractViolation, ErrorCode


PARAMETERS = {"type": "object", "additionalProperties": True}


def make_spec(handler: Any) -> ToolSpec:
    return ToolSpec(
        "private_failure",
        "Adapter privacy test tool.",
        PARAMETERS,
        handler,
        risk=Risk.READ,
        side_effect=False,
        timeout_seconds=1.0,
        max_output_bytes=1024,
        recovery_policy=RecoveryPolicy.PURE,
    )


class DirectAdapterPrivacyTests(unittest.TestCase):
    def assert_safe_failure(self, raised: ContractViolation, secret: str) -> None:
        self.assertEqual(raised.error.code, ErrorCode.TOOL_EXECUTION_FAILED)
        serialized = json.dumps(raised.error.to_dict(), ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertEqual(raised.error.cause_class, "RuntimeError")

    def test_no_isolation_handler_exception_is_structured_without_message(self) -> None:
        secret = "private-local-handler-secret"

        def handler(arguments: dict[str, Any]) -> str:
            raise RuntimeError(secret)

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as captured:
                NoIsolationLocalAdapter().execute(
                    make_spec(handler),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assert_safe_failure(captured.exception, secret)

    def test_restricted_builder_exception_is_structured_without_message(self) -> None:
        secret = "private-command-builder-secret"

        def builder(arguments: dict[str, Any]) -> str:
            raise RuntimeError(secret)

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as captured:
                RestrictedSubprocessAdapter().execute(
                    make_spec(builder),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assert_safe_failure(captured.exception, secret)

    def test_windows_taskkill_helper_receives_minimal_environment(self) -> None:
        class FakeProcess:
            pid = 123

            def poll(self) -> None:
                return None

            def wait(self, timeout: float | None = None) -> int:
                return 0

            def kill(self) -> None:
                raise AssertionError("fallback kill should not be needed")

            def terminate(self) -> None:
                raise AssertionError("terminate should not be used on Windows")

        with (
            patch.object(execution.os, "name", "nt"),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "host-secret"}, clear=False),
            patch.object(execution.subprocess, "run") as run,
        ):
            execution._terminate_process_tree(FakeProcess(), 0.1)  # type: ignore[arg-type]

        environment = run.call_args.kwargs["env"]
        self.assertNotIn("DEEPSEEK_API_KEY", environment)
        self.assertTrue(run.call_args.kwargs["check"] is False)


if __name__ == "__main__":
    unittest.main()
