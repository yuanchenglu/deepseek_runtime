"""Durable private storage for opaque rollback handles."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from .contracts import (
    ChangeJournalEntry,
    ContractViolation,
    ErrorCode,
    RollbackHandle,
    RuntimeErrorInfo,
)


def workspace_identity(root: str | Path) -> str:
    resolved = Path(root).resolve(strict=True)
    return hashlib.sha256(os.fsencode(resolved)).hexdigest()


def default_change_journal_dir() -> Path:
    configured = os.environ.get("DEEPSEEK_RUNTIME_STATE_DIR")
    base = Path(configured).expanduser() if configured else Path.home() / ".deepseek-runtime" / "state"
    return base / "change-journal"


class ChangeJournalStore:
    """Atomic owner-only JSON store for private rollback journal entries."""

    def __init__(self, root: str | Path | None = None, *, clock: Callable[[], float] = time.time):
        self.root = Path(root) if root is not None else default_change_journal_dir()
        self.clock = clock
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._chmod(self.root, 0o700)

    @staticmethod
    def _chmod(path: Path, mode: int) -> None:
        try:
            path.chmod(mode)
        except OSError:
            pass

    @staticmethod
    def _invalid(message: str, *, cause: BaseException | None = None) -> ContractViolation:
        return ContractViolation(
            RuntimeErrorInfo(
                ErrorCode.ROLLBACK_HANDLE_INVALID,
                message,
                cause_class=type(cause).__name__ if cause is not None else None,
            )
        )

    def _path(self, handle: RollbackHandle) -> Path:
        if not isinstance(handle, RollbackHandle):
            raise self._invalid("rollback handle type is invalid")
        return self.root / f"{handle.handle_id}.json"

    def save(self, entry: ChangeJournalEntry) -> None:
        entry.validate()
        target = self.root / f"{entry.handle_id}.json"
        payload = json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        descriptor, temp_name = tempfile.mkstemp(prefix=".journal-", suffix=".tmp", dir=self.root)
        temp_path = Path(temp_name)
        try:
            try:
                os.fchmod(descriptor, 0o600)
            except OSError:
                pass
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
            self._chmod(target, 0o600)
            self._fsync_directory()
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temp_path.unlink(missing_ok=True)

    def load(self, handle: RollbackHandle) -> ChangeJournalEntry:
        path = self._path(handle)
        try:
            if path.is_symlink():
                raise self._invalid("rollback journal entry is a symbolic link")
            flags = os.O_RDONLY | int(getattr(os, "O_BINARY", 0)) | int(getattr(os, "O_NOFOLLOW", 0))
            descriptor = os.open(path, flags)
            try:
                with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
                    descriptor = -1
                    value = json.load(stream)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
            if not isinstance(value, dict):
                raise ValueError("journal root must be an object")
            entry = ChangeJournalEntry.from_dict(value)
        except ContractViolation:
            raise
        except (FileNotFoundError, KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
            raise self._invalid("rollback handle does not resolve to a valid journal entry", cause=exc) from exc
        if entry.handle_id != handle.handle_id:
            raise self._invalid("rollback journal handle binding is invalid")
        return entry

    def delete(self, handle: RollbackHandle) -> None:
        self._path(handle).unlink(missing_ok=True)
        self._fsync_directory()

    def mark_consumed(self, entry: ChangeJournalEntry) -> None:
        entry.consumed = True
        self.save(entry)

    def cleanup_expired(self) -> int:
        removed = 0
        now = int(self.clock())
        for path in self.root.glob("*.json"):
            try:
                handle = RollbackHandle(path.stem)
                entry = self.load(handle)
                if entry.expires_at_unix <= now:
                    path.unlink(missing_ok=True)
                    removed += 1
            except (ContractViolation, ValueError, OSError):
                continue
        if removed:
            self._fsync_directory()
        return removed

    def _fsync_directory(self) -> None:
        if os.name == "nt":
            return
        try:
            descriptor = os.open(self.root, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
