from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections.abc import Iterable
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from deepseek_runtime import (
    DeepSeekRuntime,
    ErrorCode,
    ProviderResult,
    RecoveryPolicy,
    Risk,
    ToolArgumentError,
    ToolRegistry,
    ToolSpec,
)
from deepseek_runtime.cli import _run


PARAMETERS = {
    "type": "object",
    "properties": {"value": {"type": "integer"}},
    "required": ["value"],
    "additionalProperties": False,
}


class SequencedClient:
    def __init__(self, messages: Iterable[dict[str, Any]]) -> None:
        self.messages = list(messages)
        self.payloads: list[dict[str, Any]] = []

    def chat(self, payload: dict[str, Any]) -> ProviderResult:
        self.payloads.append(payload)
        if not self.messages:
            raise AssertionError("fake provider received an unexpected request")
        message = self.messages.pop(0)
        return ProviderResult(
            status=200,
            elapsed_ms=0,
            body={"choices": [{"message": message}], "usage": {}},
            request_fingerprint="test-fingerprint",
            request_payload=payload,
        )


def tool_call(
    name: str = "sample",
    arguments: Any = '{"value":1}',
    *,
    call_id: Any = "call-1",
    function: Any | None = None,
) -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": function if function is not None else {"name": name, "arguments": arguments},
    }


def assistant_tool_message(call: Any) -> dict[str, Any]:
    return {"role": "assistant", "content": None, "tool_calls": [call]}


def final_message() -> dict[str, Any]:
    return {"role": "assistant", "content": "done"}


def tool_output(result: Any) -> str:
    return next(message["content"] for message in result.messages if message.get("role") == "tool")


def tool_error_code(result: Any) -> str:
    return str(json.loads(tool_output(result))["error"]["code"])


class ToolRegistryContractTests(unittest.TestCase):
    def test_tc_tool_001_registers_complete_spec(self) -> None:
        handler = lambda arguments: arguments["value"]
        spec = ToolSpec(
            "sample",
            "Return one integer.",
            PARAMETERS,
            handler,
            risk=Risk.READ,
            side_effect=False,
            timeout_seconds=2.5,
            max_output_bytes=512,
            recovery_policy=RecoveryPolicy.PURE,
        )
        registry = ToolRegistry((spec,))

        self.assertEqual(registry.names, ("sample",))
        self.assertIs(registry["sample"].handler, handler)
        self.assertEqual(registry["sample"].risk, "read")
        self.assertFalse(registry["sample"].side_effect)
        self.assertEqual(registry["sample"].timeout_seconds, 2.5)
        self.assertEqual(registry["sample"].max_output_bytes, 512)
        self.assertIs(registry["sample"].recovery_policy, RecoveryPolicy.PURE)
        self.assertFalse(callable(spec))
        self.assertEqual(
            registry.provider_definitions(),
            [
                {
                    "type": "function",
                    "function": {
                        "name": "sample",
                        "description": "Return one integer.",
                        "parameters": PARAMETERS,
                    },
                }
            ],
        )

    def test_tc_tool_002_rejects_duplicate_names(self) -> None:
        first = ToolSpec("sample", "First.", PARAMETERS, lambda arguments: arguments)
        second = ToolSpec("sample", "Second.", PARAMETERS, lambda arguments: arguments)
        registry = ToolRegistry((first,))

        with self.assertRaisesRegex(ValueError, "duplicate tool name"):
            registry.register(second)

    def test_tc_tool_003_validates_schema_before_handler(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> Any:
            nonlocal calls
            calls += 1
            return arguments

        registry = ToolRegistry((ToolSpec("sample", "Validate.", PARAMETERS, handler),))
        invalid_values = ({}, {"value": 1, "extra": True}, {"value": "wrong"})

        for invalid in invalid_values:
            with self.subTest(arguments=invalid):
                with self.assertRaises(ToolArgumentError) as raised:
                    registry.execute("sample", invalid)
                self.assertIs(raised.exception.error.code, ErrorCode.TOOL_ARGUMENT_INVALID)
        self.assertEqual(calls, 0)

    def test_tc_tool_004_rejects_incomplete_side_effect_contracts(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-read risk"):
            ToolSpec(
                "write_default_risk",
                "Write.",
                PARAMETERS,
                lambda arguments: arguments,
                side_effect=True,
                recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
            )

        with self.assertRaisesRegex(ValueError, "cannot use PURE"):
            ToolSpec(
                "write_default_recovery",
                "Write.",
                PARAMETERS,
                lambda arguments: arguments,
                risk="write",
                side_effect=True,
            )

        with self.assertRaisesRegex(ValueError, "side_effect must be a boolean"):
            ToolSpec(
                "invalid_side_effect_type",
                "Write.",
                PARAMETERS,
                lambda arguments: arguments,
                risk="write",
                side_effect=1,
                recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
            )

        with self.assertRaisesRegex(ValueError, "must be a RecoveryPolicy"):
            ToolSpec(
                "invalid_recovery_type",
                "Write.",
                PARAMETERS,
                lambda arguments: arguments,
                risk="write",
                side_effect=True,
                recovery_policy="NON_IDEMPOTENT",
            )

        with self.assertRaisesRegex(ValueError, "handler must be callable"):
            ToolSpec("invalid_handler", "Invalid.", PARAMETERS, None)

        with self.assertRaisesRegex(ValueError, "timeout_seconds must be finite and positive"):
            ToolSpec(
                "invalid_timeout",
                "Invalid.",
                PARAMETERS,
                lambda arguments: arguments,
                timeout_seconds=True,
            )

        with self.assertRaisesRegex(ValueError, "max_output_bytes must be a positive integer"):
            ToolSpec(
                "invalid_output_limit",
                "Invalid.",
                PARAMETERS,
                lambda arguments: arguments,
                max_output_bytes=True,
            )


class RuntimeToolBoundaryTests(unittest.TestCase):
    def run_tool_call(self, registry: ToolRegistry, call: Any) -> tuple[Any, SequencedClient]:
        client = SequencedClient((assistant_tool_message(call), final_message()))
        with tempfile.TemporaryDirectory() as workspace:
            result = DeepSeekRuntime(client).run(
                [{"role": "user", "content": "test"}],
                workspace=Path(workspace),
                tools=registry,
            )
        return result, client

    def test_tc_run_004_rejects_raw_handler_mapping_before_provider(self) -> None:
        client = SequencedClient((final_message(),))
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaisesRegex(TypeError, "ToolRegistry"):
                DeepSeekRuntime(client).run(
                    [{"role": "user", "content": "test"}],
                    workspace=Path(workspace),
                    tools={"unsafe": lambda arguments: arguments},
                )
        self.assertEqual(client.payloads, [])

    def test_tc_run_009_normalizes_supported_results(self) -> None:
        cases = (
            ({"b": 2, "a": 1}, '{"a":1,"b":2}'),
            ([2, 1], "[2,1]"),
            (b"utf-8", "utf-8"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                registry = ToolRegistry(
                    (ToolSpec("sample", "Return value.", PARAMETERS, lambda arguments, value=value: value),)
                )
                result, _ = self.run_tool_call(registry, tool_call())
                self.assertTrue(result.ok)
                self.assertEqual(tool_output(result), expected)

    def test_tc_run_009_rejects_invalid_result(self) -> None:
        invalid_values = (object(), {1: "one", "two": 2})
        for value in invalid_values:
            with self.subTest(value_type=type(value).__name__):
                registry = ToolRegistry(
                    (ToolSpec("sample", "Invalid.", PARAMETERS, lambda arguments, value=value: value),)
                )
                result, _ = self.run_tool_call(registry, tool_call())

                self.assertTrue(result.ok)
                self.assertEqual(tool_error_code(result), ErrorCode.TOOL_RESULT_INVALID.value)

    def test_non_utf8_bytes_are_structured_result_error(self) -> None:
        registry = ToolRegistry((ToolSpec("sample", "Bytes.", PARAMETERS, lambda arguments: b"\xff"),))
        result, _ = self.run_tool_call(registry, tool_call())

        self.assertTrue(result.ok)
        self.assertEqual(tool_error_code(result), ErrorCode.TOOL_RESULT_INVALID.value)

    def test_handler_exception_is_structured_execution_error(self) -> None:
        def handler(arguments: dict[str, Any]) -> Any:
            raise RuntimeError("private handler detail")

        registry = ToolRegistry((ToolSpec("sample", "Raise.", PARAMETERS, handler),))
        result, _ = self.run_tool_call(registry, tool_call())

        self.assertTrue(result.ok)
        content = json.loads(tool_output(result))
        self.assertEqual(content["error"]["code"], ErrorCode.TOOL_EXECUTION_FAILED.value)
        self.assertEqual(content["error"]["cause_class"], "RuntimeError")
        self.assertNotIn("private handler detail", tool_output(result))

    def test_tc_run_011_unknown_tool_executes_no_handler(self) -> None:
        calls = 0

        def known_handler(arguments: dict[str, Any]) -> Any:
            nonlocal calls
            calls += 1
            return arguments

        registry = ToolRegistry((ToolSpec("known", "Known.", PARAMETERS, known_handler),))
        result, _ = self.run_tool_call(registry, tool_call(name="missing"))

        self.assertTrue(result.ok)
        self.assertEqual(tool_error_code(result), ErrorCode.TOOL_NOT_FOUND.value)
        self.assertEqual(calls, 0)

    def test_malformed_tool_call_boundaries_execute_no_handler(self) -> None:
        malformed_calls = (
            tool_call(arguments="{not-json"),
            tool_call(arguments={"value": 1}),
            tool_call(function=[]),
        )

        for call in malformed_calls:
            with self.subTest(call=call):
                calls = 0

                def handler(arguments: dict[str, Any]) -> Any:
                    nonlocal calls
                    calls += 1
                    return arguments

                registry = ToolRegistry((ToolSpec("sample", "Sample.", PARAMETERS, handler),))
                result, _ = self.run_tool_call(registry, call)
                self.assertTrue(result.ok)
                self.assertEqual(tool_error_code(result), ErrorCode.TOOL_ARGUMENT_INVALID.value)
                self.assertEqual(calls, 0)

                safe = result.to_safe_dict()
                self.assertEqual(safe["message_count"], len(result.messages))
                self.assertNotIn('"value": 1', json.dumps(safe, ensure_ascii=False))

    def test_invalid_tool_call_id_fails_closed_before_handler(self) -> None:
        for invalid_id in (123, None, ""):
            with self.subTest(call_id=invalid_id):
                calls = 0

                def handler(arguments: dict[str, Any]) -> Any:
                    nonlocal calls
                    calls += 1
                    return arguments

                registry = ToolRegistry((ToolSpec("sample", "Sample.", PARAMETERS, handler),))
                result, client = self.run_tool_call(registry, tool_call(call_id=invalid_id))
                self.assertFalse(result.ok)
                self.assertEqual(result.error_class, ErrorCode.PROVIDER_RESPONSE_INVALID.value)
                self.assertEqual(result.error, "malformed provider tool call id")
                self.assertEqual(calls, 0)
                self.assertEqual(len(client.payloads), 1)
                self.assertEqual(result.to_safe_dict()["message_count"], len(result.messages))


class CliRegistryMigrationTests(unittest.TestCase):
    def test_no_tools_passes_none_instead_of_raw_mapping(self) -> None:
        result = SimpleNamespace(ok=True, to_dict=lambda include_content=False: {"ok": True})
        with tempfile.TemporaryDirectory() as workspace:
            with (
                patch("deepseek_runtime.cli.RuntimeSettings.from_env", return_value=object()),
                patch("deepseek_runtime.cli.DeepSeekClient", return_value=object()),
                patch("deepseek_runtime.cli.DeepSeekRuntime") as runtime_class,
                redirect_stdout(io.StringIO()),
            ):
                runtime_class.return_value.run.return_value = result
                exit_code = _run(["test", "--workspace", workspace, "--no-tools"])

        self.assertEqual(exit_code, 0)
        kwargs = runtime_class.return_value.run.call_args.kwargs
        self.assertIsNone(kwargs["tools"])

    def test_default_cli_path_passes_tool_registry(self) -> None:
        result = SimpleNamespace(ok=True, to_dict=lambda include_content=False: {"ok": True})
        with tempfile.TemporaryDirectory() as workspace:
            with (
                patch("deepseek_runtime.cli.RuntimeSettings.from_env", return_value=object()),
                patch("deepseek_runtime.cli.DeepSeekClient", return_value=object()),
                patch("deepseek_runtime.cli.DeepSeekRuntime") as runtime_class,
                redirect_stdout(io.StringIO()),
            ):
                runtime_class.return_value.run.return_value = result
                exit_code = _run(["test", "--workspace", workspace])

        self.assertEqual(exit_code, 0)
        kwargs = runtime_class.return_value.run.call_args.kwargs
        self.assertIsInstance(kwargs["tools"], ToolRegistry)
        self.assertEqual(kwargs["tools"].names, ("read_file", "search"))


if __name__ == "__main__":
    unittest.main()
