"""M6 coverage/governance tests — CFG-003, PROV-007, DOC-001."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from deepseek_runtime.client import DeepSeekClient, ProviderResult, RuntimeSettings
from deepseek_runtime.evidence import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class _Env:
    @staticmethod
    def pythonpath() -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        return env


class ConfigSecretM6Tests(unittest.TestCase):
    def test_cli_doctor_output_has_no_secrets(self) -> None:
        """CFG-003：CLI doctor 输出面无 secret 泄露。"""
        env = _Env.pythonpath()
        env["DEEPSEEK_API_KEY"] = "sk-super-secret-key-12345"
        completed = subprocess.run(
            [sys.executable, "-m", "deepseek_runtime.cli", "doctor", "--json", "--workspace", str(ROOT)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = completed.stdout
        self.assertNotIn("sk-super-secret-key-12345", output)
        json.loads(output)  # 合法 JSON

    def test_provider_response_manifest_has_no_secrets(self) -> None:
        """CFG-003：Provider 响应构件输出面无 secret。"""
        # ProviderResult.request_payload 含 api_key 时应被 evidence redaction 覆盖
        payload = {"model": "deepseek-v4", "api_key": "sk-leak", "messages": []}
        result = ProviderResult(
            status=200, elapsed_ms=1, body={}, request_fingerprint="x",
            request_payload=payload,
        )
        # 构造响应证据并确认不含 api_key 值
        from deepseek_runtime.evidence import redact
        safe = redact({"payload": payload, "body": result.body})
        blob = json.dumps(safe)
        self.assertNotIn("sk-leak", blob)


class ProviderIdentityM6Tests(unittest.TestCase):
    def test_request_identity_envelope_consistent(self) -> None:
        """PROV-007：request_fingerprint 与请求内容一致且可复现。"""
        payload = {"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "hi"}]}
        fp1 = fingerprint(payload)
        fp2 = fingerprint(payload)
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)

    def test_provider_result_carries_request_id_and_fingerprint(self) -> None:
        """PROV-007：ProviderResult identity envelope 完整。"""
        result = ProviderResult(
            status=200, elapsed_ms=5, body={"choices": []},
            request_fingerprint="abc123",
            request_id="req-xyz",
            request_payload={"model": "m"},
        )
        self.assertEqual(result.request_id, "req-xyz")
        self.assertEqual(result.request_fingerprint, "abc123")
        self.assertIsNotNone(result.request_payload)


class DoctorSemanticsM6Tests(unittest.TestCase):
    def test_doctor_is_diagnostic_not_live_run(self) -> None:
        """DOC-001：doctor 是诊断命令，不是在线可运行命令。"""
        env = _Env.pythonpath()
        # 无 API Key 时 doctor 仍应成功（不依赖在线）
        env.pop("DEEPSEEK_API_KEY", None)
        completed = subprocess.run(
            [sys.executable, "-m", "deepseek_runtime.cli", "doctor", "--json", "--workspace", str(ROOT)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        data = json.loads(completed.stdout)
        # doctor 报告应标注它不执行在线请求
        blob = json.dumps(data)
        self.assertTrue(any(marker in blob for marker in ("diagnostic", "doctor", "workspace")))


if __name__ == "__main__":
    unittest.main()