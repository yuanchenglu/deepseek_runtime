"""Private checkpoint and public evidence contracts."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping

from .common import (
    CHECKPOINT_SCHEMA_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    ContractViolation,
    ErrorCode,
    RuntimeErrorInfo,
    assert_json_compatible,
    assert_publishable,
    sanitize_public,
)
from .state import RecoveryPolicy, RuntimeState


def _checkpoint_result(value: Any) -> Any:
    """Represent Runtime-supported byte results as JSON-compatible checkpoint text."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("checkpoint result contains non-UTF-8 bytes") from exc
    return copy.deepcopy(value)


@dataclass
class ToolCallCheckpoint:
    call_id: str
    name: str
    arguments: dict[str, Any]
    state: RuntimeState
    recovery_policy: RecoveryPolicy
    side_effect: bool
    attempt_count: int = 0
    idempotency_key: str | None = None
    approval: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    result: Any = None
    error: RuntimeErrorInfo | None = None

    def validate(self) -> None:
        if not self.call_id or len(self.call_id) > 256:
            raise ValueError("invalid tool call id")
        if not self.name or len(self.name) > 128:
            raise ValueError("invalid tool call name")
        if self.state not in {
            RuntimeState.TOOL_REQUESTED,
            RuntimeState.APPROVAL_PENDING,
            RuntimeState.TOOL_RUNNING,
            RuntimeState.TOOL_SUCCEEDED,
            RuntimeState.TOOL_FAILED,
            RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
        }:
            raise ValueError("invalid tool call state")
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be non-negative")
        if self.state is RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN and not self.side_effect:
            raise ValueError("only side-effect tools may be uncertain")
        if self.recovery_policy is RecoveryPolicy.RETRYABLE_WITH_KEY and not self.idempotency_key:
            raise ValueError("RETRYABLE_WITH_KEY requires an idempotency key")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "call_id": self.call_id,
            "name": self.name,
            "arguments": copy.deepcopy(self.arguments),
            "state": self.state.value,
            "recovery_policy": self.recovery_policy.value,
            "side_effect": self.side_effect,
            "attempt_count": self.attempt_count,
            "idempotency_key": self.idempotency_key,
            "approval": copy.deepcopy(self.approval),
            "receipt": copy.deepcopy(self.receipt),
            "result": _checkpoint_result(self.result),
            "error": self.error.to_dict() if self.error else None,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ToolCallCheckpoint":
        arguments = value.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("tool call arguments must be an object")
        error_value = value.get("error")
        if error_value is not None and not isinstance(error_value, Mapping):
            raise ValueError("tool call error must be an object")
        instance = cls(
            call_id=str(value["call_id"]),
            name=str(value["name"]),
            arguments=dict(arguments),
            state=RuntimeState(str(value["state"])),
            recovery_policy=RecoveryPolicy(str(value["recovery_policy"])),
            side_effect=bool(value["side_effect"]),
            attempt_count=int(value.get("attempt_count", 0)),
            idempotency_key=(str(value["idempotency_key"]) if value.get("idempotency_key") else None),
            approval=copy.deepcopy(value.get("approval")),
            receipt=copy.deepcopy(value.get("receipt")),
            result=copy.deepcopy(value.get("result")),
            error=RuntimeErrorInfo.from_dict(error_value) if error_value is not None else None,
        )
        instance.validate()
        return instance


@dataclass
class RecoverableCheckpoint:
    session_id: str
    runtime_state: RuntimeState = RuntimeState.CREATED
    step: int = 0
    messages: list[dict[str, Any]] = field(default_factory=list)
    provider_continuation: dict[str, Any] | None = None
    tool_calls: list[ToolCallCheckpoint] = field(default_factory=list)
    approvals: list[dict[str, Any]] = field(default_factory=list)
    receipts: list[dict[str, Any]] = field(default_factory=list)
    budgets: dict[str, Any] = field(default_factory=dict)
    recovery_metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != CHECKPOINT_SCHEMA_VERSION:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.CHECKPOINT_VERSION_UNSUPPORTED,
                    "unsupported checkpoint schema version",
                    details={"schema_version": self.schema_version},
                )
            )
        if not self.session_id or len(self.session_id) > 256:
            raise ValueError("invalid session_id")
        if self.step < 0:
            raise ValueError("checkpoint step must be non-negative")
        for call in self.tool_calls:
            call.validate()
        assert_json_compatible(self.to_dict(validate=False))

    def to_dict(self, *, validate: bool = True) -> dict[str, Any]:
        value = {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "runtime_state": self.runtime_state.value,
            "step": self.step,
            "messages": copy.deepcopy(self.messages),
            "provider_continuation": copy.deepcopy(self.provider_continuation),
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "approvals": copy.deepcopy(self.approvals),
            "receipts": copy.deepcopy(self.receipts),
            "budgets": copy.deepcopy(self.budgets),
            "recovery_metadata": copy.deepcopy(self.recovery_metadata),
        }
        if validate:
            self.validate()
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RecoverableCheckpoint":
        if str(value.get("schema_version", "")) != CHECKPOINT_SCHEMA_VERSION:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.CHECKPOINT_VERSION_UNSUPPORTED,
                    "unsupported checkpoint schema version",
                    details={"schema_version": str(value.get("schema_version", ""))},
                )
            )
        try:
            tool_values = value.get("tool_calls", [])
            if not isinstance(tool_values, list):
                raise TypeError("tool_calls must be an array")
            checkpoint = cls(
                schema_version=str(value["schema_version"]),
                session_id=str(value["session_id"]),
                runtime_state=RuntimeState(str(value["runtime_state"])),
                step=int(value.get("step", 0)),
                messages=copy.deepcopy(list(value.get("messages", []))),
                provider_continuation=copy.deepcopy(value.get("provider_continuation")),
                tool_calls=[ToolCallCheckpoint.from_dict(item) for item in tool_values],
                approvals=copy.deepcopy(list(value.get("approvals", []))),
                receipts=copy.deepcopy(list(value.get("receipts", []))),
                budgets=copy.deepcopy(dict(value.get("budgets", {}))),
                recovery_metadata=copy.deepcopy(dict(value.get("recovery_metadata", {}))),
            )
            checkpoint.validate()
            return checkpoint
        except ContractViolation:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.CHECKPOINT_CORRUPT,
                    "checkpoint structure is invalid",
                    cause_class=type(exc).__name__,
                )
            ) from exc


@dataclass(frozen=True)
class PublishableEvidence:
    run_id: str
    runtime_state: RuntimeState
    transitions: tuple[Mapping[str, Any], ...] = ()
    request_structure: tuple[Mapping[str, Any], ...] = ()
    response_structure: tuple[Mapping[str, Any], ...] = ()
    usage: Mapping[str, Any] = field(default_factory=dict)
    cost: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[RuntimeErrorInfo, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported evidence schema version: {self.schema_version}")
        if not self.run_id or len(self.run_id) > 256:
            raise ValueError("invalid evidence run_id")
        for value in (
            self.transitions,
            self.request_structure,
            self.response_structure,
            self.usage,
            self.cost,
            self.metadata,
        ):
            assert_publishable(value)

    def to_dict(self) -> dict[str, Any]:
        value = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "runtime_state": self.runtime_state.value,
            "transitions": sanitize_public(self.transitions),
            "request_structure": sanitize_public(self.request_structure),
            "response_structure": sanitize_public(self.response_structure),
            "usage": sanitize_public(self.usage),
            "cost": sanitize_public(self.cost),
            "errors": [error.to_dict() for error in self.errors],
            "metadata": sanitize_public(self.metadata),
        }
        assert_publishable(value)
        assert_json_compatible(value)
        return value
