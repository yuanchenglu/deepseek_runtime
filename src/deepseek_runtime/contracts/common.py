"""Shared constants, errors, and safety helpers for Runtime contracts."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

ERROR_SCHEMA_VERSION = "1.0"
CHECKPOINT_SCHEMA_VERSION = "1.0"
EVIDENCE_SCHEMA_VERSION = "1.0"
CHANGE_JOURNAL_SCHEMA_VERSION = "1.0"

PUBLIC_FORBIDDEN_KEYS = {
    "api_key",
    "authorization",
    "arguments",
    "content",
    "messages",
    "new_content",
    "original_content",
    "original_content_b64",
    "prompt",
    "reasoning_content",
    "result",
    "response_body",
    "secret",
    "token",
}


class ErrorCode(str, Enum):
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_RESPONSE_INVALID = "PROVIDER_RESPONSE_INVALID"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_ARGUMENT_INVALID = "TOOL_ARGUMENT_INVALID"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_RESULT_INVALID = "TOOL_RESULT_INVALID"
    TOOL_SIDE_EFFECT_UNCERTAIN = "TOOL_SIDE_EFFECT_UNCERTAIN"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    APPROVAL_TIMEOUT = "APPROVAL_TIMEOUT"
    APPROVAL_UNAVAILABLE = "APPROVAL_UNAVAILABLE"
    CHECKPOINT_CORRUPT = "CHECKPOINT_CORRUPT"
    CHECKPOINT_VERSION_UNSUPPORTED = "CHECKPOINT_VERSION_UNSUPPORTED"
    ROLLBACK_HANDLE_INVALID = "ROLLBACK_HANDLE_INVALID"
    ROLLBACK_HANDLE_EXPIRED = "ROLLBACK_HANDLE_EXPIRED"
    ROLLBACK_WORKSPACE_MISMATCH = "ROLLBACK_WORKSPACE_MISMATCH"
    ROLLBACK_CONFLICT = "ROLLBACK_CONFLICT"
    CHANGE_CONFLICT = "CHANGE_CONFLICT"
    BUDGET_STEP_EXCEEDED = "BUDGET_STEP_EXCEEDED"
    BUDGET_TOKEN_EXCEEDED = "BUDGET_TOKEN_EXCEEDED"
    BUDGET_COST_EXCEEDED = "BUDGET_COST_EXCEEDED"
    BUDGET_CONTEXT_EXCEEDED = "BUDGET_CONTEXT_EXCEEDED"
    BUDGET_TIME_EXCEEDED = "BUDGET_TIME_EXCEEDED"
    CANCELLED = "CANCELLED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class RuntimeErrorInfo:
    code: ErrorCode
    message: str
    retryable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)
    cause_class: str | None = None
    schema_version: str = ERROR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ERROR_SCHEMA_VERSION:
            raise ValueError(f"unsupported error schema version: {self.schema_version}")
        if not self.message or len(self.message) > 512:
            raise ValueError("error message must contain 1..512 characters")
        if self.cause_class is not None and len(self.cause_class) > 128:
            raise ValueError("cause_class is too long")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
            "details": sanitize_public(self.details),
            "cause_class": self.cause_class,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RuntimeErrorInfo":
        details = value.get("details", {})
        if not isinstance(details, Mapping):
            raise ValueError("error details must be an object")
        return cls(
            schema_version=str(value.get("schema_version", "")),
            code=ErrorCode(str(value["code"])),
            message=str(value["message"]),
            retryable=bool(value.get("retryable", False)),
            details=dict(details),
            cause_class=(str(value["cause_class"]) if value.get("cause_class") is not None else None),
        )


class ContractViolation(ValueError):
    error: RuntimeErrorInfo

    def __init__(self, error: RuntimeErrorInfo):
        super().__init__(f"{error.code.value}: {error.message}")
        self.error = error


def assert_json_compatible(value: Any) -> None:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("contract value must be finite JSON-compatible data") from exc


def assert_publishable(value: Any, *, depth: int = 0) -> None:
    if depth > 16:
        raise ValueError("publishable evidence exceeds maximum nesting")
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in PUBLIC_FORBIDDEN_KEYS:
                raise ValueError(f"publishable evidence contains forbidden field: {key_text}")
            assert_publishable(item, depth=depth + 1)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_publishable(item, depth=depth + 1)
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("publishable evidence contains a non-finite number")
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError(f"publishable evidence contains unsupported type: {type(value).__name__}")


def sanitize_public(value: Any, *, depth: int = 0) -> Any:
    if depth > 16:
        return "[TRUNCATED]"
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 100:
                output["truncated_fields"] = True
                break
            key_text = str(key)
            if key_text.lower() in PUBLIC_FORBIDDEN_KEYS:
                output[f"{key_text}_redacted"] = True
            else:
                output[key_text] = sanitize_public(item, depth=depth + 1)
        return output
    if isinstance(value, (list, tuple)):
        items = list(value)
        list_output = [sanitize_public(item, depth=depth + 1) for item in items[:100]]
        if len(items) > 100:
            list_output.append("[TRUNCATED]")
        return list_output
    if isinstance(value, str):
        return value if len(value) <= 512 else value[:512] + "[TRUNCATED]"
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if value is None or isinstance(value, (int, bool)):
        return value
    return {"type": type(value).__name__, "redacted": True}
