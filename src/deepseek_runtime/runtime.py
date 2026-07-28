"""Production Agent Runtime loop and built-in Workspace tools."""

from __future__ import annotations

import copy
import json
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .approval import ApprovalProvider, AuthorizationSession
from .client import DeepSeekClient
from .contracts import (
    ContractViolation,
    ErrorCode,
    RecoverableCheckpoint,
    RecoveryPolicy,
    RuntimeErrorInfo,
    RuntimeState,
    ToolCallCheckpoint,
    ToolRegistry,
    ToolSpec,
    normalize_tool_result,
)
from .diagnostics import build_diagnostics
from .evidence import redact, request_evidence, response_evidence, sha256_bytes, wire_json
from .execution import (
    CancellationToken,
    ExecutionAdapter,
    ExecutionContext,
    NoIsolationLocalAdapter,
)
from .lifecycle import (
    BudgetTracker,
    CheckpointSink,
    LifecycleTrace,
    RuntimeBudgets,
    ToolErrorPolicy,
    safe_usage_evidence,
)
from .security import PermissionPolicy
from .workspace import WorkspaceResolver, WorkspaceViolation


@dataclass
class RuntimeResult:
    """Result envelope returned by every completed or paused Runtime loop."""

    ok: bool
    final_text: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_class: str | None = None
    status: int | None = None
    step: int = 0
    runtime_state: RuntimeState = RuntimeState.CREATED
    lifecycle_events: list[dict[str, object]] = field(default_factory=list)
    budget: dict[str, Any] = field(default_factory=dict)
    checkpoint: RecoverableCheckpoint | None = field(default=None, repr=False)

    def _text_summary(self, value: str | None) -> dict[str, Any]:
        if not value:
            return {"present": False, "sha256": None, "bytes": 0}
        raw = wire_json(value)
        return {"present": True, "sha256": sha256_bytes(raw), "bytes": len(raw)}

    def _checkpoint_summary(self) -> dict[str, Any]:
        if self.checkpoint is None:
            return {"present": False}
        return {
            "present": True,
            "runtime_state": self.checkpoint.runtime_state.value,
            "step": self.checkpoint.step,
            "tool_call_count": len(self.checkpoint.tool_calls),
            "approval_count": len(self.checkpoint.approvals),
            "receipt_count": len(self.checkpoint.receipts),
        }

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "final_text": self._text_summary(self.final_text),
            "message_count": len(self.messages),
            "message_evidence": request_evidence(
                _request_for_evidence({"messages": self.messages})
            )["messages"],
            "usage": self.usage,
            "evidence": redact(self.evidence),
            "diagnostics": redact(self.diagnostics),
            "error": self.error,
            "error_class": self.error_class,
            "status": self.status,
            "step": self.step,
            "runtime_state": self.runtime_state.value,
            "lifecycle_events": self.lifecycle_events,
            "budget": self.budget,
            "checkpoint": self._checkpoint_summary(),
        }

    def to_dict(self, *, include_content: bool = False) -> dict[str, Any]:
        if include_content:
            value = asdict(self)
            value["runtime_state"] = self.runtime_state.value
            value["checkpoint"] = self.checkpoint.to_dict() if self.checkpoint else None
            return redact(value)
        return self.to_safe_dict()


@dataclass
class _PreparedToolCall:
    call_id: str
    tool_name: str = ""
    spec: ToolSpec | None = None
    arguments: dict[str, Any] | None = None
    error: RuntimeErrorInfo | None = None

    @property
    def executable(self) -> bool:
        return self.spec is not None and self.arguments is not None and self.error is None


@dataclass
class _ToolOutcome:
    content: str
    error: RuntimeErrorInfo | None
    execution_event: dict[str, object] | None
    receipt: dict[str, Any] | None = None


def _tool_calls_for_evidence(value: Any) -> list[dict[str, Any]]:
    """Build a non-executable structural view for legacy Evidence helpers."""
    if not isinstance(value, list):
        return []
    output: list[dict[str, Any]] = []
    for call in value:
        if not isinstance(call, Mapping):
            output.append({})
            continue
        normalized = dict(call)
        function = call.get("function")
        normalized["function"] = dict(function) if isinstance(function, Mapping) else {}
        output.append(normalized)
    return output


def _message_for_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    output = dict(value)
    if "tool_calls" in output:
        output["tool_calls"] = _tool_calls_for_evidence(output.get("tool_calls"))
    return output


def _request_for_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    output = dict(payload)
    messages = payload.get("messages")
    output["messages"] = (
        [_message_for_evidence(message) for message in messages]
        if isinstance(messages, list)
        else []
    )
    if "tools" in output:
        output["tools"] = _tool_calls_for_evidence(output.get("tools"))
    return output


def _response_for_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    output = dict(value)
    choices = value.get("choices")
    normalized_choices: list[dict[str, Any]] = []
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, Mapping):
                normalized_choices.append({})
                continue
            normalized = dict(choice)
            normalized["message"] = _message_for_evidence(choice.get("message"))
            normalized_choices.append(normalized)
    output["choices"] = normalized_choices
    return output


def _tool_error_content(error: RuntimeErrorInfo) -> str:
    return json.dumps(
        {"ok": False, "error": error.to_dict()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _invalid_tool_error(
    message: str,
    *,
    tool: str = "",
    cause: BaseException | None = None,
) -> RuntimeErrorInfo:
    return RuntimeErrorInfo(
        ErrorCode.TOOL_ARGUMENT_INVALID,
        message,
        details={"tool": tool},
        cause_class=type(cause).__name__ if cause is not None else None,
    )


def _is_execution_adapter(value: object) -> bool:
    capabilities = getattr(value, "capabilities", None)
    return (
        isinstance(getattr(value, "name", None), str)
        and callable(getattr(value, "execute", None))
        and callable(getattr(capabilities, "to_dict", None))
    )


def _execution_failure_event(
    adapter: ExecutionAdapter,
    *,
    tool_name: str,
    code: ErrorCode,
    cause_class: str | None = None,
) -> dict[str, object]:
    event: dict[str, object] = {
        "event": "tool_execution",
        "tool": tool_name,
        "adapter": adapter.name,
        "capabilities": adapter.capabilities.to_dict(),
        "status": "failed",
        "error_code": code.value,
    }
    if cause_class is not None:
        event["cause_class"] = cause_class
    return event


def _prepare_tool_call(registry: ToolRegistry, call: Any, call_id: str) -> _PreparedToolCall:
    if not isinstance(call, Mapping):
        return _PreparedToolCall(call_id, error=_invalid_tool_error("tool call must be an object"))
    function = call.get("function")
    if not isinstance(function, Mapping):
        return _PreparedToolCall(
            call_id,
            error=_invalid_tool_error("tool call function must be an object"),
        )

    name_value = function.get("name")
    if not isinstance(name_value, str) or not name_value:
        return _PreparedToolCall(
            call_id,
            error=_invalid_tool_error("tool call name must be non-empty text"),
        )
    name = name_value

    arguments_value = function.get("arguments")
    if not isinstance(arguments_value, str):
        return _PreparedToolCall(
            call_id,
            tool_name=name,
            error=_invalid_tool_error("tool call arguments must be JSON text", tool=name),
        )
    try:
        parsed = json.loads(arguments_value)
    except json.JSONDecodeError as exc:
        return _PreparedToolCall(
            call_id,
            tool_name=name,
            error=_invalid_tool_error(
                "tool call arguments contain invalid JSON",
                tool=name,
                cause=exc,
            ),
        )

    try:
        spec = registry.resolve(name)
    except ContractViolation as exc:
        return _PreparedToolCall(call_id, tool_name=name, error=exc.error)

    try:
        validated = spec.validate_arguments(parsed)
    except ContractViolation as exc:
        return _PreparedToolCall(
            call_id,
            tool_name=name,
            spec=spec,
            arguments=dict(parsed) if isinstance(parsed, dict) else None,
            error=exc.error,
        )
    return _PreparedToolCall(call_id, name, spec, validated)


def _execute_prepared_tool(
    prepared: _PreparedToolCall,
    authorization: AuthorizationSession,
    execution_adapter: ExecutionAdapter,
    execution_context: ExecutionContext,
    *,
    on_approval_pending: Any = None,
    on_authorized: Any = None,
) -> _ToolOutcome:
    if not prepared.executable or prepared.spec is None or prepared.arguments is None:
        error = prepared.error or RuntimeErrorInfo(
            ErrorCode.TOOL_EXECUTION_FAILED,
            "prepared tool call is not executable",
            details={"tool": prepared.tool_name},
        )
        return _ToolOutcome(_tool_error_content(error), error, None)

    try:
        authorization.authorize(
            prepared.spec,
            prepared.arguments,
            on_approval_pending=on_approval_pending,
        )
    except ContractViolation as exc:
        return _ToolOutcome(_tool_error_content(exc.error), exc.error, None)

    if on_authorized is not None:
        on_authorized()

    try:
        outcome = execution_adapter.execute(
            prepared.spec,
            prepared.arguments,
            execution_context,
        )
    except ContractViolation as exc:
        return _ToolOutcome(
            _tool_error_content(exc.error),
            exc.error,
            _execution_failure_event(
                execution_adapter,
                tool_name=prepared.tool_name,
                code=exc.error.code,
                cause_class=exc.error.cause_class,
            ),
        )
    except Exception as exc:
        error = RuntimeErrorInfo(
            ErrorCode.TOOL_EXECUTION_FAILED,
            "execution adapter raised an exception",
            details={"tool": prepared.tool_name, "adapter": execution_adapter.name},
            cause_class=type(exc).__name__,
        )
        return _ToolOutcome(
            _tool_error_content(error),
            error,
            _execution_failure_event(
                execution_adapter,
                tool_name=prepared.tool_name,
                code=error.code,
                cause_class=error.cause_class,
            ),
        )

    execution_event = outcome.evidence(tool_name=prepared.tool_name)
    execution_event["status"] = "succeeded"
    try:
        content = normalize_tool_result(outcome.value, tool_name=prepared.tool_name)
    except ContractViolation as exc:
        execution_event["status"] = "failed"
        execution_event["error_code"] = exc.error.code.value
        return _ToolOutcome(
            _tool_error_content(exc.error),
            exc.error,
            execution_event,
            receipt=dict(outcome.private_receipt) if outcome.private_receipt else None,
        )
    return _ToolOutcome(
        content,
        None,
        execution_event,
        receipt=dict(outcome.private_receipt) if outcome.private_receipt else None,
    )


def _checkpoint_call(prepared: _PreparedToolCall) -> ToolCallCheckpoint | None:
    if prepared.spec is None or prepared.arguments is None:
        return None
    return ToolCallCheckpoint(
        call_id=prepared.call_id,
        name=prepared.spec.name,
        arguments=copy.deepcopy(prepared.arguments),
        state=RuntimeState.TOOL_REQUESTED,
        recovery_policy=prepared.spec.recovery_policy,
        side_effect=prepared.spec.side_effect,
        error=prepared.error,
    )


def _aggregate_legacy_usage(total: dict[str, int], usage_value: Any) -> None:
    for key, value in safe_usage_evidence(usage_value).items():
        if isinstance(value, int) and not isinstance(value, bool):
            total[key] = total.get(key, 0) + value


def _error_result(
    error: RuntimeErrorInfo,
    *,
    lifecycle: LifecycleTrace,
    messages: list[dict[str, Any]],
    usage: dict[str, int],
    evidence: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    step: int,
    budget: BudgetTracker,
    checkpoint: RecoverableCheckpoint | None,
    status: int | None = None,
) -> RuntimeResult:
    return RuntimeResult(
        False,
        messages=messages,
        usage=usage,
        evidence=evidence,
        diagnostics=diagnostics,
        error=error.message,
        error_class=error.code.value,
        status=status,
        step=step,
        runtime_state=lifecycle.state,
        lifecycle_events=[event.to_dict() for event in lifecycle.events],
        budget=budget.snapshot(),
        checkpoint=checkpoint,
    )


@dataclass
class DeepSeekRuntime:
    """Execute the single Provider → authorization → Adapter production loop."""

    client: DeepSeekClient
    max_steps: int = 8

    def __post_init__(self) -> None:
        if not isinstance(self.max_steps, int) or isinstance(self.max_steps, bool) or self.max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")

    def run(
        self,
        messages: list[dict[str, Any]],
        workspace: str | Path = ".",
        tools: ToolRegistry | None = None,
        policy: PermissionPolicy | None = None,
        approval_provider: ApprovalProvider | None = None,
        execution_adapter: ExecutionAdapter | None = None,
        cancellation: CancellationToken | None = None,
        budgets: RuntimeBudgets | None = None,
        tool_error_policy: ToolErrorPolicy = ToolErrorPolicy.CONTINUE,
        checkpoint_sink: CheckpointSink | None = None,
        session_id: str | None = None,
    ) -> RuntimeResult:
        """Run with validated lifecycle, budget, cancellation, and checkpoint handoff.

        ``checkpoint_sink`` receives private in-memory snapshots. This handoff does not
        claim the durable, encrypted, locked, or migratable M3 checkpoint store.
        """
        if tools is not None and not isinstance(tools, ToolRegistry):
            raise TypeError("tools must be a ToolRegistry; raw handler mappings are not supported")
        if policy is not None and not isinstance(policy, PermissionPolicy):
            raise TypeError("policy must be a PermissionPolicy")
        if execution_adapter is not None and not _is_execution_adapter(execution_adapter):
            raise TypeError("execution_adapter must implement ExecutionAdapter")
        if cancellation is not None and not isinstance(cancellation, CancellationToken):
            raise TypeError("cancellation must be a CancellationToken")
        if budgets is not None and not isinstance(budgets, RuntimeBudgets):
            raise TypeError("budgets must be RuntimeBudgets")
        if not isinstance(tool_error_policy, ToolErrorPolicy):
            raise TypeError("tool_error_policy must be ToolErrorPolicy")
        if checkpoint_sink is not None and not callable(checkpoint_sink):
            raise TypeError("checkpoint_sink must be callable")
        if session_id is not None and (not isinstance(session_id, str) or not session_id):
            raise ValueError("session_id must be non-empty text")

        requested_budgets = budgets or RuntimeBudgets()
        effective_max_steps = (
            self.max_steps
            if requested_budgets.max_steps is None
            else min(self.max_steps, requested_budgets.max_steps)
        )
        effective_budgets = RuntimeBudgets(
            max_steps=effective_max_steps,
            max_tokens=requested_budgets.max_tokens,
            max_cost_usd=requested_budgets.max_cost_usd,
            max_context_tokens=requested_budgets.max_context_tokens,
            max_elapsed_seconds=requested_budgets.max_elapsed_seconds,
        )

        registry = tools if tools is not None else ToolRegistry()
        authorization = AuthorizationSession(
            policy=policy if policy is not None else PermissionPolicy(),
            approval_provider=approval_provider,
        )
        adapter = execution_adapter if execution_adapter is not None else NoIsolationLocalAdapter()
        workspace_path = Path(workspace)
        execution_context = ExecutionContext(workspace_path, cancellation)
        active_messages = [dict(message) for message in messages]
        tool_definitions = registry.provider_definitions()
        total_usage: dict[str, int] = {}
        evidence: list[dict[str, Any]] = []
        diagnostics = build_diagnostics(workspace_path)
        lifecycle = LifecycleTrace()
        budget_tracker = BudgetTracker(effective_budgets)
        current_tool_calls: list[ToolCallCheckpoint] = []
        receipts: list[dict[str, Any]] = []
        provider_continuation: dict[str, Any] | None = None
        last_checkpoint: RecoverableCheckpoint | None = None
        sink_enabled = checkpoint_sink is not None
        run_session_id = session_id or uuid.uuid4().hex
        step = 0

        def build_checkpoint(target: RuntimeState, checkpoint_step: int) -> RecoverableCheckpoint:
            return RecoverableCheckpoint(
                session_id=run_session_id,
                runtime_state=target,
                step=checkpoint_step,
                messages=copy.deepcopy(active_messages),
                provider_continuation=copy.deepcopy(provider_continuation),
                tool_calls=copy.deepcopy(current_tool_calls),
                approvals=[event.to_dict() for event in authorization.events],
                receipts=copy.deepcopy(receipts),
                budgets=copy.deepcopy(budget_tracker.snapshot()),
                recovery_metadata={
                    "handoff": "in-memory",
                    "lifecycle_event_count": len(lifecycle.events),
                    "tool_error_policy": tool_error_policy.value,
                    "execution_adapter": adapter.name,
                },
            )

        def handoff_current_state(checkpoint_step: int) -> None:
            nonlocal last_checkpoint, sink_enabled
            checkpoint = build_checkpoint(lifecycle.state, checkpoint_step)
            checkpoint.validate()
            last_checkpoint = checkpoint
            if sink_enabled and checkpoint_sink is not None:
                try:
                    checkpoint_sink(copy.deepcopy(checkpoint))
                except Exception as exc:
                    sink_enabled = False
                    raise ContractViolation(
                        RuntimeErrorInfo(
                            ErrorCode.INTERNAL_ERROR,
                            "checkpoint handoff failed",
                            details={"runtime_state": lifecycle.state.value},
                            cause_class=type(exc).__name__,
                        )
                    ) from exc

        def transition(
            target: RuntimeState,
            *,
            transition_step: int,
            approval_present: bool = False,
            receipt_present: bool = False,
            side_effect: bool = False,
        ) -> None:
            rule = lifecycle.transition(
                target,
                step=transition_step,
                approval_present=approval_present,
                receipt_present=receipt_present,
                side_effect=side_effect,
            )
            if rule.checkpoint:
                handoff_current_state(transition_step)

        def fail_transition(error: RuntimeErrorInfo, *, failure_step: int) -> RuntimeResult:
            nonlocal sink_enabled
            sink_enabled = False
            try:
                if lifecycle.state is RuntimeState.TOOL_RUNNING:
                    transition(RuntimeState.TOOL_FAILED, transition_step=failure_step)
                if lifecycle.state is RuntimeState.TOOL_SUCCEEDED:
                    transition(RuntimeState.PROVIDER_PENDING, transition_step=failure_step)
                if lifecycle.state is RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN:
                    transition(RuntimeState.FAILED, transition_step=failure_step)
                elif lifecycle.state is not RuntimeState.FAILED and not lifecycle.state.terminal:
                    transition(RuntimeState.FAILED, transition_step=failure_step)
            except (ContractViolation, ValueError):
                pass
            return _error_result(
                error,
                lifecycle=lifecycle,
                messages=active_messages,
                usage=total_usage,
                evidence=evidence,
                diagnostics=diagnostics,
                step=failure_step,
                budget=budget_tracker,
                checkpoint=last_checkpoint,
            )

        try:
            if cancellation is not None and cancellation.cancelled:
                transition(RuntimeState.CANCELLED, transition_step=0)
                return _error_result(
                    RuntimeErrorInfo(ErrorCode.CANCELLED, "Runtime was cancelled before Provider call"),
                    lifecycle=lifecycle,
                    messages=active_messages,
                    usage=total_usage,
                    evidence=evidence,
                    diagnostics=diagnostics,
                    step=0,
                    budget=budget_tracker,
                    checkpoint=last_checkpoint,
                )

            transition(RuntimeState.PROVIDER_PENDING, transition_step=0)

            while True:
                next_step = step + 1
                if cancellation is not None and cancellation.cancelled:
                    transition(RuntimeState.CANCELLED, transition_step=step)
                    return _error_result(
                        RuntimeErrorInfo(ErrorCode.CANCELLED, "Runtime was cancelled before Provider call"),
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                budget_error = budget_tracker.before_provider(next_step)
                if budget_error is not None:
                    transition(RuntimeState.BUDGET_EXCEEDED, transition_step=step)
                    return _error_result(
                        budget_error,
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                step = next_step
                payload: dict[str, Any] = {
                    "messages": active_messages,
                    "thinking": {"type": "enabled"},
                }
                if tool_definitions:
                    payload["tools"] = tool_definitions

                try:
                    result = self.client.chat(payload)
                except Exception as exc:
                    transition(RuntimeState.FAILED, transition_step=step)
                    return _error_result(
                        RuntimeErrorInfo(
                            ErrorCode.PROVIDER_ERROR,
                            "Provider client raised an exception",
                            cause_class=type(exc).__name__,
                        ),
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                usage_value = result.usage
                safe_usage = safe_usage_evidence(usage_value)
                _aggregate_legacy_usage(total_usage, usage_value)
                budget_tracker.record_provider(usage_value, step=step)

                step_evidence: dict[str, Any] = {
                    "step": step,
                    "status": result.status,
                    "elapsed_ms": result.elapsed_ms,
                    "request_fingerprint": result.request_fingerprint,
                    "request_id": result.request_id,
                    "usage": safe_usage,
                    "budget": budget_tracker.snapshot(),
                    "request_evidence": request_evidence(
                        _request_for_evidence(result.request_payload or payload)
                    ),
                    "response_evidence": response_evidence(
                        _response_for_evidence(result.body)
                    ),
                    "authorization_events": [],
                    "execution_events": [],
                    "error": result.error,
                    "error_class": result.error_class,
                }
                evidence.append(step_evidence)

                if result.status != 200:
                    transition(RuntimeState.FAILED, transition_step=step)
                    return RuntimeResult(
                        False,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        error=result.error,
                        error_class=result.error_class or ErrorCode.PROVIDER_ERROR.value,
                        status=result.status,
                        step=step,
                        runtime_state=lifecycle.state,
                        lifecycle_events=[event.to_dict() for event in lifecycle.events],
                        budget=budget_tracker.snapshot(),
                        checkpoint=last_checkpoint,
                    )

                body = result.body
                try:
                    if not isinstance(body, Mapping):
                        raise TypeError("provider body must be an object")
                    choices = body["choices"]
                    if not isinstance(choices, list) or not choices:
                        raise TypeError("provider choices must be a non-empty array")
                    first_choice = choices[0]
                    if not isinstance(first_choice, Mapping):
                        raise TypeError("provider choice must be an object")
                    message_value = first_choice["message"]
                    if not isinstance(message_value, Mapping):
                        raise TypeError("provider message must be an object")
                    message = dict(message_value)
                except (KeyError, IndexError, TypeError):
                    transition(RuntimeState.FAILED, transition_step=step)
                    return _error_result(
                        RuntimeErrorInfo(
                            ErrorCode.PROVIDER_RESPONSE_INVALID,
                            "malformed provider response",
                        ),
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                active_messages.append(message)
                provider_continuation = {
                    "request_id": result.request_id,
                    "message": copy.deepcopy(message),
                }
                transition(RuntimeState.PROVIDER_COMPLETED, transition_step=step)

                budget_error = budget_tracker.after_provider()
                if budget_error is not None:
                    transition(RuntimeState.BUDGET_EXCEEDED, transition_step=step)
                    return _error_result(
                        budget_error,
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                calls_value = message.get("tool_calls")
                calls = [] if calls_value is None else calls_value
                if not calls:
                    content = message.get("content", "")
                    transition(RuntimeState.COMPLETED, transition_step=step)
                    return RuntimeResult(
                        True,
                        final_text=content if isinstance(content, str) else "",
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        runtime_state=lifecycle.state,
                        lifecycle_events=[event.to_dict() for event in lifecycle.events],
                        budget=budget_tracker.snapshot(),
                        checkpoint=last_checkpoint,
                    )
                if not isinstance(calls, list):
                    transition(RuntimeState.FAILED, transition_step=step)
                    return _error_result(
                        RuntimeErrorInfo(
                            ErrorCode.PROVIDER_RESPONSE_INVALID,
                            "malformed provider tool_calls",
                        ),
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                call_ids: list[str] = []
                invalid_call_id = False
                for call in calls:
                    call_id = call.get("id") if isinstance(call, Mapping) else None
                    if not isinstance(call_id, str) or not call_id:
                        invalid_call_id = True
                        break
                    call_ids.append(call_id)
                if invalid_call_id:
                    transition(RuntimeState.FAILED, transition_step=step)
                    return _error_result(
                        RuntimeErrorInfo(
                            ErrorCode.PROVIDER_RESPONSE_INVALID,
                            "malformed provider tool call id",
                        ),
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                prepared_calls = [
                    _prepare_tool_call(registry, call, call_id)
                    for call, call_id in zip(calls, call_ids, strict=True)
                ]
                current_tool_calls = [
                    checkpoint_call
                    for prepared in prepared_calls
                    if (checkpoint_call := _checkpoint_call(prepared)) is not None
                ]
                transition(RuntimeState.TOOL_REQUESTED, transition_step=step)

                batch_failed = False
                any_side_effect = False
                all_side_effect_receipts = True
                cancellation_error: RuntimeErrorInfo | None = None
                uncertain_tool: ToolCallCheckpoint | None = None

                for prepared in prepared_calls:
                    checkpoint_call = next(
                        (item for item in current_tool_calls if item.call_id == prepared.call_id),
                        None,
                    )

                    if cancellation is not None and cancellation.cancelled:
                        cancellation_error = RuntimeErrorInfo(
                            ErrorCode.CANCELLED,
                            "Runtime was cancelled before the next tool call",
                        )
                        break

                    authorization_start = len(authorization.events)

                    def on_pending() -> None:
                        if checkpoint_call is not None:
                            checkpoint_call.state = RuntimeState.APPROVAL_PENDING
                        if lifecycle.state is RuntimeState.TOOL_REQUESTED:
                            transition(RuntimeState.APPROVAL_PENDING, transition_step=step)
                        elif lifecycle.state is RuntimeState.TOOL_RUNNING:
                            handoff_current_state(step)

                    def on_authorized() -> None:
                        if checkpoint_call is not None:
                            checkpoint_call.state = RuntimeState.TOOL_RUNNING
                            checkpoint_call.attempt_count = 1
                        if lifecycle.state is RuntimeState.APPROVAL_PENDING:
                            transition(
                                RuntimeState.TOOL_RUNNING,
                                transition_step=step,
                                approval_present=True,
                            )
                        elif lifecycle.state is RuntimeState.TOOL_REQUESTED:
                            transition(RuntimeState.TOOL_RUNNING, transition_step=step)
                        elif lifecycle.state is RuntimeState.TOOL_RUNNING:
                            handoff_current_state(step)

                    outcome = _execute_prepared_tool(
                        prepared,
                        authorization,
                        adapter,
                        execution_context,
                        on_approval_pending=on_pending,
                        on_authorized=on_authorized,
                    )

                    new_authorization_events = authorization.events[authorization_start:]
                    authorization_events = step_evidence["authorization_events"]
                    if isinstance(authorization_events, list):
                        authorization_events.extend(
                            event.to_dict() for event in new_authorization_events
                        )
                    if checkpoint_call is not None and new_authorization_events:
                        checkpoint_call.approval = new_authorization_events[-1].to_dict()
                        if outcome.error is not None and outcome.execution_event is None:
                            handoff_current_state(step)

                    execution_events = step_evidence["execution_events"]
                    if outcome.execution_event is not None and isinstance(execution_events, list):
                        execution_events.append(outcome.execution_event)

                    active_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": prepared.call_id,
                            "content": outcome.content,
                        }
                    )

                    if checkpoint_call is not None:
                        any_side_effect = any_side_effect or checkpoint_call.side_effect
                        if outcome.error is None:
                            checkpoint_call.state = RuntimeState.TOOL_SUCCEEDED
                            checkpoint_call.result = outcome.content
                            checkpoint_call.receipt = copy.deepcopy(outcome.receipt)
                            if checkpoint_call.side_effect and outcome.receipt is None:
                                all_side_effect_receipts = False
                            if outcome.receipt is not None:
                                receipts.append(copy.deepcopy(outcome.receipt))
                        else:
                            checkpoint_call.state = RuntimeState.TOOL_FAILED
                            checkpoint_call.error = outcome.error

                    if outcome.error is not None:
                        batch_failed = True
                        if outcome.error.code is ErrorCode.CANCELLED:
                            cancellation_error = outcome.error
                            if checkpoint_call is not None and checkpoint_call.side_effect:
                                checkpoint_call.state = RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN
                                checkpoint_call.error = RuntimeErrorInfo(
                                    ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN,
                                    "side-effect outcome is uncertain after cancellation",
                                    details={"tool": checkpoint_call.name},
                                )
                                uncertain_tool = checkpoint_call
                            break

                if cancellation_error is not None:
                    if uncertain_tool is not None:
                        transition(
                            RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
                            transition_step=step,
                            side_effect=True,
                            receipt_present=uncertain_tool.receipt is not None,
                        )
                        return _error_result(
                            uncertain_tool.error
                            or RuntimeErrorInfo(
                                ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN,
                                "side-effect outcome is uncertain",
                            ),
                            lifecycle=lifecycle,
                            messages=active_messages,
                            usage=total_usage,
                            evidence=evidence,
                            diagnostics=diagnostics,
                            step=step,
                            budget=budget_tracker,
                            checkpoint=last_checkpoint,
                        )
                    transition(RuntimeState.CANCELLED, transition_step=step)
                    return _error_result(
                        cancellation_error,
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )

                if batch_failed:
                    if lifecycle.state in {
                        RuntimeState.TOOL_REQUESTED,
                        RuntimeState.APPROVAL_PENDING,
                        RuntimeState.TOOL_RUNNING,
                    }:
                        transition(RuntimeState.TOOL_FAILED, transition_step=step)
                    if tool_error_policy is ToolErrorPolicy.TERMINATE:
                        transition(RuntimeState.FAILED, transition_step=step)
                        error = next(
                            (item.error for item in prepared_calls if item.error is not None),
                            None,
                        )
                        if error is None:
                            error = next(
                                (
                                    item.error
                                    for item in current_tool_calls
                                    if item.error is not None
                                ),
                                RuntimeErrorInfo(
                                    ErrorCode.TOOL_EXECUTION_FAILED,
                                    "tool batch failed",
                                ),
                            )
                        return _error_result(
                            error,
                            lifecycle=lifecycle,
                            messages=active_messages,
                            usage=total_usage,
                            evidence=evidence,
                            diagnostics=diagnostics,
                            step=step,
                            budget=budget_tracker,
                            checkpoint=last_checkpoint,
                        )
                    transition(RuntimeState.PROVIDER_PENDING, transition_step=step)
                    current_tool_calls = []
                    continue

                try:
                    transition(
                        RuntimeState.TOOL_SUCCEEDED,
                        transition_step=step,
                        side_effect=any_side_effect,
                        receipt_present=(not any_side_effect or all_side_effect_receipts),
                    )
                except ContractViolation as exc:
                    if any_side_effect:
                        for checkpoint_call in current_tool_calls:
                            if checkpoint_call.side_effect:
                                checkpoint_call.state = RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN
                                checkpoint_call.error = RuntimeErrorInfo(
                                    ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN,
                                    "side-effect success lacks a required receipt",
                                    details={"tool": checkpoint_call.name},
                                )
                        transition(
                            RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
                            transition_step=step,
                            side_effect=True,
                        )
                        return _error_result(
                            RuntimeErrorInfo(
                                ErrorCode.TOOL_SIDE_EFFECT_UNCERTAIN,
                                "side-effect success cannot be recovered without a receipt",
                                cause_class=exc.error.cause_class,
                            ),
                            lifecycle=lifecycle,
                            messages=active_messages,
                            usage=total_usage,
                            evidence=evidence,
                            diagnostics=diagnostics,
                            step=step,
                            budget=budget_tracker,
                            checkpoint=last_checkpoint,
                        )
                    raise

                transition(RuntimeState.PROVIDER_PENDING, transition_step=step)
                current_tool_calls = []

                budget_error = budget_tracker.after_tool()
                if budget_error is not None:
                    transition(RuntimeState.BUDGET_EXCEEDED, transition_step=step)
                    return _error_result(
                        budget_error,
                        lifecycle=lifecycle,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        step=step,
                        budget=budget_tracker,
                        checkpoint=last_checkpoint,
                    )
        except ContractViolation as exc:
            return fail_transition(exc.error, failure_step=step)
        except Exception as exc:
            return fail_transition(
                RuntimeErrorInfo(
                    ErrorCode.INTERNAL_ERROR,
                    "Runtime lifecycle failed unexpectedly",
                    cause_class=type(exc).__name__,
                ),
                failure_step=step,
            )


@dataclass
class WorkspaceTools:
    """Built-in read-only tools registered through the production ToolRegistry."""

    root: str | Path
    _resolver: WorkspaceResolver = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._resolver = WorkspaceResolver(self.root)
        self.root = self._resolver.root

    def _path(self, raw: str) -> Path:
        return self._resolver.resolve(raw)

    def read_file(self, args: dict[str, Any]) -> str:
        return self._resolver.read_text(str(args.get("input", "")), max_chars=20_000)

    def search(self, args: dict[str, Any]) -> str:
        needle = str(args.get("input", ""))
        if not needle:
            raise ValueError("search input must not be empty")
        matches: list[str] = []
        for path in self._resolver.iter_files():
            try:
                if path.stat(follow_symlinks=False).st_size >= 1_000_000:
                    continue
                content = self._resolver.read_text(path)
                for number, line in enumerate(content.splitlines(), 1):
                    if needle in line:
                        matches.append(f"{self._resolver.relative(path)}:{number}:{line[:200]}")
                        if len(matches) >= 100:
                            return "\n".join(matches)
            except (UnicodeDecodeError, OSError, WorkspaceViolation):
                continue
        return "\n".join(matches) or "No matches"

    def catalog(self) -> ToolRegistry:
        input_schema = {
            "type": "object",
            "properties": {"input": {"type": "string", "minLength": 1}},
            "required": ["input"],
            "additionalProperties": False,
        }
        return ToolRegistry(
            (
                ToolSpec(
                    "read_file",
                    "Read one UTF-8 text file inside the workspace.",
                    input_schema,
                    self.read_file,
                    risk="read",
                    side_effect=False,
                    timeout_seconds=30.0,
                    max_output_bytes=100_000,
                    recovery_policy=RecoveryPolicy.PURE,
                ),
                ToolSpec(
                    "search",
                    "Search UTF-8 text files inside the workspace.",
                    input_schema,
                    self.search,
                    risk="read",
                    side_effect=False,
                    timeout_seconds=30.0,
                    max_output_bytes=100_000,
                    recovery_policy=RecoveryPolicy.PURE,
                ),
            )
        )

    def registry(self) -> ToolRegistry:
        return self.catalog()
