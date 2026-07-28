"""ExecutionAdapter contracts and bounded subprocess execution.

The restricted adapter is a process-resource boundary, not a kernel security sandbox.
Tool handlers used with it must be pure builders that return ``SubprocessRequest``.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from .contracts import (
    ContractViolation,
    ErrorCode,
    RuntimeErrorInfo,
    ToolSpec,
)
from .session import ToolExecutionResult
from .workspace import WorkspaceResolver, WorkspaceViolation


class IsolationLevel(str, Enum):
    """Honest isolation classification for an adapter implementation."""

    FAKE = "fake"
    NONE = "none"
    PROCESS_RESTRICTED = "process-restricted"


@dataclass(frozen=True)
class ExecutionCapabilities:
    """Machine-readable adapter guarantees; none imply kernel isolation."""

    isolation: IsolationLevel
    timeout_enforced: bool
    cancellation_enforced: bool
    byte_output_limit: bool
    process_tree_cleanup: bool
    minimal_environment: bool
    kernel_isolation: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "isolation": self.isolation.value,
            "timeout_enforced": self.timeout_enforced,
            "cancellation_enforced": self.cancellation_enforced,
            "byte_output_limit": self.byte_output_limit,
            "process_tree_cleanup": self.process_tree_cleanup,
            "minimal_environment": self.minimal_environment,
            "kernel_isolation": self.kernel_isolation,
        }


class CancellationToken:
    """Thread-safe cancellation signal passed to execution adapters."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class ExecutionContext:
    """Per-call execution context supplied by the Runtime."""

    workspace: Path
    cancellation: CancellationToken | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "workspace", Path(self.workspace))


@dataclass(frozen=True)
class SubprocessRequest:
    """A pure command description produced by a restricted tool handler."""

    command: tuple[str, ...]
    cwd: str | Path = "."
    env: Mapping[str, str] = field(default_factory=dict)
    stdin: bytes | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.command, tuple) or not self.command:
            raise ValueError("subprocess command must be a non-empty tuple")
        if not all(isinstance(item, str) for item in self.command):
            raise ValueError("subprocess command arguments must be text")
        if not self.command[0]:
            raise ValueError("subprocess executable must not be empty")
        if isinstance(self.cwd, bytes):
            raise ValueError("subprocess cwd must be text or Path")
        if not isinstance(self.env, Mapping):
            raise ValueError("subprocess env must be a mapping")
        normalized_env: dict[str, str] = {}
        for key, value in self.env.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("subprocess env keys and values must be text")
            if not key or "=" in key or "\x00" in key or "\x00" in value:
                raise ValueError("subprocess env contains an invalid key or value")
            normalized_env[key] = value
        if self.stdin is not None and not isinstance(self.stdin, bytes):
            raise ValueError("subprocess stdin must be bytes or None")
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "cwd", Path(self.cwd))
        object.__setattr__(self, "env", normalized_env)


@dataclass(frozen=True)
class ExecutionOutcome:
    """Common result envelope returned by every ExecutionAdapter."""

    value: Any
    adapter: str
    capabilities: ExecutionCapabilities
    duration_ms: int
    output_bytes: int = 0
    truncated: bool = False
    returncode: int | None = None
    private_receipt: Mapping[str, Any] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not self.adapter or len(self.adapter) > 128:
            raise ValueError("execution adapter name must contain 1..128 characters")
        if self.duration_ms < 0:
            raise ValueError("execution duration must be non-negative")
        if self.output_bytes < 0:
            raise ValueError("execution output_bytes must be non-negative")

    def evidence(self, *, tool_name: str) -> dict[str, object]:
        """Return content-minimized, publishable execution metadata."""
        return {
            "event": "tool_execution",
            "tool": tool_name,
            "adapter": self.adapter,
            "capabilities": self.capabilities.to_dict(),
            "duration_ms": self.duration_ms,
            "output_bytes": self.output_bytes,
            "truncated": self.truncated,
            "returncode": self.returncode,
        }


class ExecutionAdapter(Protocol):
    """Pluggable boundary for executing one validated ToolSpec call."""

    name: str
    capabilities: ExecutionCapabilities

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        """Execute one validated tool call or raise a structured failure."""
        ...


def _cancelled_error(adapter: str) -> ContractViolation:
    return ContractViolation(
        RuntimeErrorInfo(
            ErrorCode.CANCELLED,
            "tool execution was cancelled",
            details={"adapter": adapter},
        )
    )


def _adapter_handler_error(
    adapter: str,
    tool_name: str,
    exc: BaseException,
) -> ContractViolation:
    return ContractViolation(
        RuntimeErrorInfo(
            ErrorCode.TOOL_EXECUTION_FAILED,
            "execution adapter handler failed",
            details={"adapter": adapter, "tool": tool_name},
            cause_class=type(exc).__name__,
        )
    )


class FakeExecutionAdapter:
    """Deterministic adapter for Runtime and contract tests; never calls handlers."""

    name = "fake"
    capabilities = ExecutionCapabilities(
        isolation=IsolationLevel.FAKE,
        timeout_enforced=True,
        cancellation_enforced=True,
        byte_output_limit=True,
        process_tree_cleanup=True,
        minimal_environment=True,
    )

    def __init__(self, outcomes: Iterable[Any] = ()) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        self.calls.append(
            {
                "tool": spec.name,
                "arguments": dict(arguments),
                "workspace": str(context.workspace),
                "cancelled": bool(context.cancellation and context.cancellation.cancelled),
            }
        )
        if context.cancellation is not None and context.cancellation.cancelled:
            raise _cancelled_error(self.name)
        if not self._outcomes:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.TOOL_EXECUTION_FAILED,
                    "fake execution adapter has no scripted outcome",
                    details={"adapter": self.name, "tool": spec.name},
                )
            )
        value = self._outcomes.pop(0)
        if isinstance(value, BaseException):
            if isinstance(value, ContractViolation):
                raise value
            raise _adapter_handler_error(self.name, spec.name, value) from value
        if isinstance(value, ExecutionOutcome):
            return value
        if isinstance(value, ToolExecutionResult):
            private_receipt = value.receipt
            value = value.value
        else:
            private_receipt = None
        return ExecutionOutcome(
            value=value,
            adapter=self.name,
            capabilities=self.capabilities,
            duration_ms=0,
            private_receipt=private_receipt,
        )


class NoIsolationLocalAdapter:
    """Direct in-process handler execution for trusted local development only."""

    name = "no-isolation-local"
    capabilities = ExecutionCapabilities(
        isolation=IsolationLevel.NONE,
        timeout_enforced=False,
        cancellation_enforced=False,
        byte_output_limit=False,
        process_tree_cleanup=False,
        minimal_environment=False,
    )

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        if context.cancellation is not None and context.cancellation.cancelled:
            raise _cancelled_error(self.name)
        started = time.monotonic()
        try:
            value = spec.handler(arguments)
        except ContractViolation:
            raise
        except Exception as exc:
            raise _adapter_handler_error(self.name, spec.name, exc) from exc
        if isinstance(value, ToolExecutionResult):
            private_receipt = value.receipt
            value = value.value
        else:
            private_receipt = None
        return ExecutionOutcome(
            value=value,
            adapter=self.name,
            capabilities=self.capabilities,
            duration_ms=max(0, int((time.monotonic() - started) * 1000)),
            private_receipt=private_receipt,
        )


_ENV_ALLOWLIST = {
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "PATHEXT",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USERPROFILE",
    "WINDIR",
}
_SECRET_ENV_MARKERS = (
    "API_KEY",
    "APIKEY",
    "AUTHORIZATION",
    "BEARER",
    "CREDENTIAL",
    "PASSWORD",
    "SECRET",
    "TOKEN",
)


def _is_secret_env_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in _SECRET_ENV_MARKERS)


def _minimal_environment(explicit: Mapping[str, str]) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in _ENV_ALLOWLIST and not _is_secret_env_key(key)
    }
    for key, value in explicit.items():
        if not _is_secret_env_key(key):
            environment[key] = value
    return environment


def _terminate_process_tree(process: subprocess.Popen[bytes], grace_seconds: float) -> None:
    """Best-effort process-tree termination on the three supported platforms."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=max(1.0, grace_seconds),
                env=_minimal_environment({}),
            )
        except (OSError, subprocess.SubprocessError):
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            process.terminate()
        try:
            process.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()
    try:
        process.wait(timeout=max(1.0, grace_seconds))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=max(1.0, grace_seconds))


def _read_stream(
    stream: Any,
    sink: bytearray,
    total: list[int],
    lock: threading.Lock,
    overflow: threading.Event,
    max_output_bytes: int,
) -> None:
    try:
        while True:
            chunk = stream.read(4096)
            if not chunk:
                return
            with lock:
                total[0] += len(chunk)
                remaining = max(0, max_output_bytes - len(sink))
                if remaining:
                    sink.extend(chunk[:remaining])
                if total[0] > max_output_bytes:
                    overflow.set()
    finally:
        try:
            stream.close()
        except OSError:
            pass


class RestrictedSubprocessAdapter:
    """Bounded subprocess adapter without kernel-level isolation guarantees."""

    name = "restricted-subprocess"
    capabilities = ExecutionCapabilities(
        isolation=IsolationLevel.PROCESS_RESTRICTED,
        timeout_enforced=True,
        cancellation_enforced=True,
        byte_output_limit=True,
        process_tree_cleanup=True,
        minimal_environment=True,
    )

    def __init__(self, *, poll_interval: float = 0.02, termination_grace: float = 0.5) -> None:
        if poll_interval <= 0 or termination_grace <= 0:
            raise ValueError("adapter timing values must be positive")
        self.poll_interval = float(poll_interval)
        self.termination_grace = float(termination_grace)

    @staticmethod
    def _contract_error(code: ErrorCode, message: str, **details: object) -> ContractViolation:
        return ContractViolation(RuntimeErrorInfo(code, message, details=details))

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome:
        if context.cancellation is not None and context.cancellation.cancelled:
            raise _cancelled_error(self.name)

        try:
            built = spec.handler(arguments)
        except ContractViolation:
            raise
        except Exception as exc:
            raise _adapter_handler_error(self.name, spec.name, exc) from exc
        private_receipt: Mapping[str, Any] | None = None
        if isinstance(built, ToolExecutionResult):
            private_receipt = built.receipt
            built = built.value
        if not isinstance(built, SubprocessRequest):
            raise self._contract_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                "restricted adapter requires a SubprocessRequest",
                adapter=self.name,
                tool=spec.name,
                result_type=type(built).__name__,
            )

        try:
            resolver = WorkspaceResolver(context.workspace)
            cwd = resolver.resolve(built.cwd)
        except WorkspaceViolation as exc:
            raise self._contract_error(
                ErrorCode.SANDBOX_VIOLATION,
                "subprocess cwd is outside the workspace or otherwise unsafe",
                adapter=self.name,
                tool=spec.name,
                cause_class=type(exc).__name__,
            ) from exc

        environment = _minimal_environment(built.env)
        creationflags = 0
        start_new_session = os.name != "nt"
        if os.name == "nt":
            creationflags = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))

        started = time.monotonic()
        try:
            process = subprocess.Popen(
                built.command,
                cwd=cwd,
                env=environment,
                shell=False,
                stdin=subprocess.PIPE if built.stdin is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=start_new_session,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise self._contract_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                "restricted subprocess could not be started",
                adapter=self.name,
                tool=spec.name,
                cause_class=type(exc).__name__,
            ) from exc

        if process.stdout is None or process.stderr is None:
            _terminate_process_tree(process, self.termination_grace)
            raise self._contract_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                "restricted subprocess pipes were not created",
                adapter=self.name,
                tool=spec.name,
            )

        stdout_buffer = bytearray()
        stderr_buffer = bytearray()
        total_output = [0]
        output_lock = threading.Lock()
        overflow = threading.Event()
        readers = (
            threading.Thread(
                target=_read_stream,
                args=(
                    process.stdout,
                    stdout_buffer,
                    total_output,
                    output_lock,
                    overflow,
                    spec.max_output_bytes,
                ),
                daemon=True,
            ),
            threading.Thread(
                target=_read_stream,
                args=(
                    process.stderr,
                    stderr_buffer,
                    total_output,
                    output_lock,
                    overflow,
                    spec.max_output_bytes,
                ),
                daemon=True,
            ),
        )
        for reader in readers:
            reader.start()

        if built.stdin is not None and process.stdin is not None:
            try:
                process.stdin.write(built.stdin)
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        deadline = started + spec.timeout_seconds
        stop_reason: str | None = None
        while process.poll() is None:
            if context.cancellation is not None and context.cancellation.cancelled:
                stop_reason = "cancelled"
                break
            if overflow.is_set():
                stop_reason = "output-limit"
                break
            if time.monotonic() >= deadline:
                stop_reason = "timeout"
                break
            time.sleep(self.poll_interval)

        if stop_reason is not None:
            _terminate_process_tree(process, self.termination_grace)

        for reader in readers:
            reader.join(timeout=max(1.0, self.termination_grace * 2))

        duration_ms = max(0, int((time.monotonic() - started) * 1000))
        if stop_reason == "cancelled":
            raise _cancelled_error(self.name)
        if stop_reason == "timeout":
            raise self._contract_error(
                ErrorCode.TOOL_TIMEOUT,
                "tool execution exceeded its registered timeout",
                adapter=self.name,
                tool=spec.name,
                timeout_seconds=spec.timeout_seconds,
            )

        stdout_raw = bytes(stdout_buffer)
        stderr_raw = bytes(stderr_buffer)
        retained_stdout = stdout_raw[: spec.max_output_bytes]
        remaining = max(0, spec.max_output_bytes - len(retained_stdout))
        retained_stderr = stderr_raw[:remaining]
        truncated = overflow.is_set() or total_output[0] > spec.max_output_bytes
        value = {
            "returncode": process.returncode,
            "stdout": retained_stdout.decode("utf-8", errors="replace"),
            "stderr": retained_stderr.decode("utf-8", errors="replace"),
            "truncated": truncated,
        }
        receipt = dict(private_receipt or {})
        receipt.update(
            {
                "adapter": self.name,
                "returncode": process.returncode,
                "output_bytes": total_output[0],
                "truncated": truncated,
            }
        )
        return ExecutionOutcome(
            value=value,
            adapter=self.name,
            capabilities=self.capabilities,
            duration_ms=duration_ms,
            output_bytes=total_output[0],
            truncated=truncated,
            returncode=process.returncode,
            private_receipt=receipt,
        )
