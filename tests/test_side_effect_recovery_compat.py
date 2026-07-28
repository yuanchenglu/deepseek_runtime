from __future__ import annotations

import unittest

from deepseek_runtime import (
    RecoveryPolicy,
    SessionState,
    ToolCallRecord,
    ToolExecutionResult,
    resume_tool_calls,
)


class SideEffectRecoveryCompatibilityTests(unittest.TestCase):
    def test_legacy_session_1_0_migrates_to_1_1_defaults(self) -> None:
        legacy = {
            "session_id": "legacy-session",
            "schema_version": "1.0",
            "step": 1,
            "messages": [],
            "tool_calls": [
                {
                    "name": "write",
                    "arguments": {"value": 1},
                    "side_effect": True,
                    "call_id": "legacy-call",
                    "status": "running",
                    "result": None,
                    "error": None,
                }
            ],
            "approvals": [],
            "change_sets": [],
            "usage": {},
            "evidence": [],
        }
        state = SessionState.from_dict(legacy)
        call = state.tool_calls[0]
        self.assertEqual(state.schema_version, "1.1")
        self.assertEqual(call.recovery_policy, RecoveryPolicy.NON_IDEMPOTENT.value)
        self.assertEqual(call.attempt_count, 0)
        self.assertEqual(call.status, "running")

    def test_future_session_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SessionState.from_dict(
                {
                    "session_id": "future-session",
                    "schema_version": "99.0",
                    "tool_calls": [],
                }
            )

    def test_failed_non_idempotent_side_effect_becomes_uncertain(self) -> None:
        calls: list[int] = []
        call = ToolCallRecord(
            "transfer",
            {"value": 9},
            side_effect=True,
            status="failed",
            attempt_count=1,
        )
        state = SessionState(tool_calls=[call])
        resume_tool_calls(
            state,
            {"transfer": lambda arguments: calls.append(arguments["value"]) or "done"},
        )
        self.assertEqual(calls, [])
        self.assertEqual(call.status, "side-effect-uncertain")

    def test_side_effect_success_always_has_structural_receipt(self) -> None:
        call = ToolCallRecord("write", {}, side_effect=True)
        state = SessionState(tool_calls=[call])
        resume_tool_calls(
            state,
            {"write": lambda _: ToolExecutionResult("ok", receipt=None)},
        )
        self.assertEqual(call.status, "succeeded")
        self.assertEqual(call.receipt["kind"], "handler-returned")
        self.assertEqual(call.receipt["call_id"], call.call_id)


if __name__ == "__main__":
    unittest.main()
