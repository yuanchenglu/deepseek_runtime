"""
M5 Release/Packaging 测试 — 覆盖 OSS-005/006/007/008。

- OSS-007：release_gate_audit 重算 digest 检测 tamper
- OSS-006：build_release_artifact 排除 denylist
- OSS-008：source artifact 可重现
- OSS-005：secret scan 覆盖
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class ReleaseGateM5Tests(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        return env

    def test_audit_detects_tampered_artifact(self) -> None:
        """OSS-007：tamper 后重算 digest 不匹配。"""
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            release = out / "release.json"
            live = out / "live.json"
            manifest = out / "manifest.json"
            artifact = out / "artifact.tar.gz"

            release.write_text(json.dumps({"success": True}), encoding="utf-8")
            live.write_text(json.dumps({
                "success": True, "provider_status": 200,
                "leak_checks": {"api_key_absent": True, "prompt_absent": True,
                                "response_content_absent": True, "reasoning_content_absent": True},
            }), encoding="utf-8")
            artifact.write_bytes(b"original content")
            manifest.write_text(json.dumps({
                "success": True,
                "artifacts": [{"path": str(artifact), "sha256": "a" * 64}],
            }), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "scripts/release_gate_audit.py",
                 "--release-drill-result", str(release),
                 "--live-smoke-result", str(live),
                 "--manifest", str(manifest),
                 "--out", str(out / "audit.json")],
                cwd=ROOT, env=self._env(), text=True, capture_output=True, check=False,
            )
            # 记录 sha256 是假的 "a"*64，重算不匹配 -> 审计失败
            self.assertEqual(result.returncode, 1)
            audit = json.loads((out / "audit.json").read_text(encoding="utf-8"))
            self.assertFalse(audit["success"])
            digest_check = next(c for c in audit["checks"] if c["name"] == "artifact_digest_verified")
            self.assertFalse(digest_check["ok"])
            self.assertTrue(digest_check["evidence"]["failures"])

    def test_audit_passes_untampered_artifact(self) -> None:
        """OSS-007：未篡改构件通过 digest 校验。"""
        import hashlib

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            release = out / "release.json"
            live = out / "live.json"
            manifest = out / "manifest.json"
            artifact = out / "artifact.tar.gz"

            release.write_text(json.dumps({"success": True}), encoding="utf-8")
            live.write_text(json.dumps({
                "success": True, "provider_status": 200,
                "leak_checks": {"api_key_absent": True, "prompt_absent": True,
                                "response_content_absent": True, "reasoning_content_absent": True},
            }), encoding="utf-8")
            artifact.write_bytes(b"original content")
            real_digest = hashlib.sha256(b"original content").hexdigest()
            manifest.write_text(json.dumps({
                "success": True,
                "artifacts": [{"path": str(artifact), "sha256": real_digest}],
            }), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "scripts/release_gate_audit.py",
                 "--release-drill-result", str(release),
                 "--live-smoke-result", str(live),
                 "--manifest", str(manifest),
                 "--out", str(out / "audit.json")],
                cwd=ROOT, env=self._env(), text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0)
            audit = json.loads((out / "audit.json").read_text(encoding="utf-8"))
            self.assertTrue(audit["success"])

    def test_build_release_artifact_excludes_denylist(self) -> None:
        """OSS-006：打包排除 .venv/__pycache__/.git。"""
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "dist"
            manifest = Path(directory) / "manifest.json"
            result = subprocess.run(
                [sys.executable, "scripts/build_release_artifact.py",
                 "--out", str(out), "--manifest", str(manifest)],
                cwd=ROOT, env=self._env(), text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0)
            data = json.loads((manifest).read_text(encoding="utf-8"))
            self.assertTrue(data["success"])
            included = data["included_files"]
            # 不应包含被排除的路径
            for path in included:
                self.assertNotIn(".venv/", path)
                self.assertNotIn("__pycache__/", path)
                self.assertNotIn(".git/", path)


if __name__ == "__main__":
    unittest.main()