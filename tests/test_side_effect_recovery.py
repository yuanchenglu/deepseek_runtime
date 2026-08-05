from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from deepseek_runtime import (
    ErrorCode,
    OperatorAction,
    RecoveryPolicy,
    SessionState,
    ToolCallRecord,
    ToolExecutionResult,
    reconcile_tool_call,
    resume_tool_calls,
)
from deepseek_runtime.session import SessionStore


class SimulatedCrash(RuntimeError):
    pass


class SideEffectRecoveryTests(unittest.TestCase):
    def test_crash_after_effect_before_result_checkpoint_never_auto_retries(self) -> None:
        effects: list[int] = []
        saved: list[SessionState] = []
        state = SessionState(
            tool_calls=[ToolCallRecord("transfer", {"value": 7}, side_effect=True)]
        )

        def handler(arguments: dict[str, int]) -> ToolExecutionResult:
            effects.append(arguments["value"])
            return ToolExecutionResult("ok", {"external_id": "receipt-1"})

        def crash_after_second_save(current: SessionState) -> None:
            saved.append(copy.deepcopy(current))
            if len(saved) == 2:
                raise SimulatedCrash("crash after effect, before durable result")

        with self.assertRaises(SimulatedCrash):
            resume_tool_calls(state, {"transfer": handler}, crash_after_second_save)

        persisted = saved[0]
        self.assertEqual(persisted.tool_calls[0].status, "running")
        self.assertEqual(effects, [7])

        resume_tool_calls(persisted, {"transfer": handler})
        resume_tool_calls(persisted, {"transfer": handler})
        call = persisted.tool_calls[0]
        self.assertEqual(effects, [7])
        self.assertEqual(call.status, "side-effect-uncertain")
        self.assertEqual(call.error_code, ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN.value)

    def test_running_pure_call_retries_safely(self) -> None:
        calls: list[int] = []
        state = SessionState(
            tool_calls=[
                ToolCallRecord(
                    "read",
                    {"value": 1},
                    side_effect=False,
                    status="running",
                    attempt_count=1,
                )
            ]
        )

        resume_tool_calls(
            state,
            {"read": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, [1])
        self.assertEqual(state.tool_calls[0].status, "succeeded")

    def test_keyed_side_effect_retries_only_with_key(self) -> None:
        calls: list[str] = []
        keyed = ToolCallRecord(
            "charge",
            {"value": "keyed"},
            side_effect=True,
            status="running",
            attempt_count=1,
            recovery_policy=RecoveryPolicy.RETRYABLE_WITH_KEY,
            idempotency_key="idem-1",
        )
        state = SessionState(tool_calls=[keyed])
        resume_tool_calls(
            state,
            {"charge": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, ["keyed"])
        self.assertEqual(keyed.status, "succeeded")

        without_key = ToolCallRecord(
            "charge",
            {"value": "missing"},
            side_effect=True,
            status="running",
            attempt_count=1,
            recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
        )
        state = SessionState(tool_calls=[without_key])
        resume_tool_calls(
            state,
            {"charge": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, ["keyed"])
        self.assertEqual(without_key.status, "side-effect-uncertain")

    def test_non_idempotent_handler_exception_is_uncertain(self) -> None:
        call = ToolCallRecord("write", {}, side_effect=True)
        state = SessionState(tool_calls=[call])

        def handler(_: dict[str, object]) -> None:
            raise RuntimeError("connection lost after dispatch")

        resume_tool_calls(state, {"write": handler})
        self.assertEqual(call.status, "side-effect-uncertain")
        self.assertEqual(call.error_code, ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN.value)

    def test_operator_can_mark_succeeded_without_reexecution(self) -> None:
        call = ToolCallRecord(
            "transfer",
            {},
            side_effect=True,
            status="side-effect-uncertain",
            attempt_count=1,
        )
        state = SessionState(tool_calls=[call])
        reconcile_tool_call(
            state,
            call.call_id,
            OperatorAction.MARK_SUCCEEDED,
            receipt={"external_id": "tx-1"},
        )
        resume_tool_calls(state, {"transfer": lambda _: self.fail("must not execute")})
        self.assertEqual(call.status, "succeeded")
        self.assertEqual(call.receipt, {"external_id": "tx-1"})
        self.assertEqual(call.operator_action, OperatorAction.MARK_SUCCEEDED.value)

    def test_mark_not_executed_then_explicit_retry_runs_once(self) -> None:
        calls: list[int] = []
        call = ToolCallRecord(
            "transfer",
            {"value": 3},
            side_effect=True,
            status="side-effect-uncertain",
            attempt_count=1,
        )
        state = SessionState(tool_calls=[call])

        reconcile_tool_call(state, call.call_id, OperatorAction.MARK_NOT_EXECUTED)
        self.assertEqual(call.status, "failed")
        resume_tool_calls(
            state,
            {"transfer": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, [])

        reconcile_tool_call(state, call.call_id, OperatorAction.EXPLICIT_RETRY)
        resume_tool_calls(
            state,
            {"transfer": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, [3])
        self.assertEqual(call.status, "succeeded")
        self.assertEqual(call.attempt_count, 2)

    def test_abandon_keeps_call_terminal_and_unexecuted(self) -> None:
        call = ToolCallRecord(
            "transfer",
            {},
            side_effect=True,
            status="side-effect-uncertain",
            attempt_count=1,
        )
        state = SessionState(tool_calls=[call])
        reconcile_tool_call(state, call.call_id, OperatorAction.ABANDON)
        resume_tool_calls(state, {"transfer": lambda _: self.fail("must not execute")})
        self.assertEqual(call.status, "failed")
        self.assertEqual(call.error_code, ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN.value)

    def test_session_store_roundtrips_recovery_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            call = ToolCallRecord(
                "transfer",
                {"value": 5},
                side_effect=True,
                status="side-effect-uncertain",
                recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
                attempt_count=1,
                receipt={"external_id": "tx-5"},
                operator_action=OperatorAction.MARK_SUCCEEDED.value,
            )
            state = SessionState(tool_calls=[call])
            store.save(state)
            loaded = store.load(state.session_id).tool_calls[0]
            self.assertEqual(loaded.status, "side-effect-uncertain")
            self.assertEqual(loaded.recovery_policy, RecoveryPolicy.NON_IDEMPOTENT.value)
            self.assertEqual(loaded.attempt_count, 1)
            self.assertEqual(loaded.receipt, {"external_id": "tx-5"})
            self.assertEqual(loaded.operator_action, OperatorAction.MARK_SUCCEEDED.value)


if __name__ == "__main__":
    unittest.main()
