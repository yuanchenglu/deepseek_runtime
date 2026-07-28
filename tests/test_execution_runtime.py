from __future__ import annotations

import json
import sys
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from deepseek_runtime import (
    CancellationToken,
    Decision,
    DeepSeekRuntime,
    ErrorCode,
    FakeExecutionAdapter,
    NoIsolationLocalAdapter,
    PermissionPolicy,
    PermissionRule,
    ProviderResult,
    RecoveryPolicy,
    RestrictedSubprocessAdapter,
    Risk,
    SubprocessRequest,
    ToolRegistry,
    ToolSpec,
)


PARAMETERS = {
    "type": "object",
    "properties": {"value": {"type": "string"}},
    "required": ["value"],
    "additionalProperties": False,
}


class SequencedClient:
    def __init__(self, messages: Iterable[dict[str, Any]]) -> None:
        self.messages = list(messages)
        self.calls = 0

    def chat(self, payload: dict[str, Any]) -> ProviderResult:
        self.calls += 1
        if not self.messages:
            raise AssertionError("unexpected Provider call")
        message = self.messages.pop(0)
        return ProviderResult(
            status=200,
            elapsed_ms=0,
            body={"choices": [{"message": message}], "usage": {}},
            request_fingerprint="execution-runtime-test",
            request_payload=payload,
        )


def tool_message(arguments: dict[str, Any], *, name: str = "sample") -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments),
                },
            }
        ],
    }


def final_message() -> dict[str, Any]:
    return {"role": "assistant", "content": "done"}


def tool_contents(result: Any) -> list[str]:
    return [
        str(message["content"])
        for message in result.messages
        if message.get("role") == "tool"
    ]


def error_code(content: str) -> str:
    return str(json.loads(content)["error"]["code"])


def read_spec(handler: Any) -> ToolSpec:
    return ToolSpec(
        "sample",
        "Execution runtime test tool.",
        PARAMETERS,
        handler,
        risk=Risk.READ,
        side_effect=False,
        timeout_seconds=2.0,
        max_output_bytes=10_000,
        recovery_policy=RecoveryPolicy.PURE,
    )


def shell_spec(handler: Any, *, timeout_seconds: float = 2.0) -> ToolSpec:
    return ToolSpec(
        "sample",
        "Restricted command test tool.",
        PARAMETERS,
        handler,
        risk=Risk.SHELL_SAFE,
        side_effect=True,
        timeout_seconds=timeout_seconds,
        max_output_bytes=10_000,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


class RuntimeExecutionAdapterTests(unittest.TestCase):
    def run_runtime(
        self,
        registry: ToolRegistry,
        *,
        adapter: Any = None,
        policy: PermissionPolicy | None = None,
        arguments: dict[str, Any] | None = None,
        cancellation: CancellationToken | None = None,
    ) -> tuple[Any, SequencedClient]:
        call_arguments = {"value": "x"} if arguments is None else arguments
        client = SequencedClient((tool_message(call_arguments), final_message()))
        with tempfile.TemporaryDirectory() as workspace:
            result = DeepSeekRuntime(client).run(
                [{"role": "user", "content": "test"}],
                workspace=Path(workspace),
                tools=registry,
                policy=policy,
                execution_adapter=adapter,
                cancellation=cancellation,
            )
        return result, client

    def test_fake_adapter_is_the_runtime_execution_boundary(self) -> None:
        handler_calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal handler_calls
            handler_calls += 1
            return "unexpected"

        adapter = FakeExecutionAdapter(({"from": "adapter"},))
        result, _ = self.run_runtime(ToolRegistry((read_spec(handler),)), adapter=adapter)

        self.assertTrue(result.ok)
        self.assertEqual(handler_calls, 0)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(tool_contents(result)[0], '{"from":"adapter"}')
        event = result.evidence[0]["execution_events"][0]
        self.assertEqual(event["adapter"], "fake")
        self.assertEqual(event["status"], "succeeded")
        self.assertNotIn("arguments", json.dumps(event))

    def test_policy_denial_prevents_adapter_and_handler_execution(self) -> None:
        handler_calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal handler_calls
            handler_calls += 1
            return "unexpected"

        adapter = FakeExecutionAdapter(("unexpected",))
        policy = PermissionPolicy(
            [PermissionRule(Risk.READ, Decision.DENY, path_glob="*")]
        )
        result, _ = self.run_runtime(
            ToolRegistry((read_spec(handler),)),
            adapter=adapter,
            policy=policy,
        )

        self.assertEqual(handler_calls, 0)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(error_code(tool_contents(result)[0]), ErrorCode.PERMISSION_DENIED.value)
        self.assertEqual(result.evidence[0]["execution_events"], [])

    def test_schema_failure_prevents_adapter_execution(self) -> None:
        adapter = FakeExecutionAdapter(("unexpected",))
        result, _ = self.run_runtime(
            ToolRegistry((read_spec(lambda arguments: "unexpected"),)),
            adapter=adapter,
            arguments={},
        )

        self.assertEqual(adapter.calls, [])
        self.assertEqual(
            error_code(tool_contents(result)[0]),
            ErrorCode.TOOL_ARGUMENT_INVALID.value,
        )
        self.assertEqual(result.evidence[0]["execution_events"], [])

    def test_default_adapter_preserves_local_handler_behavior_with_honest_evidence(self) -> None:
        result, _ = self.run_runtime(
            ToolRegistry((read_spec(lambda arguments: arguments["value"].upper()),))
        )

        self.assertEqual(tool_contents(result)[0], "X")
        event = result.evidence[0]["execution_events"][0]
        self.assertEqual(event["adapter"], NoIsolationLocalAdapter.name)
        self.assertEqual(event["capabilities"]["isolation"], "none")
        self.assertFalse(event["capabilities"]["kernel_isolation"])
        self.assertFalse(event["capabilities"]["timeout_enforced"])

    def test_restricted_adapter_executes_subprocess_after_policy_allow(self) -> None:
        def builder(arguments: dict[str, Any]) -> SubprocessRequest:
            code = "import json;print(json.dumps({'value':" + repr(arguments["value"]) + "}))"
            return SubprocessRequest((sys.executable, "-c", code))

        policy = PermissionPolicy(
            [PermissionRule(Risk.SHELL_SAFE, Decision.ALLOW, path_glob="*")]
        )
        result, _ = self.run_runtime(
            ToolRegistry((shell_spec(builder),)),
            adapter=RestrictedSubprocessAdapter(),
            policy=policy,
        )

        normalized = json.loads(tool_contents(result)[0])
        payload = json.loads(normalized["stdout"])
        self.assertEqual(payload, {"value": "x"})
        event = result.evidence[0]["execution_events"][0]
        self.assertEqual(event["adapter"], "restricted-subprocess")
        self.assertEqual(event["capabilities"]["isolation"], "process-restricted")
        self.assertFalse(event["capabilities"]["kernel_isolation"])
        self.assertNotIn("stdout", event)

    def test_cancelled_restricted_execution_is_structured_and_content_free(self) -> None:
        token = CancellationToken()

        class CancellingClient(SequencedClient):
            def chat(self, payload: dict[str, Any]) -> ProviderResult:
                result = super().chat(payload)
                token.cancel()
                return result

        policy = PermissionPolicy(
            [PermissionRule(Risk.SHELL_SAFE, Decision.ALLOW, path_glob="*")]
        )
        registry = ToolRegistry(
            (
                shell_spec(
                    lambda arguments: SubprocessRequest(
                        (sys.executable, "-c", "import time;time.sleep(5)")
                    )
                ),
            )
        )
        client = CancellingClient((tool_message({"value": "x"}),))
        with tempfile.TemporaryDirectory() as workspace:
            result = DeepSeekRuntime(client).run(
                [{"role": "user", "content": "test"}],
                workspace=Path(workspace),
                tools=registry,
                policy=policy,
                execution_adapter=RestrictedSubprocessAdapter(),
                cancellation=token,
            )

        content = tool_contents(result)[0]
        self.assertEqual(error_code(content), ErrorCode.CANCELLED.value)
        event = result.evidence[0]["execution_events"][0]
        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["error_code"], ErrorCode.CANCELLED.value)
        self.assertNotIn("time.sleep", json.dumps(event))

    def test_adapter_exception_message_is_not_exposed(self) -> None:
        class RaisingAdapter:
            name = "raising-adapter"
            capabilities = NoIsolationLocalAdapter.capabilities

            def execute(self, spec: ToolSpec, arguments: dict[str, Any], context: Any) -> Any:
                raise RuntimeError("private-adapter-secret")

        result, _ = self.run_runtime(
            ToolRegistry((read_spec(lambda arguments: "unused"),)),
            adapter=RaisingAdapter(),
        )

        content = tool_contents(result)[0]
        self.assertEqual(error_code(content), ErrorCode.TOOL_EXECUTION_FAILED.value)
        self.assertNotIn("private-adapter-secret", content)
        self.assertNotIn(
            "private-adapter-secret",
            json.dumps(result.to_safe_dict()),
        )

    def test_invalid_adapter_is_rejected_before_provider_call(self) -> None:
        client = SequencedClient((final_message(),))
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(TypeError):
                DeepSeekRuntime(client).run(
                    [{"role": "user", "content": "test"}],
                    workspace=Path(workspace),
                    tools=ToolRegistry(),
                    execution_adapter=object(),  # type: ignore[arg-type]
                )
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
