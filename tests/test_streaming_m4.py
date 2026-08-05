"""
M4 Streaming SSE 测试 — 覆盖 PROV-008/009。

- 跨 chunk 的 UTF-8 字符切分
- 跨 chunk 的事件行拼接
- 增量 parser 正确处理边界
- chat_stream 消费增量事件
"""

from __future__ import annotations

import unittest

from deepseek_runtime.client import DeepSeekClient, RuntimeSettings, iter_sse_events


class SseParserTests(unittest.TestCase):
    def test_cross_chunk_utf8_split(self) -> None:
        """PROV-008：UTF-8 字符在 chunk 边界被切分仍能正确解析。"""
        # "你好" 的中文字节可能被切分
        event = 'data: {"content": "你好"}\n\n'.encode("utf-8")
        # 切分点故意在中文字符中间
        chunks = [
            (0, event[:10]),
            (1, event[10:20]),
            (2, event[20:]),
        ]
        parsed = iter_sse_events(chunks)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][1]["content"], "你好")

    def test_cross_chunk_event_line_split(self) -> None:
        """PROV-008：事件行在跨 chunk 边界拼接。"""
        full = b'data: {"choices": [{"delta": {"content": "hi"}}]}\n\n'
        chunks = [
            (0, full[:5]),  # "data:"
            (1, full[5:15]),  # 中间
            (2, full[15:]),  # 剩余
        ]
        parsed = iter_sse_events(chunks)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][1]["choices"][0]["delta"]["content"], "hi")

    def test_multiple_events_and_done(self) -> None:
        """PROV-008：多个事件 + [DONE] 结束标记。"""
        chunks = [
            (0, b'data: {"a": 1}\n\n'),
            (1, b'data: {"b": 2}\n\n'),
            (2, b'data: [DONE]\n\n'),
        ]
        parsed = iter_sse_events(chunks)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0][1]["a"], 1)
        self.assertEqual(parsed[1][1]["b"], 2)

    def test_ignores_non_data_lines_and_heartbeats(self) -> None:
        """PROV-008：忽略非 data 行和心跳（空行）。"""
        chunks = [
            (0, b': keep-alive\n\n'),
            (1, b'data: {"x": 1}\n\n'),
            (2, b'\n\n'),
        ]
        parsed = iter_sse_events(chunks)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][1]["x"], 1)

    def test_byte_split_across_many_chunks(self) -> None:
        """PROV-008：单个字节逐个 chunk 到达也能拼接。"""
        full = b'data: {"msg": "hello"}\n\n'
        chunks = [(i, bytes([full[i]])) for i in range(len(full))]
        parsed = iter_sse_events(chunks)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][1]["msg"], "hello")

    def test_chat_stream_consumes_incremental_events(self) -> None:
        """PROV-009：chat_stream 消费增量事件。"""
        settings = RuntimeSettings(api_key="sk-test", max_retries=0)
        chunks = [
            (0, 'data: {"choices": [{"delta": {"content": "你"}}]}\n\n'.encode("utf-8")),
            (1, 'data: {"choices": [{"delta": {"content": "好"}}]}\n\n'.encode("utf-8")),
            (2, b'data: [DONE]\n\n'),
        ]

        def stream_transport(method, url, headers, data, timeout):
            return 200, {}, chunks

        client = DeepSeekClient(settings, stream_transport=stream_transport)
        result = client.chat_stream({"messages": [{"role": "user", "content": "hi"}]})
        body = result.body
        self.assertEqual(body["stream_evidence"]["event_count"], 2)


if __name__ == "__main__":
    unittest.main()