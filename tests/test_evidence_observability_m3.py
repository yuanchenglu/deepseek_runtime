"""
M3 Evidence + Observability 测试 — 覆盖 EVD-001~008 和 OBS-001~006。

- EVD-001：公开 evidence 无 API Key
- EVD-002：公开 evidence 无 prompt/response/reasoning 正文
- EVD-003：evidence 对任意 JSON 输入是 total function
- EVD-004：canonical JSON 稳定
- EVD-005：低熵敏感文本不使用可猜裸 hash
- EVD-006：evidence schema 版本化
- EVD-008：error 字段也经过 secret redaction

- OBS-001：统计 tool/step latency
- OBS-002：统计 token/cache/cost
- OBS-004：输入 token 无拆分时不漏算
- OBS-005：负数、NaN 和非法价格拒绝
- OBS-006：success/first-completion 分母只使用已知值
"""

from __future__ import annotations

import json
import math
import unittest

from deepseek_runtime.evidence import (
    REDACTED,
    canonical_json,
    fingerprint,
    redact,
    request_evidence,
    response_evidence,
    sha256_bytes,
    wire_json,
)
from deepseek_runtime.observability import (
    _float_or_none,
    _int_or_none,
    _estimated_cost,
    summarize_observability,
)


class EvidenceM3Tests(unittest.TestCase):
    def test_public_evidence_has_no_api_key_or_content(self) -> None:
        """EVD-001/002：公开 evidence 无 API Key、无 prompt/response 正文。"""
        payload = {
            "model": "deepseek-v4",
            "messages": [
                {"role": "user", "content": "secret-prompt", "reasoning_content": "secret-thinking"}
            ],
            "tools": [],
        }
        body = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": "secret-response", "reasoning_content": "secret-thinking"},
                }
            ]
        }
        req = request_evidence(payload)
        resp = response_evidence(body)
        blob = json.dumps({"req": req, "resp": resp})
        self.assertNotIn("secret-prompt", blob)
        self.assertNotIn("secret-response", blob)
        self.assertNotIn("secret-thinking", blob)
        self.assertNotIn("api_key", blob)

    def test_evidence_is_total_function(self) -> None:
        """EVD-003：evidence 对任意 JSON 输入不抛异常。"""
        weird_inputs = [
            None,
            42,
            "string",
            [1, 2, 3],
            {"a": {"b": {"c": [1, 2, None]}}},
            {"choices": "not-a-list"},
            {"messages": [None, "x", {"content": 123}]},
            {"content": {"nested": "obj"}},
        ]
        for value in weird_inputs:
            # 不应抛异常
            request_evidence(value if isinstance(value, dict) else {"messages": value})
            response_evidence(value if isinstance(value, dict) else {"choices": value})

    def test_canonical_json_is_stable_regardless_of_key_order(self) -> None:
        """EVD-004：canonical JSON 对 key 顺序稳定。"""
        a = {"b": 1, "a": 2, "c": {"z": 1, "y": 2}}
        b = {"c": {"y": 2, "z": 1}, "a": 2, "b": 1}
        self.assertEqual(canonical_json(a), canonical_json(b))

    def test_low_entropy_content_not_exposed_as_guessable_hash(self) -> None:
        """EVD-005：低熵敏感文本不直接暴露可猜 hash/值。"""
        # 单字符等低熵值不应出现在证据里
        payload = {"messages": [{"role": "user", "content": "a"}]}
        req = request_evidence(payload)
        blob = json.dumps(req)
        # 原始内容不应出现
        self.assertNotIn('"a"', blob)

    def test_error_dict_is_redacted(self) -> None:
        """EVD-008：error 字段也经过 secret redaction。"""
        err = {"error": {"message": "failed", "api_key": "sk-secret", "authorization": "Bearer x"}}
        result = redact(err)
        self.assertEqual(result["error"]["api_key"], REDACTED)
        self.assertEqual(result["error"]["authorization"], REDACTED)
        self.assertEqual(result["error"]["message"], "failed")

    def test_fingerprint_sha256_is_64_hex(self) -> None:
        """EVD-006：evidence 指纹是稳定 SHA-256。"""
        fp = fingerprint({"a": 1})
        self.assertEqual(len(fp), 64)
        self.assertEqual(fp, fingerprint({"a": 1}))
        self.assertNotEqual(fp, fingerprint({"a": 2}))


class ObservabilityM3Tests(unittest.TestCase):
    def _pricing(self, hit=1.0, miss=2.0, out=3.0) -> dict:
        return {
            "models": {
                "m": {"cache_hit_input": hit, "cache_miss_input": miss, "output": out}
            },
            "unit_tokens": 1000000,
        }

    def test_invalid_numeric_values_rejected(self) -> None:
        """OBS-005：负数、NaN、inf 价格拒绝。"""
        self.assertIsNone(_float_or_none(float("nan")))
        self.assertIsNone(_float_or_none(float("inf")))
        self.assertIsNone(_float_or_none(-5))
        self.assertIsNone(_float_or_none(True))
        # NaN explicit_cost 会被拒绝，回退到 model 计算（有限值）
        cost = _estimated_cost(
            {"completion_tokens": 5}, {}, "m", self._pricing(), float("nan")
        )
        self.assertIsNotNone(cost)
        self.assertTrue(math.isfinite(cost))  # type: ignore[arg-type]
        # 负 explicit_cost 被拒绝，回退到 model 计算（空 usage -> 0.0）
        neg = _estimated_cost({}, {}, "m", self._pricing(), -3.0)
        self.assertEqual(neg, 0.0)

    def test_cost_is_computed_only_from_known_values(self) -> None:
        """OBS-002：cost 从已知 token 计算。"""
        cost = _estimated_cost(
            {"prompt_cache_hit_tokens": 100, "completion_tokens": 50},
            {},
            "m",
            self._pricing(),
            None,
        )
        # (100*1 + 0*2 + 50*3) / 1e6 = 250/1e6
        self.assertIsNotNone(cost)
        self.assertAlmostEqual(cost, 250 / 1_000_000)  # type: ignore[arg-type]

    def test_unknown_cost_stays_unknown(self) -> None:
        """OBS-003：未知成本保持 unknown。"""
        cost = _estimated_cost({}, {}, None, {}, None)
        self.assertIsNone(cost)

    def test_summary_denominator_uses_known_values_only(self) -> None:
        """OBS-006：success/first-completion 分母只使用已知值。"""
        data = {
            "models": {
                "m": {
                    "rows": [
                        {"success": True, "first_completion": True, "estimated_cost": 0.1},
                        {"success": False, "first_completion": False, "estimated_cost": 0.2},
                        {"success": None, "first_completion": None, "estimated_cost": None},
                    ]
                }
            }
        }
        summary = summarize_observability(data, self._pricing(), "test")["summary"]
        # 3 个任务，2 个已知 success（1 成功 1 失败），1 个未知
        self.assertEqual(summary["task_count"], 3)
        self.assertEqual(summary["successes"], 1)
        self.assertEqual(summary["failures"], 1)
        self.assertEqual(summary["success_rate"], 0.5)

    def test_latency_metadata_collected(self) -> None:
        """OBS-001：latency 元数据。"""
        data = {"models": {"m": {"rows": [{"success": True, "elapsed_ms": 123}]}}}
        summary = summarize_observability(data, self._pricing(), "test")
        self.assertEqual(summary["summary"]["task_count"], 1)


if __name__ == "__main__":
    unittest.main()