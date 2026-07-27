from __future__ import annotations

from pathlib import Path


NEW_CHANGE_MANAGER = '''# Backward-compatible name only. The production authority is the opaque handle ID;
# callers cannot supply paths or original bytes.
RollbackToken = RollbackHandle


# ===== ChangeManager（变更管理器）=====

class ChangeManager:
    """文件变更管理器：预览 → 持久化 Journal → 应用 → 受约束回滚。"""

    def __init__(
        self,
        sandbox: WorkspaceSandbox,
        policy: PermissionPolicy | None = None,
        replace: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
        journal_store: ChangeJournalStore | None = None,
        clock: Callable[[], float] = time.time,
        journal_ttl_seconds: int = 7 * 24 * 60 * 60,
    ):
        if journal_ttl_seconds <= 0:
            raise ValueError("journal_ttl_seconds must be positive")
        self.sandbox = sandbox
        self.policy = policy or sandbox.policy
        self.replace = replace
        self.clock = clock
        self.journal_ttl_seconds = journal_ttl_seconds
        self.workspace_id = workspace_identity(sandbox.root)
        self.journal_store = journal_store or ChangeJournalStore(clock=clock)
        self.journal_store.cleanup_expired()
        self.audit_events: list[dict[str, object]] = []

    @staticmethod
    def _contract_error(code: ErrorCode, message: str, **details: object) -> ContractViolation:
        return ContractViolation(RuntimeErrorInfo(code, message, details=details))

    def _current(self, path: Path) -> bytes | None:
        return path.read_bytes() if path.exists() else None

    @staticmethod
    def _mode(path: Path) -> int | None:
        try:
            return stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
        except FileNotFoundError:
            return None

    def _validate(self, change: FileChange) -> tuple[Path, bytes | None, int | None]:
        path = self.sandbox.resolve(change.path)
        current = self._current(path)
        if change.original_sha256 is None:
            if current is not None:
                raise ValueError(f"expected new file but path exists: {change.path}")
        elif current is None or content_sha256(current) != change.original_sha256:
            raise ValueError(f"stale original hash: {change.path}")
        decision = self.policy.decide(PermissionRequest(Risk.WRITE, self.sandbox.relative(path)))
        if decision is not Decision.ALLOW:
            raise PermissionDenied(f"write requires {decision.value}: {change.path}")
        return path, current, self._mode(path)

    def preview(self, change_set: ChangeSet) -> str:
        chunks: list[str] = []
        for change in change_set.changes:
            path = self.sandbox.resolve(change.path)
            current = self._current(path)
            before = (current or b"").decode("utf-8", errors="replace").splitlines(keepends=True)
            after = change.new_content.splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=f"a/{change.path}",
                    tofile=f"b/{change.path}",
                )
            )
        return "".join(chunks)

    def _write_bytes(self, path: Path, content: bytes, mode: int | None = None, *, suffix: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.{suffix}", dir=path.parent)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            self.replace(temp, path)
            if mode is not None:
                try:
                    path.chmod(mode)
                except OSError:
                    pass
        finally:
            temp.unlink(missing_ok=True)

    def _restore_originals(self, originals: dict[Path, tuple[bytes | None, int | None]]) -> None:
        for path, (content, mode) in originals.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                self._write_bytes(path, content, mode, suffix="rollback.")

    def apply(self, change_set: ChangeSet) -> RollbackHandle:
        """Persist private recovery state before applying a validated change set."""
        validated = [(*self._validate(change), change) for change in change_set.changes]
        handle = RollbackHandle.issue()
        now = int(self.clock())
        records = [
            JournalFileRecord(
                relative_path=self.sandbox.relative(path),
                original_sha256=content_sha256(current) if current is not None else None,
                post_sha256=content_sha256(change.new_content.encode("utf-8")),
                original_content_b64=(base64.b64encode(current).decode("ascii") if current is not None else None),
                original_mode=mode,
            )
            for path, current, mode, change in validated
        ]
        entry = ChangeJournalEntry(
            handle_id=handle.handle_id,
            workspace_id=self.workspace_id,
            change_set_id=change_set.change_set_id,
            files=records,
            created_at_unix=now,
            expires_at_unix=now + self.journal_ttl_seconds,
        )
        self.journal_store.save(entry)

        originals = {path: (current, mode) for path, current, mode, _ in validated}
        applied: list[Path] = []
        try:
            for path, _, mode, change in validated:
                self._write_bytes(path, change.new_content.encode("utf-8"), mode)
                applied.append(path)
            self.audit_events.append(
                {
                    "event": "changeset_applied",
                    "change_set_id": change_set.change_set_id,
                    "handle_id": handle.handle_id,
                    "paths": [self.sandbox.relative(path) for path in applied],
                }
            )
            return handle
        except Exception:
            self._restore_originals({path: originals[path] for path in applied})
            self.journal_store.delete(handle)
            self.audit_events.append(
                {
                    "event": "changeset_apply_failed_rolled_back",
                    "change_set_id": change_set.change_set_id,
                    "paths": [self.sandbox.relative(path) for path in applied],
                }
            )
            raise

    @staticmethod
    def _decode_original(record: JournalFileRecord) -> bytes | None:
        if record.original_sha256 is None:
            if record.original_content_b64 is not None:
                raise ValueError("new-file journal record contains original content")
            return None
        if record.original_content_b64 is None:
            raise ValueError("existing-file journal record lacks original content")
        value = base64.b64decode(record.original_content_b64.encode("ascii"), validate=True)
        if content_sha256(value) != record.original_sha256:
            raise ValueError("journal original content hash mismatch")
        return value

    def rollback(self, handle: RollbackHandle) -> None:
        """Resolve an opaque handle and restore only its protected journal entry."""
        try:
            entry = self.journal_store.load(handle)
        except ContractViolation:
            raise
        except Exception as exc:
            raise self._contract_error(
                ErrorCode.ROLLBACK_HANDLE_INVALID,
                "rollback handle cannot be resolved",
                cause_class=type(exc).__name__,
            ) from exc

        now = int(self.clock())
        if entry.consumed:
            raise self._contract_error(ErrorCode.ROLLBACK_HANDLE_INVALID, "rollback handle already consumed")
        if entry.expires_at_unix <= now:
            raise self._contract_error(ErrorCode.ROLLBACK_HANDLE_EXPIRED, "rollback handle expired")
        if entry.workspace_id != self.workspace_id:
            raise self._contract_error(
                ErrorCode.ROLLBACK_WORKSPACE_MISMATCH,
                "rollback handle belongs to a different workspace",
            )

        prepared: list[tuple[Path, bytes | None, int | None, str]] = []
        try:
            for record in entry.files:
                path = self.sandbox.resolve(record.relative_path)
                current = self._current(path)
                if current is None or content_sha256(current) != record.post_sha256:
                    raise self._contract_error(
                        ErrorCode.ROLLBACK_CONFLICT,
                        "workspace content changed after apply",
                        path=record.relative_path,
                    )
                decision = self.policy.decide(PermissionRequest(Risk.WRITE, record.relative_path))
                if decision is not Decision.ALLOW:
                    raise PermissionDenied(f"rollback write requires {decision.value}: {record.relative_path}")
                prepared.append((path, self._decode_original(record), record.original_mode, record.relative_path))
        except ContractViolation:
            raise
        except (ValueError, OSError) as exc:
            raise self._contract_error(
                ErrorCode.ROLLBACK_HANDLE_INVALID,
                "rollback journal entry is invalid",
                cause_class=type(exc).__name__,
            ) from exc

        restored: list[str] = []
        for path, original, mode, relative_path in prepared:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                self._write_bytes(path, original, mode, suffix="rollback.")
            restored.append(relative_path)

        self.journal_store.mark_consumed(entry)
        object.__setattr__(handle, "consumed", True)
        self.audit_events.append(
            {
                "event": "changeset_rolled_back",
                "change_set_id": entry.change_set_id,
                "handle_id": handle.handle_id,
                "paths": restored,
            }
        )
'''


def replace_once(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if before not in text:
        raise RuntimeError(f"migration source not found: {path}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def main() -> None:
    security = Path("src/deepseek_runtime/security.py")
    text = security.read_text(encoding="utf-8")
    text = text.replace("import difflib\n", "import base64\nimport difflib\n", 1)
    text = text.replace("import subprocess\n", "import stat\nimport subprocess\n", 1)
    text = text.replace("import tempfile\n", "import tempfile\nimport time\n", 1)
    text = text.replace(
        "from .workspace import WorkspaceResolver, WorkspaceViolation\n",
        "from .change_journal import ChangeJournalStore, workspace_identity\n"
        "from .contracts import (\n"
        "    ChangeJournalEntry,\n"
        "    ContractViolation,\n"
        "    ErrorCode,\n"
        "    JournalFileRecord,\n"
        "    RollbackHandle,\n"
        "    RuntimeErrorInfo,\n"
        ")\n"
        "from .workspace import WorkspaceResolver, WorkspaceViolation\n",
        1,
    )
    start = text.index("@dataclass\nclass RollbackToken:")
    text = text[:start] + NEW_CHANGE_MANAGER
    security.write_text(text, encoding="utf-8")

    journal = Path("src/deepseek_runtime/contracts/journal.py")
    journal_text = journal.read_text(encoding="utf-8")
    journal_text = journal_text.replace("from dataclasses import dataclass\n", "from dataclasses import dataclass, field\n", 1)
    journal_text = journal_text.replace(
        "    schema_version: str = CHANGE_JOURNAL_SCHEMA_VERSION\n\n    def __post_init__",
        "    schema_version: str = CHANGE_JOURNAL_SCHEMA_VERSION\n"
        "    consumed: bool = field(default=False, compare=False, repr=False)\n\n"
        "    def __post_init__",
        1,
    )
    journal.write_text(journal_text, encoding="utf-8")

    package = Path("src/deepseek_runtime/__init__.py")
    package_text = package.read_text(encoding="utf-8")
    package_text = package_text.replace(
        "from .client import DeepSeekClient, ProviderResult, RuntimeSettings\n",
        "from .change_journal import ChangeJournalStore, default_change_journal_dir, workspace_identity\n"
        "from .client import DeepSeekClient, ProviderResult, RuntimeSettings\n",
        1,
    )
    package_text = package_text.replace(
        '    "ChangeJournalEntry",\n',
        '    "ChangeJournalEntry",\n    "ChangeJournalStore",\n',
        1,
    )
    package_text = package_text.replace(
        '    "content_sha256",\n',
        '    "content_sha256",\n    "default_change_journal_dir",\n',
        1,
    )
    package_text = package_text.replace(
        '    "validate_transition",\n',
        '    "validate_transition",\n    "workspace_identity",\n',
        1,
    )
    package.write_text(package_text, encoding="utf-8")

    Path(__file__).unlink()


if __name__ == "__main__":
    main()
