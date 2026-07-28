"""Production Agent Runtime loop and built-in Workspace tools."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .approval import ApprovalProvider, AuthorizationSession
from .client import DeepSeekClient
from .contracts import (
    ContractViolation,
    ErrorCode,
    RecoveryPolicy,
    RuntimeErrorInfo,
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
from .security import PermissionPolicy
from .workspace import WorkspaceResolver, WorkspaceViolation


@dataclass
class RuntimeResult:
    """Result envelope returned by every completed Runtime loop."""

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

    def _text_summary(self, value: str | None) -> dict[str, Any]:
        if not value:
            return {"present": False, "sha256": None, "bytes": 0}
        raw = wire_json(value)
        return {"present": True, "sha256": sha256_bytes(raw), "bytes": len(raw)}

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
        }

    def to_dict(self, *, include_content: bool = False) -> dict[str, Any]:
        if include_content:
            return redact(asdict(self))
        return self.to_safe_dict()


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


def _response_for_evidence(body: dict[str, Any]) -> dict[str, Any]:
    output = dict(body)
    choices = body.get("choices")
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


def _invalid_tool_call(message: str, *, tool: str = "", cause: BaseException | None = None) -> str:
    return _tool_error_content(
        RuntimeErrorInfo(
            ErrorCode.TOOL_ARGUMENT_INVALID,
            message,
            details={"tool": tool},
            cause_class=type(cause).__name__ if cause is not None else None,
        )
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


def _execute_registered_tool(
    registry: ToolRegistry,
    authorization: AuthorizationSession,
    execution_adapter: ExecutionAdapter,
    execution_context: ExecutionContext,
    call: Any,
) -> tuple[str, dict[str, object] | None]:
    if not isinstance(call, Mapping):
        return _invalid_tool_call("tool call must be an object"), None
    function = call.get("function")
    if not isinstance(function, Mapping):
        return _invalid_tool_call("tool call function must be an object"), None

    name_value = function.get("name")
    if not isinstance(name_value, str) or not name_value:
        return _invalid_tool_call("tool call name must be non-empty text"), None
    name = name_value

    arguments_value = function.get("arguments")
    if not isinstance(arguments_value, str):
        return _invalid_tool_call("tool call arguments must be JSON text", tool=name), None

    try:
        arguments = json.loads(arguments_value)
    except json.JSONDecodeError as exc:
        return _invalid_tool_call(
            "tool call arguments contain invalid JSON",
            tool=name,
            cause=exc,
        ), None

    try:
        spec = registry.resolve(name)
        validated = spec.validate_arguments(arguments)
        authorization.authorize(spec, validated)
    except ContractViolation as exc:
        return _tool_error_content(exc.error), None

    try:
        outcome = execution_adapter.execute(spec, validated, execution_context)
    except ContractViolation as exc:
        return (
            _tool_error_content(exc.error),
            _execution_failure_event(
                execution_adapter,
                tool_name=name,
                code=exc.error.code,
                cause_class=exc.error.cause_class,
            ),
        )
    except Exception as exc:
        error = RuntimeErrorInfo(
            ErrorCode.TOOL_EXECUTION_FAILED,
            "execution adapter raised an exception",
            details={"tool": name, "adapter": execution_adapter.name},
            cause_class=type(exc).__name__,
        )
        return (
            _tool_error_content(error),
            _execution_failure_event(
                execution_adapter,
                tool_name=name,
                code=error.code,
                cause_class=error.cause_class,
            ),
        )

    execution_event = outcome.evidence(tool_name=name)
    execution_event["status"] = "succeeded"
    try:
        return normalize_tool_result(outcome.value, tool_name=name), execution_event
    except ContractViolation as exc:
        execution_event["status"] = "failed"
        execution_event["error_code"] = exc.error.code.value
        return _tool_error_content(exc.error), execution_event


@dataclass
class DeepSeekRuntime:
    """Execute the production Provider → Policy → Approval → Adapter loop."""

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
    ) -> RuntimeResult:
        """Run through Registry, Policy, Approval, and ExecutionAdapter.

        The default ``NoIsolationLocalAdapter`` preserves existing local behavior but
        intentionally provides no timeout, output, process-tree, or kernel isolation.
        Callers must explicitly select a restricted adapter for subprocess guarantees.
        """
        if tools is not None and not isinstance(tools, ToolRegistry):
            raise TypeError("tools must be a ToolRegistry; raw handler mappings are not supported")
        if policy is not None and not isinstance(policy, PermissionPolicy):
            raise TypeError("policy must be a PermissionPolicy")
        if execution_adapter is not None and not _is_execution_adapter(execution_adapter):
            raise TypeError("execution_adapter must implement ExecutionAdapter")
        if cancellation is not None and not isinstance(cancellation, CancellationToken):
            raise TypeError("cancellation must be a CancellationToken")

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

        for step in range(1, self.max_steps + 1):
            payload: dict[str, Any] = {
                "messages": active_messages,
                "thinking": {"type": "enabled"},
            }
            if tool_definitions:
                payload["tools"] = tool_definitions

            result = self.client.chat(payload)
            for key, value in result.usage.items():
                if isinstance(value, int) and not isinstance(value, bool):
                    total_usage[key] = total_usage.get(key, 0) + value

            step_evidence: dict[str, Any] = {
                "step": step,
                "status": result.status,
                "elapsed_ms": result.elapsed_ms,
                "request_fingerprint": result.request_fingerprint,
                "request_id": result.request_id,
                "usage": result.usage,
                "request_evidence": request_evidence(
                    _request_for_evidence(result.request_payload or payload)
                ),
                "response_evidence": response_evidence(_response_for_evidence(result.body)),
                "authorization_events": [],
                "execution_events": [],
                "error": result.error,
                "error_class": result.error_class,
            }
            evidence.append(step_evidence)

            if result.status != 200:
                return RuntimeResult(
                    False,
                    messages=active_messages,
                    usage=total_usage,
                    evidence=evidence,
                    diagnostics=diagnostics,
                    error=result.error,
                    error_class=result.error_class,
                    status=result.status,
                    step=step,
                )

            try:
                message = result.body["choices"][0]["message"]
                if not isinstance(message, dict):
                    raise TypeError("provider message must be an object")
            except (KeyError, IndexError, TypeError):
                return RuntimeResult(
                    False,
                    messages=active_messages,
                    usage=total_usage,
                    evidence=evidence,
                    diagnostics=diagnostics,
                    error="malformed provider response",
                    error_class=ErrorCode.PROVIDER_RESPONSE_INVALID.value,
                    step=step,
                )

            active_messages.append(dict(message))
            calls = message.get("tool_calls") or []
            if not calls:
                content = message.get("content", "")
                return RuntimeResult(
                    True,
                    final_text=content if isinstance(content, str) else "",
                    messages=active_messages,
                    usage=total_usage,
                    evidence=evidence,
                    diagnostics=diagnostics,
                    step=step,
                )
            if not isinstance(calls, list):
                return RuntimeResult(
                    False,
                    messages=active_messages,
                    usage=total_usage,
                    evidence=evidence,
                    diagnostics=diagnostics,
                    error="malformed provider tool_calls",
                    error_class=ErrorCode.PROVIDER_RESPONSE_INVALID.value,
                    step=step,
                )

            for call in calls:
                call_id = call.get("id") if isinstance(call, Mapping) else None
                if not isinstance(call_id, str) or not call_id:
                    return RuntimeResult(
                        False,
                        messages=active_messages,
                        usage=total_usage,
                        evidence=evidence,
                        diagnostics=diagnostics,
                        error="malformed provider tool call id",
                        error_class=ErrorCode.PROVIDER_RESPONSE_INVALID.value,
                        step=step,
                    )
                authorization_start = len(authorization.events)
                output, execution_event = _execute_registered_tool(
                    registry,
                    authorization,
                    adapter,
                    execution_context,
                    call,
                )
                authorization_events = step_evidence["authorization_events"]
                if isinstance(authorization_events, list):
                    authorization_events.extend(
                        event.to_dict()
                        for event in authorization.events[authorization_start:]
                    )
                execution_events = step_evidence["execution_events"]
                if execution_event is not None and isinstance(execution_events, list):
                    execution_events.append(execution_event)
                active_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": output,
                    }
                )

        return RuntimeResult(
            False,
            messages=active_messages,
            usage=total_usage,
            evidence=evidence,
            diagnostics=diagnostics,
            error="maximum steps reached",
            error_class=ErrorCode.BUDGET_STEP_EXCEEDED.value,
            step=self.max_steps,
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
