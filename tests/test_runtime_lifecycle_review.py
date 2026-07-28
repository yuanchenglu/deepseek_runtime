from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from deepseek_runtime import (
    ApprovalOutcome,
    DeepSeekRuntime,
    Decision,
    ErrorCode,
    FakeExecutionAdapter,
    LifecycleTrace,
    PermissionPolicy,
    PermissionRule,
    ProviderResult,
    RecoveryPolicy,
    Risk,
    RuntimeBudgets,
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


class Client:
    def __init__(self, messages: list[dict[str, Any]], usages: list[dict[str, Any]] | None = None) -> None:
        self.messages = list(messages)
        self.usages = list(usages or [{} for _ in messages])
        self.calls = 0

    def chat(self, payload: dict[str, Any]) -> ProviderResult:
        self.calls += 1
        if not self.messages:
            raise AssertionError("unexpected Provider call")
        message = self.messages.pop(0)
        usage = self.usages.pop(0)
        return ProviderResult(
            status=200,
            elapsed_ms=0,
            body={"choices": [{"message": message}], "usage": usage},
            request_fingerprint="review-fingerprint",
            request_payload=payload,
        )


def final_message() -> dict[str, Any]:
    return {"role": "assistant", "content": "done"}


def call(call_id: str, *, value: Any = "x") -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "sample",
            "arguments": json.dumps({"value": value}) if value is not None else "{}",
        },
    }


def tool_message(*calls: dict[str, Any]) -> dict[str, Any]:
    return {"role": "assistant", "content": None, "tool_calls": list(calls)}


def write_spec() -> ToolSpec:
    return ToolSpec(
        "sample",
        "Review side-effect tool.",
        PARAMETERS,
        lambda arguments: arguments["value"],
        risk=Risk.WRITE,
        side_effect=True,
        timeout_seconds=2.0,
        max_output_bytes=1000,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


class RuntimeLifecycleReviewTests(unittest.TestCase):
    def run_runtime(self, client: Client, **kwargs: Any) -> Any:
        with tempfile.TemporaryDirectory() as directory:
            return DeepSeekRuntime(client).run(
                [{"role": "user", "content": "private-review-marker"}],
                workspace=Path(directory),
                **kwargs,
            )

    def test_provider_completed_checkpoint_contains_provider_message(self) -> None:
        checkpoints: list[Any] = []
        result = self.run_runtime(
            Client([final_message()]),
            checkpoint_sink=checkpoints.append,
            session_id="provider-completed",
        )

        self.assertTrue(result.ok)
        completed = next(
            checkpoint
            for checkpoint in checkpoints
            if checkpoint.runtime_state is RuntimeState.PROVIDER_COMPLETED
        )
        self.assertEqual(completed.messages[-1]["role"], "assistant")
        self.assertEqual(completed.messages[-1]["content"], "done")

    def test_approval_pending_checkpoint_contains_pending_authorization(self) -> None:
        class Approver:
            def request_approval(self, request: Any) -> ApprovalOutcome:
                return ApprovalOutcome.APPROVE_ONCE

        checkpoints: list[Any] = []
        result = self.run_runtime(
            Client([tool_message(call("call-1")), final_message()]),
            tools=ToolRegistry((write_spec(),)),
            policy=PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ASK),)),
            approval_provider=Approver(),
            execution_adapter=FakeExecutionAdapter(("ok",)),
            checkpoint_sink=checkpoints.append,
            session_id="approval-pending",
        )

        self.assertTrue(result.ok)
        pending = next(
            checkpoint
            for checkpoint in checkpoints
            if checkpoint.runtime_state is RuntimeState.APPROVAL_PENDING
        )
        self.assertEqual(pending.approvals[-1]["approval_outcome"], "pending")

    def test_usage_evidence_excludes_unrecognized_string_content(self) -> None:
        marker = "private-usage-marker"
        result = self.run_runtime(
            Client([final_message()], [{"prompt_tokens": 1, "note": marker}])
        )

        self.assertTrue(result.ok)
        safe = json.dumps(result.to_safe_dict(), ensure_ascii=False)
        self.assertNotIn(marker, safe)
        self.assertEqual(result.evidence[0]["usage"], {"prompt_tokens": 1})

    def test_terminate_policy_preserves_invalid_argument_error(self) -> None:
        client = Client([tool_message(call("call-1", value=None))])
        result = self.run_runtime(
            client,
            tools=ToolRegistry((write_spec(),)),
            policy=PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ALLOW),)),
            tool_error_policy=ToolErrorPolicy.TERMINATE,
        )

        self.assertFalse(result.ok)
        self.assertEqual(client.calls, 1)
        self.assertEqual(result.error_class, ErrorCode.TOOL_ARGUMENT_INVALID.value)

    def test_multi_tool_batch_records_first_real_approval_pending(self) -> None:
        class Approver:
            def request_approval(self, request: Any) -> ApprovalOutcome:
                return ApprovalOutcome.APPROVE_ONCE

        result = self.run_runtime(
            Client([tool_message(call("call-1"), call("call-2")), final_message()]),
            tools=ToolRegistry((write_spec(),)),
            policy=PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ASK),)),
            approval_provider=Approver(),
            execution_adapter=FakeExecutionAdapter(("one", "two")),
        )

        self.assertTrue(result.ok)
        targets = [event["target"] for event in result.lifecycle_events]
        self.assertIn(RuntimeState.APPROVAL_PENDING.value, targets)
        self.assertEqual(targets.count(RuntimeState.TOOL_RUNNING.value), 1)
        self.assertEqual(targets.count(RuntimeState.TOOL_SUCCEEDED.value), 1)

    def test_later_batch_approval_is_checkpointed_before_execution(self) -> None:
        class Approver:
            def request_approval(self, request: Any) -> ApprovalOutcome:
                return ApprovalOutcome.APPROVE_ONCE

        checkpoints: list[Any] = []
        result = self.run_runtime(
            Client([tool_message(call("call-1"), call("call-2")), final_message()]),
            tools=ToolRegistry((write_spec(),)),
            policy=PermissionPolicy((PermissionRule(Risk.WRITE, Decision.ASK),)),
            approval_provider=Approver(),
            execution_adapter=FakeExecutionAdapter(("one", "two")),
            checkpoint_sink=checkpoints.append,
        )

        self.assertTrue(result.ok)
        second_pending_index = next(
            index
            for index, checkpoint in enumerate(checkpoints)
            if len(checkpoint.approvals) == 2
            and checkpoint.approvals[-1]["approval_outcome"] == "pending"
        )
        approved = checkpoints[second_pending_index + 1]
        self.assertIs(approved.runtime_state, RuntimeState.TOOL_RUNNING)
        self.assertEqual(approved.approvals[-1]["approval_outcome"], "approve-once")
        self.assertEqual(approved.tool_calls[-1].state, RuntimeState.TOOL_RUNNING)

    def test_equal_token_limit_stops_at_threshold(self) -> None:
        result = self.run_runtime(
            Client([final_message()], [{"total_tokens": 10}]),
            budgets=RuntimeBudgets(max_tokens=10),
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.error_class, ErrorCode.BUDGET_TOKEN_EXCEEDED.value)

    def test_generic_cost_field_does_not_claim_known_usd_cost(self) -> None:
        result = self.run_runtime(
            Client([final_message()], [{"cost": 1.0}]),
            budgets=RuntimeBudgets(max_cost_usd=0.1),
        )

        self.assertTrue(result.ok)
        self.assertIsNone(result.budget["observed"]["cost_usd"])
        self.assertFalse(result.budget["observed"]["cost_known"])

    def test_checkpoint_lifecycle_event_count_has_no_off_by_one(self) -> None:
        checkpoints: list[Any] = []
        result = self.run_runtime(Client([final_message()]), checkpoint_sink=checkpoints.append)

        self.assertTrue(result.ok)
        self.assertEqual(checkpoints[0].runtime_state, RuntimeState.PROVIDER_PENDING)
        self.assertEqual(checkpoints[0].recovery_metadata["lifecycle_event_count"], 1)

    def test_lifecycle_rejects_negative_step(self) -> None:
        trace = LifecycleTrace()
        with self.assertRaisesRegex(ValueError, "step"):
            trace.transition(RuntimeState.PROVIDER_PENDING, step=-1)


if __name__ == "__main__":
    unittest.main()
