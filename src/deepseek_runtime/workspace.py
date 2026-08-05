"""Workspace containment plus bounded, structured no-follow file access."""

from __future__ import annotations

import math
import os
import stat
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class WorkspaceViolation(ValueError):
    """A requested path or filesystem entry violates workspace containment."""


class WorkspacePathMissing(WorkspaceViolation):
    """A contained path disappeared or did not exist when it was inspected."""


@dataclass(frozen=True)
class WorkspaceReadResult:
    """Content-minimized result for one bounded workspace read."""

    status: str
    path: str
    content: str = ""
    bytes_read: int = 0
    file_bytes: int | None = None
    truncated: bool = False
    error_code: str | None = None

    @property
    def readable(self) -> bool:
        return self.status in {"ok", "truncated"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": self.path,
            "content": self.content,
            "bytes_read": self.bytes_read,
            "file_bytes": self.file_bytes,
            "truncated": self.truncated,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class WorkspaceSearchBudgets:
    """Hard budgets for one workspace search operation."""

    max_files: int = 20_000
    max_bytes: int = 10_000_000
    max_seconds: float = 5.0
    max_matches: int = 100
    max_file_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        integer_fields = {
            "max_files": self.max_files,
            "max_bytes": self.max_bytes,
            "max_matches": self.max_matches,
            "max_file_bytes": self.max_file_bytes,
        }
        for name, value in integer_fields.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            not isinstance(self.max_seconds, (int, float))
            or isinstance(self.max_seconds, bool)
            or not math.isfinite(float(self.max_seconds))
            or self.max_seconds <= 0
        ):
            raise ValueError("max_seconds must be finite and positive")


@dataclass(frozen=True)
class WorkspaceSearchResult:
    """Structured result for a bounded workspace search."""

    status: str
    matches: list[dict[str, object]] = field(default_factory=list)
    files_scanned: int = 0
    bytes_scanned: int = 0
    elapsed_ms: int = 0
    truncated: bool = False
    stop_reason: str | None = None
    skipped: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matches": [dict(item) for item in self.matches],
            "files_scanned": self.files_scanned,
            "bytes_scanned": self.bytes_scanned,
            "elapsed_ms": self.elapsed_ms,
            "truncated": self.truncated,
            "stop_reason": self.stop_reason,
            "skipped": dict(self.skipped),
        }


class WorkspaceResolver:
    """Resolve and traverse workspace paths without following links.

    The Alpha boundary protects against untrusted model input and untrusted
    workspace contents. It does not claim to defeat a malicious concurrent
    process with the same host permissions.
    """

    def __init__(self, root: str | Path):
        resolved = Path(root).expanduser().resolve(strict=True)
        if not resolved.is_dir():
            raise WorkspaceViolation("workspace root must be an existing directory")
        self.root = resolved

    @staticmethod
    def is_reparse_stat(value: os.stat_result) -> bool:
        attributes = int(getattr(value, "st_file_attributes", 0))
        flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        return bool(flag and attributes & flag)

    def _assert_contained(self, path: Path) -> None:
        if path != self.root and self.root not in path.parents:
            raise WorkspaceViolation("path escapes workspace")

    def _assert_plain_entry(self, path: Path, value: os.stat_result) -> None:
        if stat.S_ISLNK(value.st_mode) or self.is_reparse_stat(value):
            raise WorkspaceViolation(
                f"workspace links are not followed: {self.relative_lexical(path)}"
            )

    def _lexical_candidate(self, raw: str | Path) -> Path:
        raw_text = os.fspath(raw)
        if "\x00" in raw_text:
            raise WorkspaceViolation("workspace path contains NUL")
        requested = Path(raw_text).expanduser()
        candidate = requested if requested.is_absolute() else self.root / requested
        normalized = Path(os.path.abspath(os.path.normpath(os.fspath(candidate))))
        self._assert_contained(normalized)
        return normalized

    def relative_lexical(self, path: str | Path) -> str:
        candidate = self._lexical_candidate(path)
        return candidate.relative_to(self.root).as_posix()

    def resolve(self, raw: str | Path, *, must_exist: bool = False) -> Path:
        """Return a contained absolute path while rejecting links/reparse points.

        Missing trailing components are permitted when ``must_exist`` is false,
        which keeps secure create/write workflows possible. Every existing
        ancestor is inspected with ``lstat`` before the path is returned.
        """

        candidate = self._lexical_candidate(raw)
        relative = candidate.relative_to(self.root)
        current = self.root
        missing = False

        for index, part in enumerate(relative.parts):
            current = current / part
            if missing:
                continue
            try:
                current_stat = current.lstat()
            except FileNotFoundError:
                missing = True
                continue
            except OSError as exc:
                raise WorkspaceViolation("workspace path cannot be inspected") from exc
            self._assert_plain_entry(current, current_stat)
            if index < len(relative.parts) - 1 and not stat.S_ISDIR(current_stat.st_mode):
                raise WorkspaceViolation("workspace ancestor is not a directory")

        if missing:
            if must_exist:
                raise WorkspacePathMissing("workspace path does not exist")
            return candidate

        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise WorkspacePathMissing("workspace path disappeared during resolution") from exc
        except OSError as exc:
            raise WorkspaceViolation("workspace path cannot be resolved") from exc
        self._assert_contained(resolved)
        try:
            final_stat = candidate.lstat()
        except FileNotFoundError as exc:
            raise WorkspacePathMissing("workspace path disappeared during inspection") from exc
        self._assert_plain_entry(candidate, final_stat)
        return resolved

    def relative(self, path: str | Path) -> str:
        resolved = self.resolve(path, must_exist=False)
        return resolved.relative_to(self.root).as_posix()

    def iter_files(
        self,
        *,
        excluded_names: frozenset[str] = frozenset({".git"}),
    ) -> Iterator[Path]:
        """Yield contained regular files without following directory entries.

        This compatibility iterator preserves its original skip-on-I/O behavior.
        Production bounded search uses :meth:`search_text`, which records those
        outcomes structurally rather than silently discarding them.
        """

        stack = [self.root]
        while stack:
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if entry.name in excluded_names:
                            continue
                        try:
                            entry_stat = entry.stat(follow_symlinks=False)
                        except OSError:
                            continue
                        if stat.S_ISLNK(entry_stat.st_mode) or self.is_reparse_stat(entry_stat):
                            continue
                        entry_path = Path(entry.path)
                        if stat.S_ISDIR(entry_stat.st_mode):
                            try:
                                stack.append(self.resolve(entry_path, must_exist=True))
                            except WorkspaceViolation:
                                continue
                        elif stat.S_ISREG(entry_stat.st_mode):
                            try:
                                yield self.resolve(entry_path, must_exist=True)
                            except WorkspaceViolation:
                                continue
            except OSError:
                continue

    @staticmethod
    def _read_status(
        *,
        status: str,
        path: str,
        file_bytes: int | None = None,
        error_code: str | None = None,
    ) -> WorkspaceReadResult:
        return WorkspaceReadResult(
            status=status,
            path=path,
            file_bytes=file_bytes,
            error_code=error_code,
        )

    def read_bounded(
        self,
        raw: str | Path,
        *,
        max_bytes: int,
        encoding: str = "utf-8",
    ) -> WorkspaceReadResult:
        """Read at most ``max_bytes`` and return a stable structured result.

        Containment, traversal, link, reparse-point, and non-regular-file failures
        remain security exceptions. Ordinary file-system races and unsupported
        content are returned as content-minimized statuses.
        """

        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        relative = self.relative_lexical(raw)
        try:
            path = self.resolve(raw, must_exist=True)
        except WorkspacePathMissing:
            return self._read_status(
                status="disappeared",
                path=relative,
                error_code="WORKSPACE_FILE_DISAPPEARED",
            )

        try:
            before = path.lstat()
        except FileNotFoundError:
            return self._read_status(
                status="disappeared",
                path=relative,
                error_code="WORKSPACE_FILE_DISAPPEARED",
            )
        self._assert_plain_entry(path, before)
        if not stat.S_ISREG(before.st_mode):
            raise WorkspaceViolation("workspace path is not a regular file")

        flags = (
            os.O_RDONLY
            | int(getattr(os, "O_BINARY", 0))
            | int(getattr(os, "O_NOFOLLOW", 0))
        )
        try:
            descriptor = os.open(path, flags)
        except PermissionError:
            return self._read_status(
                status="permission-denied",
                path=relative,
                file_bytes=before.st_size,
                error_code="WORKSPACE_PERMISSION_DENIED",
            )
        except FileNotFoundError:
            return self._read_status(
                status="disappeared",
                path=relative,
                file_bytes=before.st_size,
                error_code="WORKSPACE_FILE_DISAPPEARED",
            )
        except OSError:
            return self._read_status(
                status="io-error",
                path=relative,
                file_bytes=before.st_size,
                error_code="WORKSPACE_IO_ERROR",
            )

        try:
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode):
                    raise WorkspaceViolation("workspace path is not a regular file")
                before_identity = (
                    getattr(before, "st_dev", None),
                    getattr(before, "st_ino", None),
                )
                opened_identity = (
                    getattr(opened, "st_dev", None),
                    getattr(opened, "st_ino", None),
                )
                if all(
                    item not in (None, 0)
                    for item in before_identity + opened_identity
                ) and before_identity != opened_identity:
                    raise WorkspaceViolation("workspace file changed during open")

                chunks: list[bytes] = []
                remaining = max_bytes + 1
                while remaining > 0:
                    chunk = os.read(descriptor, min(65_536, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                observed = b"".join(chunks)
            except PermissionError:
                return self._read_status(
                    status="permission-denied",
                    path=relative,
                    file_bytes=before.st_size,
                    error_code="WORKSPACE_PERMISSION_DENIED",
                )
            except FileNotFoundError:
                return self._read_status(
                    status="disappeared",
                    path=relative,
                    file_bytes=before.st_size,
                    error_code="WORKSPACE_FILE_DISAPPEARED",
                )
            except WorkspaceViolation:
                raise
            except OSError:
                return self._read_status(
                    status="io-error",
                    path=relative,
                    file_bytes=before.st_size,
                    error_code="WORKSPACE_IO_ERROR",
                )
        finally:
            os.close(descriptor)

        truncated = len(observed) > max_bytes or opened.st_size > max_bytes
        prefix = observed[:max_bytes]
        if b"\x00" in prefix:
            return WorkspaceReadResult(
                status="binary",
                path=relative,
                bytes_read=len(prefix),
                file_bytes=opened.st_size,
                truncated=truncated,
                error_code="WORKSPACE_BINARY_FILE",
            )

        try:
            content = prefix.decode(encoding, errors="strict")
        except UnicodeDecodeError as exc:
            cut_at_boundary = (
                truncated
                and exc.reason == "unexpected end of data"
                and exc.end == len(prefix)
            )
            if not cut_at_boundary:
                return WorkspaceReadResult(
                    status="binary",
                    path=relative,
                    bytes_read=len(prefix),
                    file_bytes=opened.st_size,
                    truncated=truncated,
                    error_code="WORKSPACE_BINARY_FILE",
                )
            content = prefix[: exc.start].decode(encoding, errors="strict")

        return WorkspaceReadResult(
            status="truncated" if truncated else "ok",
            path=relative,
            content=content,
            bytes_read=len(prefix),
            file_bytes=opened.st_size,
            truncated=truncated,
        )

    def search_text(
        self,
        needle: str,
        *,
        budgets: WorkspaceSearchBudgets | None = None,
        excluded_names: frozenset[str] = frozenset({".git"}),
        clock: Callable[[], float] = time.monotonic,
    ) -> WorkspaceSearchResult:
        """Search text files while enforcing file, byte, time, and match budgets."""

        if not isinstance(needle, str) or not needle:
            raise ValueError("search input must not be empty")
        active = budgets or WorkspaceSearchBudgets()
        if not isinstance(active, WorkspaceSearchBudgets):
            raise TypeError("budgets must be WorkspaceSearchBudgets")
        if not callable(clock):
            raise TypeError("clock must be callable")

        started = float(clock())
        stack = [self.root]
        matches: list[dict[str, object]] = []
        files_scanned = 0
        bytes_scanned = 0
        stop_reason: str | None = None
        skipped = {
            "binary": 0,
            "permission-denied": 0,
            "disappeared": 0,
            "io-error": 0,
            "links": 0,
            "non-regular": 0,
            "truncated-files": 0,
        }

        def elapsed() -> float:
            return max(0.0, float(clock()) - started)

        while stack and stop_reason is None:
            if elapsed() >= active.max_seconds:
                stop_reason = "time-limit"
                break
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if elapsed() >= active.max_seconds:
                            stop_reason = "time-limit"
                            break
                        if entry.name in excluded_names:
                            continue
                        try:
                            entry_stat = entry.stat(follow_symlinks=False)
                        except PermissionError:
                            skipped["permission-denied"] += 1
                            continue
                        except FileNotFoundError:
                            skipped["disappeared"] += 1
                            continue
                        except OSError:
                            skipped["io-error"] += 1
                            continue

                        if stat.S_ISLNK(entry_stat.st_mode) or self.is_reparse_stat(entry_stat):
                            skipped["links"] += 1
                            continue
                        entry_path = Path(entry.path)
                        if stat.S_ISDIR(entry_stat.st_mode):
                            try:
                                stack.append(self.resolve(entry_path, must_exist=True))
                            except WorkspacePathMissing:
                                skipped["disappeared"] += 1
                            except WorkspaceViolation:
                                skipped["io-error"] += 1
                            continue
                        if not stat.S_ISREG(entry_stat.st_mode):
                            skipped["non-regular"] += 1
                            continue
                        if files_scanned >= active.max_files:
                            stop_reason = "file-limit"
                            break
                        if bytes_scanned >= active.max_bytes:
                            stop_reason = "byte-limit"
                            break

                        remaining_bytes = active.max_bytes - bytes_scanned
                        read_limit = min(active.max_file_bytes, remaining_bytes)
                        files_scanned += 1
                        try:
                            result = self.read_bounded(entry_path, max_bytes=read_limit)
                        except WorkspacePathMissing:
                            skipped["disappeared"] += 1
                            continue
                        bytes_scanned += result.bytes_read
                        if elapsed() >= active.max_seconds:
                            stop_reason = "time-limit"
                            break

                        if result.status in skipped:
                            skipped[result.status] += 1
                            continue
                        if not result.readable:
                            skipped["io-error"] += 1
                            continue
                        if result.truncated:
                            skipped["truncated-files"] += 1

                        for number, line in enumerate(result.content.splitlines(), 1):
                            if needle not in line:
                                continue
                            matches.append(
                                {
                                    "path": result.path,
                                    "line": number,
                                    "text": line[:200],
                                }
                            )
                            if len(matches) >= active.max_matches:
                                stop_reason = "match-limit"
                                break
                        if stop_reason is not None:
                            break
                        if bytes_scanned >= active.max_bytes:
                            stop_reason = "byte-limit"
                            break
            except PermissionError:
                skipped["permission-denied"] += 1
            except FileNotFoundError:
                skipped["disappeared"] += 1
            except OSError:
                skipped["io-error"] += 1

        elapsed_ms = int(elapsed() * 1000)
        return WorkspaceSearchResult(
            status="budget-exhausted" if stop_reason is not None else "ok",
            matches=matches,
            files_scanned=files_scanned,
            bytes_scanned=bytes_scanned,
            elapsed_ms=elapsed_ms,
            truncated=stop_reason is not None,
            stop_reason=stop_reason,
            skipped=skipped,
        )

    def read_text(
        self,
        raw: str | Path,
        *,
        encoding: str = "utf-8",
        max_chars: int | None = None,
    ) -> str:
        """Compatibility text reader with the original character-limit contract."""

        path = self.resolve(raw, must_exist=True)
        before = path.lstat()
        self._assert_plain_entry(path, before)
        if not stat.S_ISREG(before.st_mode):
            raise WorkspaceViolation("workspace path is not a regular file")

        flags = (
            os.O_RDONLY
            | int(getattr(os, "O_BINARY", 0))
            | int(getattr(os, "O_NOFOLLOW", 0))
        )
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise WorkspaceViolation("workspace file cannot be opened safely") from exc

        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise WorkspaceViolation("workspace path is not a regular file")
            before_identity = (
                getattr(before, "st_dev", None),
                getattr(before, "st_ino", None),
            )
            opened_identity = (
                getattr(opened, "st_dev", None),
                getattr(opened, "st_ino", None),
            )
            if all(
                item not in (None, 0)
                for item in before_identity + opened_identity
            ) and before_identity != opened_identity:
                raise WorkspaceViolation("workspace file changed during open")
            with os.fdopen(descriptor, "r", encoding=encoding) as handle:
                descriptor = -1
                return handle.read() if max_chars is None else handle.read(max_chars)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
