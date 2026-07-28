"""Workspace path containment and no-follow filesystem access."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from pathlib import Path


class WorkspaceViolation(ValueError):
    """A requested path or filesystem entry violates workspace containment."""


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
            raise WorkspaceViolation(f"workspace links are not followed: {self.relative_lexical(path)}")

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
                raise WorkspaceViolation("workspace path does not exist")
            return candidate

        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise WorkspaceViolation("workspace path cannot be resolved") from exc
        self._assert_contained(resolved)
        final_stat = candidate.lstat()
        self._assert_plain_entry(candidate, final_stat)
        return resolved

    def relative(self, path: str | Path) -> str:
        resolved = self.resolve(path, must_exist=False)
        return resolved.relative_to(self.root).as_posix()

    def iter_files(self, *, excluded_names: frozenset[str] = frozenset({".git"})) -> Iterator[Path]:
        """Yield contained regular files without following directory entries."""

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

    def read_text(self, raw: str | Path, *, encoding: str = "utf-8", max_chars: int | None = None) -> str:
        """Read a regular contained file through a no-follow descriptor."""

        path = self.resolve(raw, must_exist=True)
        before = path.lstat()
        self._assert_plain_entry(path, before)
        if not stat.S_ISREG(before.st_mode):
            raise WorkspaceViolation("workspace path is not a regular file")

        flags = os.O_RDONLY | int(getattr(os, "O_BINARY", 0)) | int(getattr(os, "O_NOFOLLOW", 0))
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise WorkspaceViolation("workspace file cannot be opened safely") from exc

        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise WorkspaceViolation("workspace path is not a regular file")
            before_identity = (getattr(before, "st_dev", None), getattr(before, "st_ino", None))
            opened_identity = (getattr(opened, "st_dev", None), getattr(opened, "st_ino", None))
            if all(item not in (None, 0) for item in before_identity + opened_identity):
                if before_identity != opened_identity:
                    raise WorkspaceViolation("workspace file changed during open")
            with os.fdopen(descriptor, "r", encoding=encoding) as handle:
                descriptor = -1
                return handle.read() if max_chars is None else handle.read(max_chars)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
