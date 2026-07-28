# DeepSeek Runtime Core Contracts

> Contract version: 1.0
> Milestone: M1-A
> Status: implemented as types and schemas; legacy Runtime wiring remains pending

## 1. Scope

This document freezes the minimum contracts required before P0 Workspace, rollback, and side-effect recovery work.

The contract package does **not** create a second production Agent loop. Existing `DeepSeekRuntime`, `SessionState`, and `ChangeManager` remain the only current execution path until later M1/M2 migration PRs replace their internal data flow with these contracts.

## 2. Authority

The normative artifacts are:

- Python types under `src/deepseek_runtime/contracts/`;
- JSON Schemas under `docs/schemas/`;
- `docs/contracts/runtime-state-transitions.json`;
- ADR-002, ADR-003, ADR-005, ADR-007, ADR-009, and ADR-010.

When prose and machine-readable artifacts disagree, implementation stops until the inconsistency is corrected.

## 3. Error Contract

`RuntimeErrorInfo` provides:

- schema version;
- stable `ErrorCode`;
- bounded human-readable message;
- retry eligibility;
- content-safe structural details;
- optional exception class, never raw traceback or secret value.

Public serialization removes forbidden fields such as `content`, `messages`, `arguments`, `result`, `api_key`, `authorization`, and `reasoning_content`.

Unknown internal exceptions must eventually map to `INTERNAL_ERROR`; callers must not branch on Python exception text.

## 4. Runtime State Contract

`RuntimeState` defines the lifecycle:

```text
CREATED
→ PROVIDER_PENDING
→ PROVIDER_COMPLETED
→ TOOL_REQUESTED
→ APPROVAL_PENDING?
→ TOOL_RUNNING
→ TOOL_SUCCEEDED | TOOL_FAILED | TOOL_SIDE_EFFECT_UNCERTAIN
→ PROVIDER_PENDING
→ COMPLETED | FAILED | CANCELLED | BUDGET_EXCEEDED
```

The transition manifest defines for every legal edge:

- lifecycle event;
- whether a checkpoint is required;
- recovery eligibility;
- retry eligibility;
- approval requirement;
- receipt requirement.

An edge absent from the manifest is illegal. Side-effect success requires a receipt record. `TOOL_SIDE_EFFECT_UNCERTAIN` has no implicit automatic progress path.

## 5. Tool and Recovery Contract

`ToolSpec` contains:

- name and description;
- immutable JSON Schema Draft 2020-12 parameters;
- handler;
- risk;
- side-effect flag;
- timeout and output byte limits;
- `RecoveryPolicy`.

The same schema generates Provider tool definitions and validates local arguments. Provider output is untrusted; handler execution must occur only after local validation.

Recovery policies:

| Policy | Running-call recovery |
| --- | --- |
| `PURE` | automatic retry permitted within budget |
| `IDEMPOTENT` | automatic retry permitted under declared contract |
| `RETRYABLE_WITH_KEY` | retry only when stable idempotency key exists |
| `NON_IDEMPOTENT` | transition to uncertain; no automatic retry |
| `MANUAL_RECONCILIATION` | explicit operator decision required |

A side-effect tool cannot register with `PURE`. A non-side-effect tool currently uses `PURE`; broader read-only policies require a future contract revision.

## 6. Recoverable Checkpoint

`RecoverableCheckpoint` is private local state. It may contain:

- messages and Provider continuation;
- tool arguments and results;
- per-call state, recovery policy, attempts, approval and receipt;
- budgets and recovery metadata.

It deliberately contains no public evidence field. Future schema versions fail with `CHECKPOINT_VERSION_UNSUPPORTED`; malformed supported-version data fails with `CHECKPOINT_CORRUPT`.

Encryption-at-rest and durable store migration are M3 implementation work. The existence of a private schema does not make plaintext storage acceptable for release.

## 7. Publishable Evidence

`PublishableEvidence` contains only structural and redacted data:

- state and transition records;
- request/response structure, lengths, identities and flags;
- usage and cost summaries;
- machine-readable safe errors;
- bounded metadata.

It rejects recoverable field names, including messages, content, arguments, results and secrets. It must never be used as a resume source.

## 8. Rollback Handle and ChangeJournal

`RollbackHandle` exposes only:

- schema version;
- random opaque handle ID.

The caller cannot provide paths, original bytes, hashes, workspace identity, expiry or consumed state.

`ChangeJournalEntry` is private durable state containing workspace/change-set identity, relative paths, pre/post hashes, recovery bytes, mode, expiry, protection and consumed status.

The current contract validates shape only. M1-C must implement protected persistence, lookup, workspace binding, expiry, post-change conflict checks and one-time consumption.

## 9. Compatibility

Schema version `1.0` is exact. A future incompatible field or state change requires:

1. a new schema version;
2. migration or structured unsupported-version behavior;
3. updated ADR and transition manifest;
4. compatibility fixtures;
5. explicit public API review.

Silent interpretation of unknown states, fields or policies is prohibited.

## 10. Current limitations

This PR freezes and tests contracts but does not yet:

- route production tools through ToolRegistry;
- migrate `SessionStore` to `RecoverableCheckpoint`;
- replace legacy `RollbackToken`;
- fix Workspace symlink escape;
- change `resume_tool_calls()` uncertain semantics;
- implement encryption, locks, budgets or durable journal storage.

Those limitations remain P0/P1 blockers. Repository status remains **NO RELEASE**.
