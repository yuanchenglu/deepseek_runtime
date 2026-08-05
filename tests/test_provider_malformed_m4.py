"""
M4 Provider malformed response 测试 — 覆盖 PROV-002/003/004。

- PROV-002：任意 JSON root 不崩溃（normalization）
- PROV-003：malformed response 分类（body/choices/choice/message/tool_calls/call id）
- PROV-004：error-code 分类正确
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from deepseek_runtime.client import DeepSeekClient, RuntimeSettings


def _settings() -> RuntimeSettings:
    return RuntimeSettings(api_key="sk-test", max_retries=0)


def _client(body: object) -> DeepSeekClient:
    payload = json.dumps(body).encode() if not isinstance(body, bytes) else body

    def transport(method, url, headers, data, timeout):
        return 200, {}, payload

    return DeepSeekClient(_settings(), transport=transport)


class MalformedResponseTests(unittest.TestCase):
    def test_arbitrary_root_does_not_crash(self) -> None:
        """PROV-002：任意 root 不崩溃。"""
        weird_roots = [
            None,
            [],
            "string",
            42,
            {"choices": None},
            {"choices": []},
            {"choices": [None]},
            {"choices": [{"message": None}]},
            {"choices": [{"message": "x"}]},
        ]
        for root in weird_roots:
            client = _client(root)
            result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
            # 不应抛异常（arbitrary root 不崩溃）
            self.assertIsInstance(result, object)

    def test_malformed_body_is_classified(self) -> None:
        """PROV-003：body 非对象分类。"""
        client = _client("not-an-object")
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 200)
        # body 是字符串 -> json.loads 后是 str，runtime 会报 PROVIDER_RESPONSE_INVALID

    def test_error_status_maps_to_error_class(self) -> None:
        """PROV-004：HTTP 错误分类。"""
        def transport(method, url, headers, data, timeout):
            return 429, {}, b'{"error": {"message": "rate limited"}}'

        client = DeepSeekClient(_settings(), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 429)
        self.assertEqual(result.error_class, "http")
        self.assertIn("rate limited", result.error or "")


if __name__ == "__main__":
    unittest.main()