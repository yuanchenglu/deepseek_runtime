from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepseek_runtime.contracts import ContractViolation, ErrorCode, RecoveryPolicy, ToolSpec
from deepseek_runtime.execution import (
    CancellationToken,
    ExecutionContext,
    ExecutionOutcome,
    FakeExecutionAdapter,
    IsolationLevel,
    NoIsolationLocalAdapter,
    RestrictedSubprocessAdapter,
    SubprocessRequest,
)


PARAMETERS = {"type": "object", "additionalProperties": True}


def make_spec(
    handler: object,
    *,
    name: str = "command_tool",
    timeout_seconds: float = 2.0,
    max_output_bytes: int = 100_000,
) -> ToolSpec:
    return ToolSpec(
        name,
        "Execution adapter test tool.",
        PARAMETERS,
        handler,  # type: ignore[arg-type]
        risk="shell-safe",
        side_effect=True,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


class ExecutionAdapterContractTests(unittest.TestCase):
    def test_tc_sec_009_capabilities_distinguish_all_adapter_levels(self) -> None:
        fake = FakeExecutionAdapter()
        local = NoIsolationLocalAdapter()
        restricted = RestrictedSubprocessAdapter()

        self.assertIs(fake.capabilities.isolation, IsolationLevel.FAKE)
        self.assertIs(local.capabilities.isolation, IsolationLevel.NONE)
        self.assertIs(
            restricted.capabilities.isolation,
            IsolationLevel.PROCESS_RESTRICTED,
        )
        self.assertFalse(fake.capabilities.kernel_isolation)
        self.assertFalse(local.capabilities.kernel_isolation)
        self.assertFalse(restricted.capabilities.kernel_isolation)
        self.assertFalse(local.capabilities.timeout_enforced)
        self.assertTrue(restricted.capabilities.timeout_enforced)
        self.assertTrue(restricted.capabilities.process_tree_cleanup)

    def test_fake_adapter_is_deterministic_and_does_not_call_handler(self) -> None:
        handler_calls = 0

        def handler(arguments: dict[str, object]) -> str:
            nonlocal handler_calls
            handler_calls += 1
            return "unexpected"

        adapter = FakeExecutionAdapter(({"ok": True},))
        with tempfile.TemporaryDirectory() as root:
            outcome = adapter.execute(
                make_spec(handler),
                {"secret": "private"},
                ExecutionContext(Path(root)),
            )

        self.assertEqual(handler_calls, 0)
        self.assertEqual(outcome.value, {"ok": True})
        self.assertEqual(outcome.adapter, "fake")
        self.assertEqual(adapter.calls[0]["tool"], "command_tool")

    def test_no_isolation_adapter_calls_handler_and_labels_risk(self) -> None:
        adapter = NoIsolationLocalAdapter()
        with tempfile.TemporaryDirectory() as root:
            outcome = adapter.execute(
                make_spec(lambda arguments: {"received": arguments["value"]}),
                {"value": 7},
                ExecutionContext(Path(root)),
            )

        self.assertEqual(outcome.value, {"received": 7})
        self.assertEqual(outcome.capabilities.isolation.value, "none")
        self.assertFalse(outcome.capabilities.timeout_enforced)
        self.assertFalse(outcome.capabilities.minimal_environment)

    def test_cancelled_context_rejects_before_local_handler(self) -> None:
        calls = 0

        def handler(arguments: dict[str, object]) -> str:
            nonlocal calls
            calls += 1
            return "unexpected"

        token = CancellationToken()
        token.cancel()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as raised:
                NoIsolationLocalAdapter().execute(
                    make_spec(handler),
                    {},
                    ExecutionContext(Path(root), token),
                )

        self.assertEqual(raised.exception.error.code, ErrorCode.CANCELLED)
        self.assertEqual(calls, 0)


class RestrictedSubprocessAdapterTests(unittest.TestCase):
    def run_request(
        self,
        request: SubprocessRequest,
        *,
        timeout_seconds: float = 2.0,
        max_output_bytes: int = 100_000,
        cancellation: CancellationToken | None = None,
    ) -> tuple[ExecutionOutcome, Path]:
        workspace = Path(tempfile.mkdtemp())
        spec = make_spec(
            lambda arguments: request,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
        outcome = RestrictedSubprocessAdapter().execute(
            spec,
            {},
            ExecutionContext(workspace, cancellation),
        )
        return outcome, workspace

    def test_tc_sec_005_child_receives_minimal_environment_without_api_key(self) -> None:
        code = (
            "import json,os;"
            "print(json.dumps({'key':os.getenv('DEEPSEEK_API_KEY'),"
            "'visible':os.getenv('ADAPTER_VISIBLE')}))"
        )
        request = SubprocessRequest(
            (sys.executable, "-c", code),
            env={
                "ADAPTER_VISIBLE": "yes",
                "DEEPSEEK_API_KEY": "explicit-secret",
            },
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "host-secret"}, clear=False):
            outcome, _ = self.run_request(request)

        value = outcome.value
        self.assertIsInstance(value, dict)
        payload = json.loads(str(value["stdout"]))
        self.assertIsNone(payload["key"])
        self.assertEqual(payload["visible"], "yes")
        self.assertTrue(outcome.capabilities.minimal_environment)

    def test_explicit_cwd_is_contained_in_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as root_value:
            root = Path(root_value)
            child = root / "child"
            child.mkdir()
            request = SubprocessRequest(
                (sys.executable, "-c", "import os;print(os.getcwd())"),
                cwd="child",
            )
            spec = make_spec(lambda arguments: request)
            outcome = RestrictedSubprocessAdapter().execute(
                spec,
                {},
                ExecutionContext(root),
            )

        value = outcome.value
        self.assertEqual(Path(str(value["stdout"]).strip()), child.resolve())

    def test_external_cwd_is_rejected_before_process_start(self) -> None:
        request = SubprocessRequest(
            (sys.executable, "-c", "print('unexpected')"),
            cwd="../outside",
        )
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as raised:
                RestrictedSubprocessAdapter().execute(
                    make_spec(lambda arguments: request),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assertEqual(raised.exception.error.code, ErrorCode.SANDBOX_VIOLATION)

    def test_tc_tool_005_registered_timeout_returns_structured_error(self) -> None:
        request = SubprocessRequest(
            (sys.executable, "-c", "import time;time.sleep(5)"),
        )
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as raised:
                RestrictedSubprocessAdapter(poll_interval=0.01).execute(
                    make_spec(lambda arguments: request, timeout_seconds=0.1),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assertEqual(raised.exception.error.code, ErrorCode.TOOL_TIMEOUT)
        self.assertNotIn("time.sleep", json.dumps(raised.exception.error.to_dict()))

    def test_tc_tool_006_output_limit_is_measured_in_bytes(self) -> None:
        request = SubprocessRequest(
            (
                sys.executable,
                "-c",
                "import sys;sys.stdout.buffer.write(b'x'*4096);sys.stdout.flush()",
            ),
        )
        outcome, _ = self.run_request(request, max_output_bytes=128)

        value = outcome.value
        self.assertTrue(value["truncated"])
        self.assertTrue(outcome.truncated)
        self.assertGreater(outcome.output_bytes, 128)
        self.assertLessEqual(len(str(value["stdout"]).encode("utf-8")), 128)
        self.assertEqual(str(value["stderr"]), "")
        event = outcome.evidence(tool_name="command_tool")
        self.assertNotIn("stdout", event)
        self.assertNotIn("stderr", event)

    def test_tc_run_013_cancellation_reaches_adapter_and_cleans_process(self) -> None:
        request = SubprocessRequest(
            (sys.executable, "-c", "import time;time.sleep(5)"),
        )
        token = CancellationToken()
        timer = threading.Timer(0.1, token.cancel)
        timer.start()
        try:
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(ContractViolation) as raised:
                    RestrictedSubprocessAdapter(poll_interval=0.01).execute(
                        make_spec(lambda arguments: request, timeout_seconds=10.0),
                        {},
                        ExecutionContext(Path(root), token),
                    )
        finally:
            timer.cancel()

        self.assertEqual(raised.exception.error.code, ErrorCode.CANCELLED)

    def test_tc_sec_006_timeout_cleans_descendant_process_tree(self) -> None:
        with tempfile.TemporaryDirectory() as root_value:
            root = Path(root_value)
            marker = root / "grandchild-alive.txt"
            child_code = (
                "import pathlib,time;"
                "time.sleep(0.8);"
                f"pathlib.Path({str(marker)!r}).write_text('alive',encoding='utf-8')"
            )
            parent_code = (
                "import subprocess,sys,time;"
                f"subprocess.Popen([sys.executable,'-c',{child_code!r}]);"
                "time.sleep(5)"
            )
            request = SubprocessRequest((sys.executable, "-c", parent_code))
            with self.assertRaises(ContractViolation) as raised:
                RestrictedSubprocessAdapter(poll_interval=0.01).execute(
                    make_spec(lambda arguments: request, timeout_seconds=0.2),
                    {},
                    ExecutionContext(root),
                )
            self.assertEqual(raised.exception.error.code, ErrorCode.TOOL_TIMEOUT)
            time.sleep(1.0)
            self.assertFalse(marker.exists())

    def test_incompatible_handler_result_fails_without_executing_command(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ContractViolation) as raised:
                RestrictedSubprocessAdapter().execute(
                    make_spec(lambda arguments: {"command": "unsafe"}),
                    {},
                    ExecutionContext(Path(root)),
                )

        self.assertEqual(raised.exception.error.code, ErrorCode.TOOL_EXECUTION_FAILED)
        self.assertEqual(raised.exception.error.details["result_type"], "dict")

    def test_subprocess_request_rejects_string_command(self) -> None:
        with self.assertRaises(ValueError):
            SubprocessRequest("echo unsafe")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
