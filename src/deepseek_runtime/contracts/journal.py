"""Opaque rollback handle and durable ChangeJournal data contract."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Mapping

from .common import CHANGE_JOURNAL_SCHEMA_VERSION

_HANDLE_RE = re.compile(r"^[A-Za-z0-9_-]{32,256}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RollbackHandle:
    handle_id: str
    schema_version: str = CHANGE_JOURNAL_SCHEMA_VERSION
    consumed: bool = field(default=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if self.schema_version != CHANGE_JOURNAL_SCHEMA_VERSION:
            raise ValueError("unsupported rollback handle schema version")
        if not _HANDLE_RE.fullmatch(self.handle_id):
            raise ValueError("invalid rollback handle")

    @classmethod
    def issue(cls) -> "RollbackHandle":
        return cls(secrets.token_urlsafe(32))

    def to_dict(self) -> dict[str, str]:
        return {"schema_version": self.schema_version, "handle_id": self.handle_id}


@dataclass(frozen=True)
class JournalFileRecord:
    relative_path: str
    original_sha256: str | None
    post_sha256: str
    original_content_b64: str | None
    original_mode: int | None = None

    def __post_init__(self) -> None:
        path = PurePosixPath(self.relative_path)
        if not self.relative_path or path.is_absolute() or ".." in path.parts:
            raise ValueError("journal path must be workspace-relative")
        if self.original_sha256 is not None and not _SHA256_RE.fullmatch(self.original_sha256):
            raise ValueError("invalid original sha256")
        if not _SHA256_RE.fullmatch(self.post_sha256):
            raise ValueError("invalid post sha256")
        if self.original_mode is not None and self.original_mode < 0:
            raise ValueError("invalid original mode")

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "original_sha256": self.original_sha256,
            "post_sha256": self.post_sha256,
            "original_content_b64": self.original_content_b64,
            "original_mode": self.original_mode,
        }


@dataclass
class ChangeJournalEntry:
    handle_id: str
    workspace_id: str
    change_set_id: str
    files: list[JournalFileRecord]
    created_at_unix: int
    expires_at_unix: int
    consumed: bool = False
    protection: str = "owner-only"
    schema_version: str = CHANGE_JOURNAL_SCHEMA_VERSION

    def validate(self) -> None:
        RollbackHandle(self.handle_id, self.schema_version)
        if not self.workspace_id or len(self.workspace_id) > 256:
            raise ValueError("invalid workspace_id")
        if not self.change_set_id or len(self.change_set_id) > 256:
            raise ValueError("invalid change_set_id")
        if self.created_at_unix < 0 or self.expires_at_unix <= self.created_at_unix:
            raise ValueError("invalid journal expiry")
        paths = [item.relative_path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate journal path")
        if self.protection not in {"owner-only", "encrypted"}:
            raise ValueError("unsupported journal protection")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "handle_id": self.handle_id,
            "workspace_id": self.workspace_id,
            "change_set_id": self.change_set_id,
            "files": [item.to_dict() for item in self.files],
            "created_at_unix": self.created_at_unix,
            "expires_at_unix": self.expires_at_unix,
            "consumed": self.consumed,
            "protection": self.protection,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ChangeJournalEntry":
        file_values = value.get("files", [])
        if not isinstance(file_values, list):
            raise ValueError("journal files must be an array")
        entry = cls(
            schema_version=str(value.get("schema_version", "")),
            handle_id=str(value["handle_id"]),
            workspace_id=str(value["workspace_id"]),
            change_set_id=str(value["change_set_id"]),
            files=[JournalFileRecord(**dict(item)) for item in file_values],
            created_at_unix=int(value["created_at_unix"]),
            expires_at_unix=int(value["expires_at_unix"]),
            consumed=bool(value.get("consumed", False)),
            protection=str(value.get("protection", "owner-only")),
        )
        entry.validate()
        return entry
