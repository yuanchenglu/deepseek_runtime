"""Policy and human-approval enforcement for production tool calls."""

from __future__ import annotations

import hashlib
import json
import shlex
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .contracts import ContractViolation, ErrorCode, RuntimeErrorInfo, ToolSpec
from .security import Decision, PermissionPolicy, PermissionRequest, Risk


class ApprovalOutcome(str, Enum):
    """A human or host decision for one ASK policy result."""

    APPROVE_ONCE = "approve-once"
    APPROVE_SESSION = "approve-session"
    DENY = "deny"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ApprovalRequest:
    """Content-minimized approval request safe for user-facing surfaces."""

    tool_name: str
    risk: Risk
    side_effect: bool
    summary: str


class ApprovalProvider(Protocol):
    """Host-provided approval boundary. Implementations must return synchronously."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        """Return the outcome for one approval request."""
        ...


@dataclass(frozen=True)
class AuthorizationEvent:
    """Publishable metadata for one policy/approval decision."""

    tool_name: str
    risk: Risk
    policy_decision: Decision
    approval_outcome: str | None
    summary: str
    cached_session_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": "tool_authorization",
            "tool": self.tool_name,
            "risk": self.risk.value,
            "policy_decision": self.policy_decision.value,
            "approval_outcome": self.approval_outcome,
            "summary": self.summary,
            "cached_session_approval": self.cached_session_approval,
        }


def summarize_approval(spec: ToolSpec, arguments: dict[str, Any]) -> str:
    """Create an approval summary without argument names, values, paths, or commands."""
    return (
        f"tool={spec.name}; risk={spec.risk}; side_effect={str(spec.side_effect).lower()}; "
        f"argument_count={len(arguments)}"
    )


def _approval_key(spec: ToolSpec, arguments: dict[str, Any]) -> str:
    """Create an internal exact-request key; the digest is never emitted as evidence."""
    canonical = json.dumps(
        arguments,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return f"{spec.name}:{spec.risk}:{digest}"


def _permission_request(risk: Risk, arguments: dict[str, Any]) -> PermissionRequest:
    """Extract only explicit policy selectors; absent paths use a non-specific sentinel."""
    path_value = arguments.get("path")
    path = path_value if isinstance(path_value, str) else ""

    command_value = arguments.get("command")
    command: tuple[str, ...] = ()
    if isinstance(command_value, list) and all(isinstance(item, str) for item in command_value):
        command = tuple(command_value)
    elif isinstance(command_value, str):
        try:
            command = tuple(shlex.split(command_value))
        except ValueError:
            command = ()

    return PermissionRequest(risk=risk, path=path, command=command)


def _scrub_new_policy_audit_events(policy: PermissionPolicy, start: int) -> None:
    """Ensure Runtime policy audit records contain no raw path or command values."""
    for event in policy.audit_events[start:]:
        event["path"] = None
        event["path_present"] = bool(event.get("path_present", False))
        event["command"] = []
        event["command_present"] = bool(event.get("command_present", False))


@dataclass
class AuthorizationSession:
    """Enforce one PermissionPolicy and ApprovalProvider for a Runtime.run session.

    PermissionPolicy uses declaration order and the last matching rule wins.
    """

    policy: PermissionPolicy = field(default_factory=PermissionPolicy)
    approval_provider: ApprovalProvider | None = None
    events: list[AuthorizationEvent] = field(default_factory=list)
    _session_approvals: set[str] = field(default_factory=set, init=False, repr=False)

    def authorize(self, spec: ToolSpec, arguments: dict[str, Any]) -> None:
        try:
            risk = Risk(spec.risk)
        except ValueError as exc:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.PERMISSION_DENIED,
                    "registered tool risk is not supported by the permission policy",
                    details={"tool": spec.name},
                    cause_class=type(exc).__name__,
                )
            ) from exc

        summary = summarize_approval(spec, arguments)
        audit_start = len(self.policy.audit_events)
        decision = self.policy.decide(_permission_request(risk, arguments))
        _scrub_new_policy_audit_events(self.policy, audit_start)

        if decision is Decision.ALLOW:
            self.events.append(
                AuthorizationEvent(spec.name, risk, decision, None, summary)
            )
            return
        if decision is Decision.DENY:
            self.events.append(
                AuthorizationEvent(spec.name, risk, decision, None, summary)
            )
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.PERMISSION_DENIED,
                    "tool execution was denied by policy",
                    details={"tool": spec.name, "risk": risk.value},
                )
            )

        approval_key = _approval_key(spec, arguments)
        if approval_key in self._session_approvals:
            self.events.append(
                AuthorizationEvent(
                    spec.name,
                    risk,
                    decision,
                    ApprovalOutcome.APPROVE_SESSION.value,
                    summary,
                    cached_session_approval=True,
                )
            )
            return

        if self.approval_provider is None:
            self.events.append(
                AuthorizationEvent(spec.name, risk, decision, "unavailable", summary)
            )
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.APPROVAL_UNAVAILABLE,
                    "tool execution requires approval but no ApprovalProvider is available",
                    details={"tool": spec.name, "risk": risk.value},
                )
            )

        request = ApprovalRequest(
            tool_name=spec.name,
            risk=risk,
            side_effect=spec.side_effect,
            summary=summary,
        )
        try:
            outcome = self.approval_provider.request_approval(request)
        except Exception as exc:
            self.events.append(
                AuthorizationEvent(spec.name, risk, decision, "unavailable", summary)
            )
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.APPROVAL_UNAVAILABLE,
                    "ApprovalProvider failed while requesting approval",
                    details={"tool": spec.name, "risk": risk.value},
                    cause_class=type(exc).__name__,
                )
            ) from exc

        if not isinstance(outcome, ApprovalOutcome):
            self.events.append(
                AuthorizationEvent(spec.name, risk, decision, "invalid", summary)
            )
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.APPROVAL_UNAVAILABLE,
                    "ApprovalProvider returned an invalid outcome",
                    details={"tool": spec.name, "risk": risk.value},
                )
            )

        self.events.append(
            AuthorizationEvent(spec.name, risk, decision, outcome.value, summary)
        )
        if outcome is ApprovalOutcome.APPROVE_ONCE:
            return
        if outcome is ApprovalOutcome.APPROVE_SESSION:
            self._session_approvals.add(approval_key)
            return
        if outcome is ApprovalOutcome.TIMEOUT:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.APPROVAL_TIMEOUT,
                    "tool approval timed out",
                    details={"tool": spec.name, "risk": risk.value},
                )
            )
        raise ContractViolation(
            RuntimeErrorInfo(
                ErrorCode.PERMISSION_DENIED,
                "tool execution was denied by approval",
                details={"tool": spec.name, "risk": risk.value},
            )
        )
