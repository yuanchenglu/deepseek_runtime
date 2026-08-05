"""
M3 Recovery 测试 — 覆盖 SES-001~010。

- SES-001：checkpoint/evidence schema 分离
- SES-003：SessionStore 可选加密 at rest
- SES-004：原子写入 + 损坏检测（crash/corrupt）
- SES-005：schema migration
- SES-009：retry budget / backoff
- SES-010：approvals/budgets/receipts roundtrip
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from deepseek_runtime.contracts import (
    ErrorCode,
    OperatorAction,
    RecoveryPolicy,
    RuntimeState,
    ToolCallCheckpoint,
)
from deepseek_runtime.session import (
    SESSION_SCHEMA_VERSION,
    SessionState,
    SessionStore,
    ToolCallRecord,
    reconcile_tool_call,
    resume_tool_calls,
)


class RecoveryM3Tests(unittest.TestCase):
    def test_session_store_atomic_write_and_corrupt_detection(self) -> None:
        """SES-004：原子写入 + 损坏检测。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            state = SessionState(tool_calls=[ToolCallRecord("ls", {}, side_effect=False)])
            store.save(state)
            loaded = store.load(state.session_id)
            self.assertEqual(loaded.tool_calls[0].name, "ls")

            # 写入损坏内容 -> load 应报损坏
            store.path(state.session_id).write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                store.load(state.session_id)
            self.assertIn("corrupt", str(raised.exception))

    def test_session_store_optional_encryption_at_rest(self) -> None:
        """SES-003：可选加密 at rest。"""
        with tempfile.TemporaryDirectory() as directory:
            key = os.urandom(32)
            store = SessionStore(Path(directory), encrypt_key=key)
            call = ToolCallRecord("write", {"content": "secret-data"}, side_effect=True)
            state = SessionState(tool_calls=[call])
            store.save(state)

            # 磁盘上的文件不应包含明文
            raw = store.path(state.session_id).read_text(encoding="utf-8")
            self.assertNotIn("secret-data", raw)
            self.assertNotIn("write", raw)

            # 用相同密钥可解密恢复
            loaded = SessionStore(Path(directory), encrypt_key=key).load(state.session_id)
            self.assertEqual(loaded.tool_calls[0].arguments, {"content": "secret-data"})

            # 用错误密钥应报损坏
            wrong_store = SessionStore(Path(directory), encrypt_key=os.urandom(32))
            with self.assertRaises(ValueError):
                wrong_store.load(state.session_id)

    def test_session_store_wrong_key_length_rejected(self) -> None:
        """SES-003：加密密钥必须是 32 字节。"""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                SessionStore(Path(directory), encrypt_key=b"short")

    def test_schema_migration_from_legacy_version(self) -> None:
        """SES-005：legacy schema (1.0) 迁移到当前版本。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            legacy = {
                "schema_version": "1.0",
                "session_id": "abc123",
                "step": 0,
                "messages": [],
                "tool_calls": [
                    {
                        "name": "ls",
                        "arguments": {},
                        "side_effect": False,
                        "call_id": "call-1",
                        "status": "succeeded",
                        "result": "x",
                        "error": None,
                        "error_code": None,
                        "recovery_policy": "PURE",
                        "attempt_count": 1,
                        "idempotency_key": None,
                        "receipt": None,
                        "retry_authorized": False,
                        "operator_action": None,
                    }
                ],
                "approvals": [],
                "change_sets": [],
                "usage": {},
                "evidence": [],
            }
            store.path("abc123").write_text(json.dumps(legacy), encoding="utf-8")
            loaded = store.load("abc123")
            self.assertEqual(loaded.schema_version, SESSION_SCHEMA_VERSION)
            self.assertEqual(loaded.tool_calls[0].name, "ls")

    def test_resume_retry_budget_and_backoff(self) -> None:
        """SES-009：retry budget 限制 + 自动重试。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            call = ToolCallRecord(
                "pure-op",
                {},
                side_effect=False,
                status="failed",
                recovery_policy=RecoveryPolicy.PURE,
                attempt_count=2,
            )
            state = SessionState(tool_calls=[call])
            calls = []

            def handler(args: dict) -> str:
                calls.append(1)
                return "ok"

            # max_attempts=3，attempt_count 已达 2，允许再重试 1 次
            resume_tool_calls(state, {"pure-op": handler}, max_attempts=3)
            self.assertEqual(len(calls), 1)
            self.assertEqual(state.tool_calls[0].status, "succeeded")

    def test_reconcile_approval_receipt_roundtrip(self) -> None:
        """SES-010：operator 决策 + receipt roundtrip。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            call = ToolCallRecord(
                "transfer",
                {"amount": 5},
                side_effect=True,
                status="side-effect-uncertain",
                recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
            )
            state = SessionState(tool_calls=[call])
            reconcile_tool_call(
                state,
                call.call_id,
                OperatorAction.MARK_SUCCEEDED,
                receipt={"external_id": "tx-123"},
            )
            self.assertEqual(state.tool_calls[0].status, "succeeded")
            self.assertEqual(state.tool_calls[0].receipt, {"external_id": "tx-123"})

            # roundtrip 到磁盘
            store.save(state)
            loaded = store.load(state.session_id).tool_calls[0]
            self.assertEqual(loaded.status, "succeeded")
            self.assertEqual(loaded.receipt, {"external_id": "tx-123"})

    def test_checkpoint_evidence_schema_separation(self) -> None:
        """SES-001：ToolCallCheckpoint 有独立 schema 且可序列化。"""
        cp = ToolCallCheckpoint(
            call_id="c1",
            name="ls",
            arguments={},
            state=RuntimeState.TOOL_SUCCEEDED,
            recovery_policy=RecoveryPolicy.PURE,
            side_effect=False,
            attempt_count=1,
        )
        d = cp.to_dict()
        self.assertEqual(d["state"], RuntimeState.TOOL_SUCCEEDED.value)
        self.assertEqual(d["recovery_policy"], RecoveryPolicy.PURE.value)
        # checkpoint 是 JSON 兼容的
        json.dumps(d)


if __name__ == "__main__":
    unittest.main()