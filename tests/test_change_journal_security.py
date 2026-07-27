from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from deepseek_runtime.change_journal import ChangeJournalStore
from deepseek_runtime.contracts import ContractViolation, ErrorCode, RollbackHandle
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


class ChangeJournalSecurityTests(unittest.TestCase):
    @staticmethod
    def _manager(
        workspace: Path,
        store: ChangeJournalStore,
        *,
        clock=lambda: 100.0,
        ttl: int = 100,
    ) -> ChangeManager:
        policy = PermissionPolicy([PermissionRule(Risk.WRITE, Decision.ALLOW)])
        return ChangeManager(
            WorkspaceSandbox(workspace, policy),
            policy,
            journal_store=store,
            clock=clock,
            journal_ttl_seconds=ttl,
        )

    def test_apply_returns_opaque_handle_and_restart_manager_can_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            journal = base / "journal"
            workspace.mkdir()
            target = workspace / "notes.txt"
            target.write_bytes(b"old\n")
            store = ChangeJournalStore(journal, clock=lambda: 100.0)
            manager = self._manager(workspace, store)

            handle = manager.apply(
                ChangeSet((FileChange("notes.txt", content_sha256(b"old\n"), "new\n"),))
            )
            self.assertEqual(set(handle.to_dict()), {"schema_version", "handle_id"})
            self.assertNotIn("notes.txt", json.dumps(handle.to_dict()))
            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")

            restarted = self._manager(workspace, ChangeJournalStore(journal, clock=lambda: 100.0))
            restarted.rollback(RollbackHandle(handle.handle_id))
            self.assertEqual(target.read_text(encoding="utf-8"), "old\n")

    def test_forged_handle_and_payload_are_rejected_repeatedly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside-safe", encoding="utf-8")
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))

            class ForgedPayload:
                originals = {outside: b"forged"}

            for _ in range(20):
                with self.assertRaises(ContractViolation) as unknown:
                    manager.rollback(RollbackHandle.issue())
                self.assertEqual(unknown.exception.error.code, ErrorCode.ROLLBACK_HANDLE_INVALID)
                with self.assertRaises(ContractViolation) as payload:
                    manager.rollback(ForgedPayload())  # type: ignore[arg-type]
                self.assertEqual(payload.exception.error.code, ErrorCode.ROLLBACK_HANDLE_INVALID)
                self.assertEqual(outside.read_text(encoding="utf-8"), "outside-safe")

    def test_malicious_journal_path_cannot_target_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside-safe", encoding="utf-8")
            store = ChangeJournalStore(base / "journal", clock=lambda: 100.0)
            manager = self._manager(workspace, store)
            handle = RollbackHandle.issue()
            malicious = {
                "schema_version": "1.0",
                "handle_id": handle.handle_id,
                "workspace_id": manager.workspace_id,
                "change_set_id": "forged-change",
                "files": [
                    {
                        "relative_path": "../outside.txt",
                        "original_sha256": content_sha256(b"forged"),
                        "post_sha256": content_sha256(b"outside-safe"),
                        "original_content_b64": "Zm9yZ2Vk",
                        "original_mode": None,
                    }
                ],
                "created_at_unix": 100,
                "expires_at_unix": 200,
                "consumed": False,
                "protection": "owner-only",
            }
            (store.root / f"{handle.handle_id}.json").write_text(json.dumps(malicious), encoding="utf-8")

            with self.assertRaises(ContractViolation) as raised:
                manager.rollback(handle)
            self.assertEqual(raised.exception.error.code, ErrorCode.ROLLBACK_HANDLE_INVALID)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside-safe")

    def test_cross_workspace_handle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first = base / "first"
            second = base / "second"
            first.mkdir()
            second.mkdir()
            target = first / "a.txt"
            target.write_text("old", encoding="utf-8")
            store = ChangeJournalStore(base / "journal", clock=lambda: 100.0)
            first_manager = self._manager(first, store)
            second_manager = self._manager(second, store)
            handle = first_manager.apply(ChangeSet((FileChange("a.txt", content_sha256(b"old"), "new"),)))

            with self.assertRaises(ContractViolation) as raised:
                second_manager.rollback(handle)
            self.assertEqual(raised.exception.error.code, ErrorCode.ROLLBACK_WORKSPACE_MISMATCH)
            self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_expired_handle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("old", encoding="utf-8")
            now = [100.0]
            clock = lambda: now[0]
            store = ChangeJournalStore(base / "journal", clock=clock)
            manager = self._manager(workspace, store, clock=clock, ttl=1)
            handle = manager.apply(ChangeSet((FileChange("a.txt", content_sha256(b"old"), "new"),)))
            now[0] = 102.0

            with self.assertRaises(ContractViolation) as raised:
                manager.rollback(handle)
            self.assertEqual(raised.exception.error.code, ErrorCode.ROLLBACK_HANDLE_EXPIRED)
            self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_post_change_conflict_prevents_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            target = workspace / "a.txt"
            target.write_text("old", encoding="utf-8")
            manager = self._manager(workspace, ChangeJournalStore(base / "journal"))
            handle = manager.apply(ChangeSet((FileChange("a.txt", content_sha256(b"old"), "new"),)))
            target.write_text("external-edit", encoding="utf-8")

            with self.assertRaises(ContractViolation) as raised:
                manager.rollback(handle)
            self.assertEqual(raised.exception.error.code, ErrorCode.ROLLBACK_CONFLICT)
            self.assertEqual(target.read_text(encoding="utf-8"), "external-edit")

    def test_consumed_handle_cannot_be_reused_and_created_file_is_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            store = ChangeJournalStore(base / "journal")
            manager = self._manager(workspace, store)
            handle = manager.apply(ChangeSet((FileChange("created.txt", None, "created"),)))
            target = workspace / "created.txt"
            self.assertTrue(target.exists())

            manager.rollback(handle)
            self.assertFalse(target.exists())
            self.assertTrue(handle.consumed)
            with self.assertRaises(ContractViolation) as raised:
                manager.rollback(handle)
            self.assertEqual(raised.exception.error.code, ErrorCode.ROLLBACK_HANDLE_INVALID)

    def test_audit_events_do_not_include_file_contents(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
