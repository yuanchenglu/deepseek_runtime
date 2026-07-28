from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from deepseek_runtime import (
    ApprovalOutcome,
    BudgetTracker,
    CancellationToken,
    ContractViolation,
    Decision,
    DeepSeekRuntime,
    ErrorCode,
    ExecutionCapabilities,
    ExecutionOutcome,
    FakeExecutionAdapter,
    IsolationLevel,
    PermissionPolicy,
    PermissionRule,
    ProviderResult,
    RecoveryPolicy,
    Risk,
    RuntimeBudgets,
    RuntimeErrorInfo,
    RuntimeState,
    ToolErrorPolicy,
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
    def __init__(self, responses: Iterable[ProviderResult]) -> None:
        self.responses = list(responses)
        self.calls = 0
        self.payloads: list[dict[str, Any]] = []

    def chat(self, payload: dict[str, Any]) -> ProviderResult:
        self.calls += 1
        self.payloads.append(payload)
        if not self.responses:
            raise AssertionError("unexpected Provider call")
        return self.responses.pop(0)


def provider(message: Any, *, usage: Any = None, body: Any = None) -> ProviderResult:
    response_body = (
        {"choices": [{"message": message}], "usage": {} if usage is None else usage}
        if body is None
        else body
    )
    return ProviderResult(
        status=200,
        elapsed_ms=1,
        body=response_body,  # type: ignore[arg-type]
        request_fingerprint="lifecycle-fingerprint",
        request_payload={"messages": []},
    )


def final_message(text: str = "done") -> dict[str, Any]:
    return {"role": "assistant", "content": text}


def tool_message(*, name: str = "sample", value: str = "x") -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps({"value": value}),
                },
            }
        ],
    }


def read_spec(handler: Any) -> ToolSpec:
    return ToolSpec(
        "sample",
        "Lifecycle read tool.",
        PARAMETERS,
        handler,
        risk=Risk.READ,
        side_effect=False,
        timeout_seconds=2.0,
        max_output_bytes=10_000,
        recovery_policy=RecoveryPolicy.PURE,
    )


def side_effect_spec(handler: Any) -> ToolSpec:
    return ToolSpec(
        "sample",
        "Lifecycle side-effect tool.",
        PARAMETERS,
        handler,
        risk=Risk.WRITE,
        side_effect=True,
        timeout_seconds=2.0,
        max_output_bytes=10_000,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


def states(result: Any) -> list[str]:
    return [str(event["target"]) for event in result.lifecycle_events]


class RuntimeLifecycleTests(unittest.TestCase):
    def run_runtime(self, client: SequencedClient, **kwargs: Any) -> Any:
        with tempfile.TemporaryDirectory() as directory:
            return DeepSeekRuntime(client).run(
                [{"role": "user", "content": "private-lifecycle-marker"}],
                workspace=Path(directory),
                **kwargs,
            )

    def test_text_completion_uses_validated_lifecycle_and_checkpoint(self) -> None:
        client = SequencedClient((provider(final_message(), usage={"total_tokens": 3}),))
        checkpoints: list[Any] = []
        result = self.run_runtime(client, checkpoint_sink=checkpoints.append, session_id="session-1")

        self.assertTrue(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.COMPLETED)
        self.assertEqual(
            states(result),
            ["PROVIDER_PENDING", "PROVIDER_COMPLETED", "COMPLETED"],
        )
        self.assertIsNotNone(result.checkpoint)
        self.assertEqual(result.checkpoint.runtime_state, RuntimeState.COMPLETED)
        self.assertEqual(checkpoints[-1].runtime_state, RuntimeState.COMPLETED)
        self.assertEqual(result.budget["observed"]["total_tokens"], 3)
        self.assertNotIn("private-lifecycle-marker", json.dumps(result.to_safe_dict()))

    def test_pre_provider_cancellation_sends_no_request(self) -> None:
        token = CancellationToken()
        token.cancel()
        client = SequencedClient((provider(final_message()),))

        result = self.run_runtime(client, cancellation=token)

        self.assertFalse(result.ok)
        self.assertEqual(client.calls, 0)
        self.assertIs(result.runtime_state, RuntimeState.CANCELLED)
        self.assertEqual(result.error_class, ErrorCode.CANCELLED.value)
        self.assertEqual(states(result), ["CANCELLED"])

    def test_known_token_budget_stops_after_provider(self) -> None:
        client = SequencedClient((provider(final_message(), usage={"total_tokens": 11}),))

        result = self.run_runtime(client, budgets=RuntimeBudgets(max_tokens=10))

        self.assertFalse(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.BUDGET_EXCEEDED)
        self.assertEqual(result.error_class, ErrorCode.BUDGET_TOKEN_EXCEEDED.value)
        self.assertEqual(result.budget["observed"]["total_tokens"], 11)

    def test_unknown_usage_remains_unknown_and_does_not_become_zero(self) -> None:
        client = SequencedClient((provider(final_message(), usage={}),))

        result = self.run_runtime(client, budgets=RuntimeBudgets(max_tokens=1, max_cost_usd=0.01))

        self.assertTrue(result.ok)
        observed = result.budget["observed"]
        self.assertIsNone(observed["total_tokens"])
        self.assertFalse(observed["total_tokens_known"])
        self.assertIsNone(observed["cost_usd"])
        self.assertFalse(observed["cost_known"])

    def test_step_budget_stops_before_second_provider_call(self) -> None:
        client = SequencedClient(
            (
                provider(tool_message()),
                provider(final_message()),
            )
        )
        registry = ToolRegistry((read_spec(lambda arguments: arguments["value"]),))

        result = self.run_runtime(
            client,
            tools=registry,
            execution_adapter=FakeExecutionAdapter(("ok",)),
            budgets=RuntimeBudgets(max_steps=1),
        )

        self.assertFalse(result.ok)
        self.assertEqual(client.calls, 1)
        self.assertEqual(result.error_class, ErrorCode.BUDGET_STEP_EXCEEDED.value)
        self.assertIs(result.runtime_state, RuntimeState.BUDGET_EXCEEDED)

    def test_tool_error_policy_continue_returns_error_to_provider(self) -> None:
        error = ContractViolation(
            RuntimeErrorInfo(ErrorCode.TOOL_EXECUTION_FAILED, "scripted failure")
        )
        client = SequencedClient((provider(tool_message()), provider(final_message())))
        registry = ToolRegistry((read_spec(lambda arguments: "unused"),))

        result = self.run_runtime(
            client,
            tools=registry,
            execution_adapter=FakeExecutionAdapter((error,)),
        )

        self.assertTrue(result.ok)
        self.assertEqual(client.calls, 2)
        self.assertIn("TOOL_FAILED", states(result))
        self.assertIs(result.runtime_state, RuntimeState.COMPLETED)

    def test_tool_error_policy_terminate_stops_without_second_provider(self) -> None:
        error = ContractViolation(
            RuntimeErrorInfo(ErrorCode.TOOL_EXECUTION_FAILED, "scripted failure")
        )
        client = SequencedClient((provider(tool_message()), provider(final_message())))
        registry = ToolRegistry((read_spec(lambda arguments: "unused"),))

        result = self.run_runtime(
            client,
            tools=registry,
            execution_adapter=FakeExecutionAdapter((error,)),
            tool_error_policy=ToolErrorPolicy.TERMINATE,
        )

        self.assertFalse(result.ok)
        self.assertEqual(client.calls, 1)
        self.assertIs(result.runtime_state, RuntimeState.FAILED)
        self.assertEqual(result.error_class, ErrorCode.TOOL_EXECUTION_FAILED.value)

    def test_single_ask_records_approval_pending_and_granted(self) -> None:
        class Approver:
            def request_approval(self, request: Any) -> ApprovalOutcome:
                return ApprovalOutcome.APPROVE_ONCE

        client = SequencedClient((provider(tool_message()), provider(final_message())))
        registry = ToolRegistry((side_effect_spec(lambda arguments: "unused"),))
        policy = PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ASK),))
        adapter = FakeExecutionAdapter(
            (
                ExecutionOutcome(
                    value="ok",
                    adapter="fake",
                    capabilities=FakeExecutionAdapter.capabilities,
                    duration_ms=0,
                    private_receipt={"receipt": "test"},
                ),
            )
        )

        result = self.run_runtime(
            client,
            tools=registry,
            policy=policy,
            approval_provider=Approver(),
            execution_adapter=adapter,
        )

        self.assertTrue(result.ok)
        self.assertIn("APPROVAL_PENDING", states(result))
        pending_index = states(result).index("APPROVAL_PENDING")
        self.assertEqual(states(result)[pending_index + 1], "TOOL_RUNNING")
        self.assertEqual(result.checkpoint.receipts, [{"receipt": "test"}])

    def test_pure_tool_cancellation_reaches_cancelled_terminal_state(self) -> None:
        token = CancellationToken()

        class CancellingAdapter:
            name = "cancelling"
            capabilities = ExecutionCapabilities(
                isolation=IsolationLevel.FAKE,
                timeout_enforced=False,
                cancellation_enforced=True,
                byte_output_limit=False,
                process_tree_cleanup=False,
                minimal_environment=False,
            )

            def execute(self, spec: ToolSpec, arguments: dict[str, Any], context: Any) -> Any:
                token.cancel()
                raise ContractViolation(
                    RuntimeErrorInfo(ErrorCode.CANCELLED, "tool execution was cancelled")
                )

        client = SequencedClient((provider(tool_message()),))
        registry = ToolRegistry((read_spec(lambda arguments: "unused"),))

        result = self.run_runtime(
            client,
            tools=registry,
            execution_adapter=CancellingAdapter(),
            cancellation=token,
        )

        self.assertFalse(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.CANCELLED)
        self.assertEqual(result.error_class, ErrorCode.CANCELLED.value)
        self.assertEqual(states(result)[-1], "CANCELLED")

    def test_side_effect_cancellation_returns_uncertain_not_cancelled(self) -> None:
        token = CancellationToken()

        class CancellingAdapter:
            name = "cancelling"
            capabilities = FakeExecutionAdapter.capabilities

            def execute(self, spec: ToolSpec, arguments: dict[str, Any], context: Any) -> Any:
                token.cancel()
                raise ContractViolation(
                    RuntimeErrorInfo(ErrorCode.CANCELLED, "tool execution was cancelled")
                )

        policy = PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ALLOW),))
        client = SequencedClient((provider(tool_message()),))
        registry = ToolRegistry((side_effect_spec(lambda arguments: "unused"),))

        result = self.run_runtime(
            client,
            tools=registry,
            policy=policy,
            execution_adapter=CancellingAdapter(),
            cancellation=token,
        )

        self.assertFalse(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN)
        self.assertEqual(result.error_class, ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN.value)
        self.assertNotEqual(states(result)[-1], "CANCELLED")

    def test_malformed_provider_root_returns_structured_result(self) -> None:
        client = SequencedClient((provider({}, body=[]),))

        result = self.run_runtime(client)

        self.assertFalse(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.FAILED)
        self.assertEqual(result.error_class, ErrorCode.PROVIDER_RESPONSE_INVALID.value)

    def test_checkpoint_sink_failure_is_structured_and_message_is_private(self) -> None:
        def sink(checkpoint: Any) -> None:
            raise RuntimeError("private-checkpoint-secret")

        client = SequencedClient((provider(final_message()),))

        result = self.run_runtime(client, checkpoint_sink=sink)

        self.assertFalse(result.ok)
        self.assertIs(result.runtime_state, RuntimeState.FAILED)
        self.assertEqual(result.error_class, ErrorCode.INTERNAL_ERROR.value)
        self.assertNotIn("private-checkpoint-secret", json.dumps(result.to_safe_dict()))


class BudgetTrackerTests(unittest.TestCase):
    def test_time_budget_uses_injected_monotonic_clock(self) -> None:
        now = [10.0]
        tracker = BudgetTracker(
            RuntimeBudgets(max_elapsed_seconds=1.0),
            clock=lambda: now[0],
        )
        now[0] = 11.1

        error = tracker.after_tool()

        self.assertIsNotNone(error)
        self.assertEqual(error.code, ErrorCode.BUDGET_TIME_EXCEEDED)

    def test_context_and_cost_limits_use_only_explicit_known_values(self) -> None:
        tracker = BudgetTracker(
            RuntimeBudgets(max_context_tokens=5, max_cost_usd=0.1),
            clock=lambda: 0.0,
        )
        tracker.record_provider(
            {"prompt_tokens": 6, "completion_tokens": 1, "estimated_cost_usd": 0.2},
            step=1,
        )

        error = tracker.after_provider()

        self.assertIsNotNone(error)
        self.assertEqual(error.code, ErrorCode.BUDGET_COST_EXCEEDED)
        self.assertEqual(tracker.snapshot()["observed"]["context_tokens"], 6)


if __name__ == "__main__":
    unittest.main()
