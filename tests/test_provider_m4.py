"""
M4 Provider 测试 — 覆盖 PROV-005/006、CFG-004/005。

- PROV-005：retry/backoff（5xx 重试、网络错误重试、4xx 不重试）
- PROV-006：response-size limit（普通 + 流式）
- CFG-004：settings 校验
- CFG-005：from_env 语义
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from deepseek_runtime.client import DeepSeekClient, RuntimeSettings


def _settings(**overrides: object) -> RuntimeSettings:
    base: dict[str, object] = dict(
        api_key="sk-test",
        max_retries=2,
        retry_backoff_seconds=0.001,  # 测试用极短退避
        max_response_bytes=1024,
    )
    base.update(overrides)
    return RuntimeSettings(**base)  # type: ignore[arg-type]


class ProviderRetryTests(unittest.TestCase):
    def test_5xx_is_retried_and_succeeds(self) -> None:
        """PROV-005：5xx 重试后成功。"""
        calls = []

        def transport(method, url, headers, data, timeout):
            calls.append(1)
            if len(calls) == 1:
                return 503, {}, b'{"error": {"message": "overloaded"}}'
            return 200, {}, b'{"choices": [{"message": {"content": "ok"}}]}'

        client = DeepSeekClient(_settings(), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 200)
        self.assertEqual(len(calls), 2)  # 1 次失败 + 1 次成功

    def test_network_error_is_retried(self) -> None:
        """PROV-005：网络错误重试后成功。"""
        import urllib.error

        calls = []

        def transport(method, url, headers, data, timeout):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.URLError("connection refused")
            return 200, {}, b'{"choices": [{"message": {"content": "ok"}}]}'

        client = DeepSeekClient(_settings(), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 200)
        self.assertEqual(len(calls), 2)

    def test_4xx_is_not_retried(self) -> None:
        """PROV-005：4xx 不重试。"""
        calls = []

        def transport(method, url, headers, data, timeout):
            calls.append(1)
            return 400, {}, b'{"error": {"message": "bad request"}}'

        client = DeepSeekClient(_settings(), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 400)
        self.assertEqual(len(calls), 1)  # 不重试

    def test_retry_exhausted_returns_error(self) -> None:
        """PROV-005：重试耗尽返回最后一次错误。"""
        calls = []

        def transport(method, url, headers, data, timeout):
            calls.append(1)
            return 500, {}, b'{"error": {"message": "still down"}}'

        client = DeepSeekClient(_settings(max_retries=2), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 500)
        self.assertEqual(len(calls), 3)  # 初始 + 2 次重试


class ProviderSizeLimitTests(unittest.TestCase):
    def test_response_exceeding_size_limit_rejected(self) -> None:
        """PROV-006：响应体超过上限被拒绝。"""
        big = b'{"choices": [{"message": {"content": "' + b"a" * 5000 + b'"}}]}'

        def transport(method, url, headers, data, timeout):
            return 200, {}, big

        client = DeepSeekClient(_settings(max_response_bytes=1024), transport=transport)
        result = client.chat({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 0)
        self.assertIn("size limit", result.error)

    def test_stream_exceeding_size_limit_rejected(self) -> None:
        """PROV-006：流式响应超过上限被拒绝。"""
        chunks = [(0, b"data: " + b"a" * 5000 + b"\n")]

        def stream_transport(method, url, headers, data, timeout):
            return 200, {}, chunks

        client = DeepSeekClient(
            _settings(max_response_bytes=1024),
            stream_transport=stream_transport,
        )
        result = client.chat_stream({"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(result.status, 0)
        self.assertIn("size limit", result.error)


class SettingsTests(unittest.TestCase):
    def test_from_env_parses_retry_and_limit(self) -> None:
        """CFG-004/005：from_env 解析 retry/limit 配置。"""
        env = {
            "DEEPSEEK_API_KEY": "sk-env",
            "DEEPSEEK_MAX_RETRIES": "3",
            "DEEPSEEK_MAX_RESPONSE_BYTES": "2048",
        }
        with patch.dict("os.environ", env, clear=False):
            settings = RuntimeSettings.from_env()
        self.assertEqual(settings.max_retries, 3)
        self.assertEqual(settings.max_response_bytes, 2048)
        self.assertEqual(settings.api_key, "sk-env")

    def test_invalid_settings_rejected(self) -> None:
        """CFG-004：非法配置被拒绝。"""
        with self.assertRaises(ValueError):
            RuntimeSettings(api_key="x", max_retries=-1)
        with self.assertRaises(ValueError):
            RuntimeSettings(api_key="x", max_response_bytes=0)


if __name__ == "__main__":
    unittest.main()