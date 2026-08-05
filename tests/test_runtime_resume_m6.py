"""M6 Runtime durable session resume tests — SES-002/006/008."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from deepseek_runtime import (
    DeepSeekRuntime,
    ProviderResult,
    RecoveryPolicy,
    ToolRegistry,
    ToolSpec,
)
from deepseek_runtime.session import SessionStore

PARAMETERS = {
    "type": "object",
    "properties": {"value": {"type": "string"}},
    "required": ["value"],
    "additionalProperties": False,
}


class SequencedClient:
    """Client that returns a fixed sequence of Provider messages."""

    def __init__(self, messages: list[dict]) -> None:
        self.messages = list(messages)
        self.calls = 0

    def chat(self, payload: dict) -> ProviderResult:
        self.calls += 1
        message = self.messages.pop(0)
        return ProviderResult(
            status=200,
            elapsed_ms=0,
            body={"choices": [{"message": message}], "usage": {}},
            request_fingerprint="resume-test",
            request_payload=payload,
        )


def tool_message(arguments: dict) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "sample",
                    "arguments": json.dumps(arguments),
                },
            }
        ],
    }


def final_message() -> dict:
    return {"role": "assistant", "content": "done"}


class RuntimeResumeM6Tests(unittest.TestCase):
    def _tool_registry(self) -> ToolRegistry:
        def handler(arguments: dict) -> dict:
            return {"value": "result"}

        return ToolRegistry(
            (
                ToolSpec(
                    "sample",
                    "resume test tool",
                    PARAMETERS,
                    handler,
                    risk="read",
                    side_effect=False,
                    timeout_seconds=2.0,
                    max_output_bytes=10_000,
                    recovery_policy=RecoveryPolicy.PURE,
                ),
            )
        )

    def test_session_is_persisted_during_run(self) -> None:
        """SES-006：run 期间 checkpoint 持久化到 SessionStore。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            client = SequencedClient([tool_message({"value": "x"}), final_message()])
            runtime = DeepSeekRuntime(client)
            result = runtime.run(
                [{"role": "user", "content": "test"}],
                workspace=Path(directory),
                tools=self._tool_registry(),
                session_id="session-1",
                session_store=store,
            )
            self.assertTrue(result.ok)
            # session 文件应存在且可加载
            loaded = store.load("session-1")
            self.assertEqual(loaded.session_id, "session-1")
            self.assertGreater(loaded.step, 0)

    def test_resume_loads_prior_messages(self) -> None:
        """SES-006/008：重跑同 session_id 时恢复 messages。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            # 先跑一次持久化
            client = SequencedClient([tool_message({"value": "x"}), final_message()])
            runtime = DeepSeekRuntime(client)
            result = runtime.run(
                [{"role": "user", "content": "original-prompt"}],
                workspace=Path(directory),
                tools=self._tool_registry(),
                session_id="session-2",
                session_store=store,
            )
            self.assertTrue(result.ok)
            persisted = store.load("session-2")
            self.assertTrue(any(m.get("content") == "original-prompt" for m in persisted.messages))

            # 第二次 run 同 session_id：恢复 messages 后继续
            client2 = SequencedClient([final_message()])
            result2 = DeepSeekRuntime(client2).run(
                [{"role": "user", "content": "original-prompt"}],
                workspace=Path(directory),
                tools=self._tool_registry(),
                session_id="session-2",
                session_store=store,
            )
            self.assertTrue(result2.ok)
            # 恢复后 messages 应包含首次的 tool 消息
            roles = [m.get("role") for m in result2.messages]
            self.assertIn("tool", roles)

    def test_no_session_store_still_runs(self) -> None:
        """SES-006：无 session_store 时行为不变。"""
        with tempfile.TemporaryDirectory() as directory:
            client = SequencedClient([final_message()])
            result = DeepSeekRuntime(client).run(
                [{"role": "user", "content": "test"}],
                workspace=Path(directory),
            )
            self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()