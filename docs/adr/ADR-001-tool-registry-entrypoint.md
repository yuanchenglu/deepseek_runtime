# ADR-001: ToolRegistry is the only production tool entry point

- Status: Accepted
- Date: 2026-07-27
- Requirements: RUN-003, TOOL-001–TOOL-007, SEC-004

## Context

The current Runtime can receive and invoke bare handlers. That allows parameter validation, policy, approval, timeout, output limits, recovery metadata, and evidence hooks to be bypassed.

## Decision

Every production tool, including built-in tools, is represented by a validated `ToolSpec` and registered in one `ToolRegistry`. Runtime code may resolve and execute tools only through the Registry execution path.

The Registry path must enforce, in order:

1. tool-name lookup;
2. argument schema validation;
3. risk and recovery metadata validation;
4. policy decision and optional approval;
5. execution-adapter limits and cancellation;
6. result normalization;
7. lifecycle, receipt, checkpoint, and evidence emission.

Direct handler invocation is permitted only inside isolated unit tests for the handler itself, never as a production Runtime path.

## Consequences

- Existing `dict[str, handler]` APIs must be removed, made private, or adapted through explicit migration code.
- Provider tool definitions are generated from registered specifications.
- Registry construction fails for duplicate names or incomplete mandatory metadata.
- Tool execution becomes a reviewable security invariant rather than a caller convention.

## Rejected alternatives

- Keep bare handlers and document that callers should run policy first: unenforceable.
- Wrap only high-risk tools: classification mistakes would create a bypass.
- Let each handler implement its own validation and audit: inconsistent and not centrally testable.

## Verification

`TC-RUN-004`, `TC-TOOL-001`–`TC-TOOL-007`, `TC-SEC-004`, and a code-search gate showing no production direct-handler path.
