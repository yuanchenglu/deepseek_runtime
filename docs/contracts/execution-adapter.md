# ExecutionAdapter Contract

> Contract status: M2-C implementation draft  
> Implementation PR: #18  
> Production path: `Registry → Schema → Policy → Approval → ExecutionAdapter → normalization`  
> Release status: **NO RELEASE**

## 1. Scope

This contract defines the single execution boundary used after a tool call has been resolved, validated, and authorized. It covers in-process compatibility execution and bounded subprocess execution.

It does not provide or claim container, virtual-machine, seccomp, Seatbelt, Job Object, namespace, or other kernel-level isolation. It does not define the complete Runtime lifecycle, durable checkpoint timing, budgets, Provider cancellation, or recovery state machine.

## 2. Common interface

Every adapter implements:

```python
class ExecutionAdapter(Protocol):
    name: str
    capabilities: ExecutionCapabilities

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome: ...
```

Runtime ordering is mandatory:

1. parse Provider tool call;
2. resolve `ToolSpec` from `ToolRegistry`;
3. validate arguments with the registered JSON Schema;
4. obtain `PermissionPolicy` decision;
5. complete `ApprovalProvider` when decision is `ASK`;
6. invoke exactly one `ExecutionAdapter`;
7. normalize `ExecutionOutcome.value` or return a structured error;
8. emit content-minimized execution evidence.

Schema failure, Policy denial, Approval denial/timeout/unavailability, unknown tool, or malformed tool call must not invoke the Adapter.

## 3. Capability model

`ExecutionCapabilities` is machine-readable and must accurately describe the selected adapter:

- `isolation`: `fake`, `none`, or `process-restricted`;
- `timeout_enforced`;
- `cancellation_enforced`;
- `byte_output_limit`;
- `process_tree_cleanup`;
- `minimal_environment`;
- `kernel_isolation`.

For all current M2-C adapters, `kernel_isolation` is `false`.

Capability metadata is evidence, not a security mechanism. An adapter must not claim a capability that its implementation and automated tests do not enforce.

## 4. Adapter types

### 4.1 FakeExecutionAdapter

Purpose: deterministic tests and fault injection.

Guarantees:

- never calls the registered handler;
- returns scripted outcomes;
- records test-only calls;
- supports deterministic cancellation and structured failures.

It is not a production isolation mechanism.

### 4.2 NoIsolationLocalAdapter

Purpose: compatibility with trusted local Python handlers.

Guarantees:

- calls the registered handler in the current Python process;
- rejects cancellation only when the token is already cancelled before execution;
- converts handler exceptions to `TOOL_EXECUTION_FAILED` without exception message disclosure.

Non-guarantees:

- no timeout enforcement;
- no cancellation after handler start;
- no output byte enforcement;
- no process-tree cleanup;
- no environment minimization;
- no OS or kernel isolation.

Runtime evidence must expose these non-guarantees. This adapter is only appropriate for trusted local tools.

### 4.3 RestrictedSubprocessAdapter

Purpose: bounded subprocess execution for handlers that are pure command builders.

A registered handler used with this adapter must return `SubprocessRequest`; it must not execute the command itself. Builder exceptions are structured and their messages are not published.

Enforced controls:

- command is an argument tuple; shell strings are rejected;
- `shell=False`;
- cwd is explicit and resolved through `WorkspaceResolver`;
- cwd outside the workspace or through a prohibited link/reparse point is rejected;
- child environment begins from a small host allowlist;
- environment keys containing secret markers such as API key, token, authorization, password, credential, or secret are removed, including explicit overrides;
- ToolSpec `timeout_seconds` is enforced;
- combined stdout/stderr is bounded by ToolSpec `max_output_bytes` measured in bytes;
- cancellation is polled while the child runs;
- timeout, cancellation, and output overflow terminate the process tree on supported platforms;
- output is decoded as UTF-8 with replacement after byte enforcement;
- result and errors use structured contracts.

Non-guarantees:

- no filesystem, network, syscall, user, namespace, or kernel isolation;
- the process may access any resource available to the same host user unless separately restricted by the operating environment;
- process-tree cleanup is best-effort against hostile processes and must be verified per supported platform;
- universal exactly-once behavior is not provided.

## 5. SubprocessRequest

`SubprocessRequest` contains private execution input:

- `command: tuple[str, ...]`;
- `cwd: str | Path` relative to the Runtime workspace;
- optional explicit environment additions;
- optional byte stdin.

The request is not publishable evidence. Command arguments, cwd, environment values, and stdin must not be copied into public evidence or errors.

Environment keys and values must be valid subprocess strings. Secret-like environment keys are silently excluded from the child environment rather than echoed in an error.

## 6. Result and errors

`ExecutionOutcome` contains:

- private `value` for Runtime normalization;
- adapter name and capabilities;
- duration in milliseconds;
- total observed output bytes;
- truncation flag;
- return code;
- optional private receipt.

Expected structured errors include:

- `SANDBOX_VIOLATION`: unsafe cwd;
- `TOOL_TIMEOUT`: registered timeout exceeded;
- `CANCELLED`: cancellation reached the Adapter;
- `TOOL_EXECUTION_FAILED`: builder, handler, spawn, pipe, or adapter failure;
- `TOOL_RESULT_INVALID`: malformed result or normalization failure.

Public error fields may contain tool name, adapter name, limit values, and exception class. They must not contain exception messages, command text, environment values, stdin, stdout, stderr, prompt, response, or tool arguments.

## 7. Execution evidence

Each attempted Adapter execution emits one content-minimized event after authorization:

- tool name;
- adapter name;
- capability map;
- succeeded/failed status;
- duration;
- output byte count;
- truncated flag;
- return code;
- structured error code and exception class when applicable.

Execution evidence must not include:

- arguments;
- command or cwd;
- environment;
- stdin;
- stdout or stderr;
- handler/builder exception messages;
- result value or private receipt.

No execution event is emitted when Registry, schema, Policy, or Approval rejects the call before the Adapter boundary.

## 8. WorkspaceSandbox compatibility path

`WorkspaceSandbox.run()` remains a compatibility API, but it must not call `subprocess.run` directly. It performs:

1. command array validation and risk classification;
2. workspace cwd resolution;
3. `PermissionPolicy` decision;
4. construction of a temporary ToolSpec and `SubprocessRequest`;
5. delegation to its configured `ExecutionAdapter`;
6. validation and conversion to the legacy `CommandResult` envelope.

The default compatibility adapter is `RestrictedSubprocessAdapter`. The class name does not imply kernel isolation.

## 9. Cross-platform gate

PR #18 must pass the focused `M2 ExecutionAdapter Gate` on:

- Ubuntu / Python 3.11;
- macOS / Python 3.11;
- Windows / Python 3.11.

The gate covers Adapter contracts, minimal child environment, cwd containment, timeout, byte output limit, cancellation handoff, descendant cleanup, Runtime ordering, WorkspaceSandbox migration, and error/evidence privacy. Each job uploads a JSON evidence file with an explicit test denominator.

## 10. Deferred boundaries

M2-C intentionally defers:

- complete Runtime state transitions and checkpoint timing;
- token/cost/context/time budgets;
- Provider cancellation before or during HTTP requests;
- durable cancellation/resume semantics;
- Workspace read/search byte/file/time budgets;
- CLI output/report/JSON protocol;
- recovery receipt/idempotency integration;
- M3 Evidence redesign;
- any kernel sandbox.
