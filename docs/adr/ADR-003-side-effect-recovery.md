# ADR-003: Side effects require explicit recovery semantics

- Status: Accepted
- Date: 2026-07-27
- Requirements: TOOL-006, SES-006–SES-010

## Context

A process can crash after an external effect succeeds but before success is checkpointed. Treating every `running` call as retryable can duplicate payments, messages, writes, or remote mutations. A local Runtime cannot prove universal exactly-once behavior for arbitrary external systems.

## Decision

Every tool declares one `RecoveryPolicy`:

- `PURE`: no externally observable side effect; retry is allowed within budget.
- `IDEMPOTENT`: repeated execution is safe under the declared contract.
- `RETRYABLE_WITH_KEY`: retry requires a stable idempotency key and bounded attempts.
- `NON_IDEMPOTENT`: an ambiguous running state becomes uncertain and cannot auto-retry.
- `MANUAL_RECONCILIATION`: recovery always requires an explicit operator decision.

The Runtime persists call identity, policy, attempt count, idempotency key where applicable, approval, and receipt. On recovery:

- confirmed `succeeded` is never re-executed;
- `TOOL_SIDE_EFFECT_UNCERTAIN` stops automatic progress;
- operator actions are `mark-succeeded`, `mark-not-executed`, `explicit-retry`, or `abandon`;
- every operator action is checkpointed and represented in safe evidence.

## Consequences

- Side-effect tools without a recovery policy cannot register.
- Retry/backoff is policy- and budget-bound, not a generic exception handler.
- Receipts can support reconciliation but are not proof of exactly-once execution unless the external system contract provides it.
- User experience must expose uncertainty rather than converting it to success or failure silently.

## Rejected alternatives

- Retry every incomplete call: unsafe duplication.
- Never retry any call: unnecessarily blocks pure/idempotent work.
- Infer side effects from tool names or commands: unreliable and bypassable.
- Claim exactly-once using only a local idempotency key: the external system may ignore it.

## Verification

`TC-TOOL-007`, `TC-SES-006`–`TC-SES-010`, and fault injection at effect-before-checkpoint, after-success-checkpoint, and failed-before-effect windows.
