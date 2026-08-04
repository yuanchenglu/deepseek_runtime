"""
M3 ChangeManager 测试 — 覆盖 CHG-003~009。

- CHG-003：apply 拒绝同一 change_set 内重复路径
- CHG-004：并发 apply/rollback 同一实例被串行化（进程内锁）
- CHG-006：mode/metadata 按策略保留
- CHG-007：写入后 fsync 文件与父目录（crash-during-restore 防护）
- CHG-009：best-effort 多文件事务，失败时补偿已应用文件
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
import unittest
from pathlib import Path

from deepseek_runtime.change_journal import ChangeJournalStore
from deepseek_runtime.contracts import ContractViolation, ErrorCode
from deepseek_runtime.security import (
    ChangeManager,
    ChangeSet,
    Decision,
    FileChange,
    PermissionPolicy,
    PermissionRule,
    Risk,
    WorkspaceSandbox,
    content_sha256,
)


class ChangeManagerM3Tests(unittest.TestCase):
    @staticmethod
    def _manager(
        workspace: Path,
        store: ChangeJournalStore,
        *,
        clock=lambda: 100.0,
    ) -> ChangeManager:
        policy = PermissionPolicy([PermissionRule(Risk.WRITE, Decision.ALLOW)])
        return ChangeManager(
            WorkspaceSandbox(workspace, policy),
            policy,
            journal_store=store,
            clock=clock,
        )

    def test_duplicate_path_in_change_set_is_rejected(self) -> None:
        """CHG-003：同一 change_set 内重复路径被拒绝。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("old", encoding="utf-8")
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))

            # 两个变更指向同一路径（不同 relative 但解析到同一文件）
            with self.assertRaises(ContractViolation) as raised:
                manager.apply(
                    ChangeSet(
                        (
                            FileChange("a.txt", content_sha256(b"old"), "new-1"),
                            FileChange("a.txt", content_sha256(b"old"), "new-2"),
                        )
                    )
                )
            self.assertEqual(raised.exception.error.code, ErrorCode.CHANGE_CONFLICT)
            # 文件未被修改
            self.assertEqual(target.read_text(encoding="utf-8"), "old")

    def test_concurrent_apply_is_serialized(self) -> None:
        """CHG-004：并发 apply 同一实例被进程内锁串行化，无竞争损坏。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("old", encoding="utf-8")
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))

            errors: list[BaseException] = []
            barrier = threading.Barrier(2)

            def worker(content: str) -> None:
                try:
                    barrier.wait()
                    manager.apply(
                        ChangeSet((FileChange("a.txt", content_sha256(b"old"), content),))
                    )
                except BaseException as exc:  # noqa: BLE001
                    errors.append(exc)

            threads = [threading.Thread(target=worker, args=(f"new-{i}",)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 可能有一个成功、一个因 stale hash 失败，但绝不能出现损坏内容
            content = target.read_text(encoding="utf-8")
            self.assertIn(content, {"new-0", "new-1"})
            # 无未处理的并发异常（stale hash 会被捕获为 ValueError）
            for err in errors:
                self.assertIsInstance(err, ValueError)  # stale original hash

    def test_mode_metadata_is_preserved(self) -> None:
        """CHG-006：文件 mode 在 apply 和 rollback 后保留。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("old", encoding="utf-8")
            if os.name != "nt":
                target.chmod(0o640)
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))

            handle = manager.apply(ChangeSet((FileChange("a.txt", content_sha256(b"old"), "new"),)))
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(target.read_text(encoding="utf-8"), "new")

            manager.rollback(handle)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(target.read_text(encoding="utf-8"), "old")

    def test_multi_file_best_effort_rolls_back_on_failure(self) -> None:
        """CHG-009：多文件事务是 best-effort，中途失败时补偿已应用文件。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            first = workspace / "first.txt"
            first.write_text("old-1", encoding="utf-8")

            # 第二个变更指向一个 stale hash（内容已变），apply 应整体失败
            second = workspace / "second.txt"
            second.write_text("old-2", encoding="utf-8")

            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))

            with self.assertRaises(ValueError):
                manager.apply(
                    ChangeSet(
                        (
                            FileChange("first.txt", content_sha256(b"old-1"), "new-1"),
                            FileChange("second.txt", content_sha256(b"WRONG"), "new-2"),
                        )
                    )
                )
            # best-effort：校验阶段失败，两个文件都不应被修改
            self.assertEqual(first.read_text(encoding="utf-8"), "old-1")
            self.assertEqual(second.read_text(encoding="utf-8"), "old-2")

    def test_apply_failure_after_partial_write_restores_originals(self) -> None:
        """CHG-009：写入中途失败时，已应用文件被补偿回原始内容。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            first = workspace / "first.txt"
            first.write_text("old-1", encoding="utf-8")

            def failing_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
                # 第一次调用（第一个文件）成功，第二次失败
                if Path(dst).name == "second.txt":
                    raise OSError("simulated write failure")
                os.replace(src, dst)

            policy = PermissionPolicy([PermissionRule(Risk.WRITE, Decision.ALLOW)])
            manager = ChangeManager(
                WorkspaceSandbox(workspace, policy),
                policy,
                replace=failing_replace,
                journal_store=ChangeJournalStore(base / "journal"),
                clock=lambda: 100.0,
            )

            with self.assertRaises(OSError):
                manager.apply(
                    ChangeSet(
                        (
                            FileChange("first.txt", content_sha256(b"old-1"), "new-1"),
                            FileChange("second.txt", None, "new-2"),
                        )
                    )
                )
            # 第一个文件已写入 new-1，第二个失败，应补偿回 old-1
            self.assertEqual(first.read_text(encoding="utf-8"), "old-1")
            self.assertFalse((workspace / "second.txt").exists())

    def test_audit_events_are_content_free_and_structured(self) -> None:
        """CHG-008：audit 事件只含路径/ID，不含文件正文。"""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("original-secret", encoding="utf-8")
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))
            handle = manager.apply(
                ChangeSet((FileChange("a.txt", content_sha256(b"original-secret"), "new-secret"),))
            )
            manager.rollback(handle)
            audit = json.dumps(manager.audit_events)
            self.assertNotIn("original-secret", audit)
            self.assertNotIn("new-secret", audit)
            # 事件包含结构化字段
            self.assertIn("changeset_applied", audit)
            self.assertIn("changeset_rolled_back", audit)


if __name__ == "__main__":
    unittest.main()