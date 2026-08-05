# M1-D Uncertain Side-effect Recovery Evidence

> Pull request: #9
> Stacked base: PR #8 (`agent/m1-rollback-p0`)
> Validated production commit: `76a2976a4ce71b1f371f9d10d53fb00429d83b3b`
> Workflow: `Minimum CI`
> Initial implementation run: 51 (`30292433040`), `success`
> Compatibility/refinement run: 52 (`30292641575`), expected test failure
> Diagnostic run: 53 (`30292766515`), exact failing assertion retained
> Corrected implementation run: 55 (`30292898991`), `success`
> Standard final validation: 56 (`30293105963`), `success`
> Release decision: **NO RELEASE**

## 1. Scope

The production `ToolCallRecord` and `resume_tool_calls()` path now uses explicit `RecoveryPolicy` semantics.

- Legacy `side_effect=True` records default to `NON_IDEMPOTENT` rather than automatic retry.
- A persisted `running` non-idempotent/manual side effect transitions to `side-effect-uncertain` and is not executed.
- Pure, idempotent, or keyed operations retry only when their declared policy and attempt budget permit it.
- Side-effect handlers are checkpointed as `running` before invocation.
- Successful side effects retain a handler/external structural receipt.
- Handler exceptions after side-effect execution begins become uncertain unless automatic retry is explicitly safe.
- Missing handlers produce `TOOL_NOT_FOUND` rather than an unhandled `KeyError`.
- Operators may record `mark-succeeded`, `mark-not-executed`, `explicit-retry`, or `abandon` decisions.
- `SessionState` schema is now `1.1`; supported `1.0` records migrate to the new in-memory model, while future versions are rejected.

## 2. Requirement mapping

| Requirement | Implementation | Test evidence | Current status | Remaining evidence |
| --- | --- | --- | --- | --- |
| SES-007 | persisted `running` non-idempotent call becomes uncertain; repeated resume is a no-op | simulated crash after external effect but before result checkpoint; effect count remains exactly one | Partial | process-level crash/fault injection and consolidated P0 report |
| TOOL-006 | `RecoveryPolicy` controls pure/idempotent/keyed/non-idempotent behavior | pure replay, keyed replay, missing-key uncertain and non-idempotent exception tests | Partial | ToolRegistry registration enforcement in M2 |
| SES-009 | attempt count plus `max_attempts`; unsafe calls need explicit retry authorization | failed/retry budget behavior and explicit retry test | Partial | fake-clock backoff and complete retry schedule in M3 |
| SES-010 | attempt, receipt, idempotency, recovery and operator metadata persist | SessionStore 1.1 roundtrip and 1.0 migration tests | Partial | migration to separate RecoverableCheckpoint store in M3 |

## 3. Crash-window proof

The central test performs this sequence:

1. persist the call as `running`;
2. execute the external-effect handler once;
3. simulate a crash before the succeeded result is durably saved;
4. restore the last durable `running` checkpoint;
5. invoke resume repeatedly;
6. verify the handler is never called again and state becomes `side-effect-uncertain`.

This directly exercises the known P0 window rather than inferring safety from static control flow.

## 4. Operator reconciliation

| Action | Result | Automatic execution |
| --- | --- | --- |
| `mark-succeeded` | `succeeded` with external/operator receipt | Never |
| `mark-not-executed` | reconciled `failed` state | Never |
| `explicit-retry` | `pending` with one persisted retry authorization | Runs only on a later resume |
| `abandon` | terminal reconciled `failed` state with uncertain error code | Never |

A reconciled `mark-not-executed` or `abandon` record is not automatically converted back to uncertain.

## 5. Validation history

- Run 51 passed the first production migration.
- Review identified two contract issues: new legacy fields required a schema migration, and old failed non-idempotent side effects required an operator path.
- Run 52 correctly failed one test because `ABANDON` was being reclassified as uncertain.
- Run 53 uploaded the complete unittest artifact and isolated that single assertion.
- The rule was narrowed so only **unreconciled** failed side effects become uncertain.
- Run 55 passed after that correction.
- Run 56 passed the standard read-only repository workflow against the final production contents.

All successful runs passed Ruff, Pyright, unit tests, import smoke, tracked-secret scan and documentation checks. No lint, type, or test rule was disabled.

## 6. Non-claims

This change does not claim:

- external exactly-once semantics;
- a local `handler-returned` receipt proves an external system committed the effect;
- retry backoff and time budgets are complete;
- the legacy SessionStore is encrypted, locked, or separated from Publishable Evidence;
- ToolRegistry currently enforces RecoveryPolicy at registration;
- multi-process reconciliation is serialized;
- platform-wide P0 evidence is complete.

Those remain M2/M3/M5 work. Repository status remains **NO RELEASE**.
