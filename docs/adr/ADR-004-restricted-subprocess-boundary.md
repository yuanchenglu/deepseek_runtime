# ADR-004: Restricted subprocess execution is not OS isolation

- Status: Accepted
- Date: 2026-07-27
- Requirements: SEC-005–SEC-008

## Context

Command classification, a workspace `cwd`, environment filtering, timeout, and process cleanup reduce accidental harm but cannot prevent an interpreter, wrapper, child process, or native program from accessing resources allowed to the host user. Calling this mechanism a sandbox creates a false security guarantee.

## Decision

The Alpha exposes explicit execution-adapter levels:

- `NoIsolationLocalAdapter`: trusted local development only; no OS isolation.
- `RestrictedSubprocessAdapter`: minimal environment, explicit cwd, timeout, process-tree cleanup, cancellation, output limits, and structured errors; still no kernel isolation.
- `SandboxAdapter`: interface for future container or platform-specific isolation implementations.

Documentation, API names, diagnostics, and CLI output must state the active adapter and its guarantees. `RestrictedSubprocessAdapter` must not be described as secure isolation, containment against a malicious same-user process, or a multi-tenant boundary.

## Consequences

- Command policy remains a governance gate, not an isolation primitive.
- Dangerous operations are denied by default, but allowed commands still execute with host-user privileges.
- Container/Seatbelt/Job Object implementations may be added later without changing Runtime orchestration contracts.
- Threat-model tests verify truthful naming and behavior in addition to functional limits.

## Rejected alternatives

- Rename the current command gate as a sandbox: materially misleading.
- Parse shell commands deeply enough to prove safety: wrappers, interpreters, native code, and runtime behavior make this infeasible.
- Block Alpha until every platform has kernel isolation: expands scope without closing the immediate contract and honesty gaps.

## Verification

`TC-SEC-005`–`TC-SEC-009`, process-tree tests on supported platforms, environment-leak tests, and documentation/diagnostic assertions that expose the adapter level.
