"""Runtime lifecycle and side-effect recovery contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .common import ContractViolation, ErrorCode, RuntimeErrorInfo


class RuntimeState(str, Enum):
    CREATED = "CREATED"
    PROVIDER_PENDING = "PROVIDER_PENDING"
    PROVIDER_COMPLETED = "PROVIDER_COMPLETED"
    TOOL_REQUESTED = "TOOL_REQUESTED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    TOOL_RUNNING = "TOOL_RUNNING"
    TOOL_SUCCEEDED = "TOOL_SUCCEEDED"
    TOOL_FAILED = "TOOL_FAILED"
    TOOL_SIDE_EFFECT_UNCERTAIN = "TOOL_SIDE_EFFECT_UNCERTAIN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"

    @property
    def terminal(self) -> bool:
        return self in {
            RuntimeState.COMPLETED,
            RuntimeState.FAILED,
            RuntimeState.CANCELLED,
            RuntimeState.BUDGET_EXCEEDED,
        }


class RecoveryPolicy(str, Enum):
    PURE = "PURE"
    IDEMPOTENT = "IDEMPOTENT"
    RETRYABLE_WITH_KEY = "RETRYABLE_WITH_KEY"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"
    MANUAL_RECONCILIATION = "MANUAL_RECONCILIATION"

    def permits_automatic_retry(self, *, has_idempotency_key: bool = False) -> bool:
        if self in {RecoveryPolicy.PURE, RecoveryPolicy.IDEMPOTENT}:
            return True
        if self is RecoveryPolicy.RETRYABLE_WITH_KEY:
            return has_idempotency_key
        return False

    def recovery_state_for_running(self, *, has_idempotency_key: bool = False) -> RuntimeState:
        if self.permits_automatic_retry(has_idempotency_key=has_idempotency_key):
            return RuntimeState.TOOL_REQUESTED
        return RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN


class OperatorAction(str, Enum):
    MARK_SUCCEEDED = "mark-succeeded"
    MARK_NOT_EXECUTED = "mark-not-executed"
    EXPLICIT_RETRY = "explicit-retry"
    ABANDON = "abandon"


class ReceiptRequirement(str, Enum):
    NONE = "none"
    OPTIONAL = "optional"
    IF_SIDE_EFFECT = "if-side-effect"
    REQUIRED = "required"


@dataclass(frozen=True)
class TransitionRule:
    source: RuntimeState
    target: RuntimeState
    event: str
    checkpoint: bool
    recovery_eligible: bool
    retry_eligible: bool
    approval_required: bool = False
    receipt_requirement: ReceiptRequirement = ReceiptRequirement.NONE

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.value,
            "target": self.target.value,
            "event": self.event,
            "checkpoint": self.checkpoint,
            "recovery_eligible": self.recovery_eligible,
            "retry_eligible": self.retry_eligible,
            "approval_required": self.approval_required,
            "receipt_requirement": self.receipt_requirement.value,
        }


def _transition(
    source: RuntimeState,
    target: RuntimeState,
    event: str,
    *,
    checkpoint: bool = True,
    recovery_eligible: bool = True,
    retry_eligible: bool = False,
    approval_required: bool = False,
    receipt_requirement: ReceiptRequirement = ReceiptRequirement.NONE,
) -> tuple[tuple[RuntimeState, RuntimeState], TransitionRule]:
    rule = TransitionRule(
        source=source,
        target=target,
        event=event,
        checkpoint=checkpoint,
        recovery_eligible=recovery_eligible,
        retry_eligible=retry_eligible,
        approval_required=approval_required,
        receipt_requirement=receipt_requirement,
    )
    return (source, target), rule


TRANSITION_RULES: dict[tuple[RuntimeState, RuntimeState], TransitionRule] = dict(
    [
        _transition(RuntimeState.CREATED, RuntimeState.PROVIDER_PENDING, "provider.requested", retry_eligible=True),
        _transition(RuntimeState.CREATED, RuntimeState.CANCELLED, "run.cancelled", recovery_eligible=False),
        _transition(RuntimeState.CREATED, RuntimeState.FAILED, "run.failed", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_PENDING, RuntimeState.PROVIDER_COMPLETED, "provider.completed"),
        _transition(RuntimeState.PROVIDER_PENDING, RuntimeState.FAILED, "provider.failed", retry_eligible=True),
        _transition(RuntimeState.PROVIDER_PENDING, RuntimeState.CANCELLED, "run.cancelled", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_PENDING, RuntimeState.BUDGET_EXCEEDED, "budget.exceeded", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_COMPLETED, RuntimeState.TOOL_REQUESTED, "tool.requested"),
        _transition(RuntimeState.PROVIDER_COMPLETED, RuntimeState.COMPLETED, "run.completed", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_COMPLETED, RuntimeState.FAILED, "run.failed", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_COMPLETED, RuntimeState.CANCELLED, "run.cancelled", recovery_eligible=False),
        _transition(RuntimeState.PROVIDER_COMPLETED, RuntimeState.BUDGET_EXCEEDED, "budget.exceeded", recovery_eligible=False),
        _transition(RuntimeState.TOOL_REQUESTED, RuntimeState.APPROVAL_PENDING, "approval.requested"),
        _transition(RuntimeState.TOOL_REQUESTED, RuntimeState.TOOL_RUNNING, "tool.started"),
        _transition(RuntimeState.TOOL_REQUESTED, RuntimeState.TOOL_FAILED, "tool.rejected"),
        _transition(RuntimeState.TOOL_REQUESTED, RuntimeState.FAILED, "run.failed", recovery_eligible=False),
        _transition(RuntimeState.TOOL_REQUESTED, RuntimeState.CANCELLED, "run.cancelled", recovery_eligible=False),
        _transition(RuntimeState.APPROVAL_PENDING, RuntimeState.TOOL_RUNNING, "approval.granted", approval_required=True),
        _transition(RuntimeState.APPROVAL_PENDING, RuntimeState.TOOL_FAILED, "approval.denied"),
        _transition(RuntimeState.APPROVAL_PENDING, RuntimeState.CANCELLED, "approval.cancelled", recovery_eligible=False),
        _transition(RuntimeState.APPROVAL_PENDING, RuntimeState.FAILED, "approval.failed", recovery_eligible=False),
        _transition(RuntimeState.TOOL_RUNNING, RuntimeState.TOOL_SUCCEEDED, "tool.succeeded", receipt_requirement=ReceiptRequirement.IF_SIDE_EFFECT),
        _transition(RuntimeState.TOOL_RUNNING, RuntimeState.TOOL_FAILED, "tool.failed", retry_eligible=True),
        _transition(RuntimeState.TOOL_RUNNING, RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN, "tool.side_effect_uncertain", receipt_requirement=ReceiptRequirement.OPTIONAL),
        _transition(RuntimeState.TOOL_RUNNING, RuntimeState.CANCELLED, "run.cancelled", recovery_eligible=False),
        _transition(RuntimeState.TOOL_SUCCEEDED, RuntimeState.PROVIDER_PENDING, "provider.requested", retry_eligible=True),
        _transition(RuntimeState.TOOL_FAILED, RuntimeState.PROVIDER_PENDING, "provider.requested", retry_eligible=True),
        _transition(RuntimeState.TOOL_FAILED, RuntimeState.TOOL_RUNNING, "recovery.retry", retry_eligible=True),
        _transition(RuntimeState.TOOL_FAILED, RuntimeState.FAILED, "run.failed", recovery_eligible=False),
        _transition(RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN, RuntimeState.TOOL_SUCCEEDED, OperatorAction.MARK_SUCCEEDED.value, receipt_requirement=ReceiptRequirement.OPTIONAL),
        _transition(RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN, RuntimeState.TOOL_FAILED, OperatorAction.MARK_NOT_EXECUTED.value),
        _transition(RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN, RuntimeState.TOOL_RUNNING, OperatorAction.EXPLICIT_RETRY.value, retry_eligible=True),
        _transition(RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN, RuntimeState.FAILED, OperatorAction.ABANDON.value, recovery_eligible=False),
    ]
)


def validate_transition(
    source: RuntimeState,
    target: RuntimeState,
    *,
    approval_present: bool = False,
    receipt_present: bool = False,
    side_effect: bool = False,
) -> TransitionRule:
    rule = TRANSITION_RULES.get((source, target))
    if rule is None:
        raise ContractViolation(
            RuntimeErrorInfo(
                ErrorCode.INTERNAL_ERROR,
                "illegal runtime state transition",
                details={"source": source.value, "target": target.value},
            )
        )
    if rule.approval_required and not approval_present:
        raise ContractViolation(
            RuntimeErrorInfo(ErrorCode.PERMISSION_DENIED, "transition requires an approval record")
        )
    if rule.receipt_requirement is ReceiptRequirement.REQUIRED and not receipt_present:
        raise ContractViolation(RuntimeErrorInfo(ErrorCode.INTERNAL_ERROR, "transition requires a receipt"))
    if rule.receipt_requirement is ReceiptRequirement.IF_SIDE_EFFECT and side_effect and not receipt_present:
        raise ContractViolation(
            RuntimeErrorInfo(ErrorCode.INTERNAL_ERROR, "side-effect success requires a receipt")
        )
    return rule


def transition_manifest() -> list[dict[str, Any]]:
    return [
        TRANSITION_RULES[key].to_dict()
        for key in sorted(TRANSITION_RULES, key=lambda item: (item[0].value, item[1].value))
    ]
