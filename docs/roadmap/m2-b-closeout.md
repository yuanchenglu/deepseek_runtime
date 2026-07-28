# M2-B Policy and Approval Closeout

> Status date: 2026-07-28  
> Implementation PR: #16 `feat(security): enforce M2-B policy and approval path`  
> Merge commit: `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`  
> Release decision: **NO RELEASE**

## 1. Decision

M2-B is **CLOSED** for its scoped in-memory production authorization path.

The merged Runtime path is:

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider (ASK only)
→ handler
→ result normalization
```

This closeout does not claim durable approval checkpoint timing, resume behavior, migration, ExecutionAdapter enforcement, subprocess isolation, budgets, cancellation, Workspace P1, or CLI protocol completion.

## 2. Merged scope

PR #16 added and enforced:

- `ApprovalOutcome`, `ApprovalRequest`, `ApprovalProvider`, `AuthorizationEvent`, and `AuthorizationSession`;
- default `READ=ALLOW` and non-READ `DENY`;
- deterministic declaration-order rule evaluation with the existing last-match precedence;
- missing-path protection for path-specific rules;
- approve-once and exact-request approve-session semantics;
- fail-closed behavior for deny, timeout, missing provider, provider exception, and invalid outcome;
- authorization before every supported `DeepSeekRuntime` handler execution;
- content-minimized approval summaries, evidence, errors, and policy audit records;
- distinct audit semantics for direct Policy denial and human denial after ASK;
- checkpoint-compatible authorization event records.

## 3. Requirement disposition

| Requirement | Test | Closeout status | Remaining boundary |
| --- | --- | --- | --- |
| `SEC-001` | `TC-SEC-001` | Verified | none in M2-B scope |
| `SEC-002` | `TC-SEC-002` | Verified | none in M2-B scope |
| `SEC-003` | `TC-SEC-003` | Partial | durable checkpoint timing, resume, and migration remain M2-D/M3 |
| `SEC-004` | `TC-SEC-004` | Verified | ExecutionAdapter remains M2-C |
| `SEC-009` | `TC-SEC-008` | Partial | subprocess environment and adapter error surfaces remain M2-C |

## 4. Retained failure evidence

The following failures remain visible and were not rerun away:

1. Minimum CI run 114 (`30331798350`) — ErrorCode/schema mismatch caused Pyright failure.
2. Minimum CI run 122 (`30332543894`) — an accidental Policy precedence change caused unit regression.
3. Minimum CI run 127 (`30333987276`) — audit semantics incorrectly represented direct Policy denial as human approval denial.

Each failure was fixed at the implementation or contract layer without casts, rule weakening, assertion weakening, or deletion of evidence.

## 5. Final PR evidence

Final PR head: `7e2913204b89164ba10ec3c43c03ab7bd69435af`.

- Minimum CI run 129 (`30340272861`): PASS.
  - critical Ruff rules;
  - Pyright `errorCount=0`;
  - complete unit suite;
  - package import smoke;
  - tracked-secret scan;
  - documentation traceability/link checks.
- M1 P0 Gate run 77 (`30340272870`): PASS.
  - Linux/Python 3.11;
  - macOS/Python 3.11;
  - Windows/Python 3.11.
- Strict review unresolved P0/S0/S1 findings: 0.

## 6. Explicit exclusions

M2-B did not implement:

- ExecutionAdapter;
- minimal child environment;
- actual subprocess timeout enforcement;
- byte-size stdout/stderr enforcement;
- process-tree cleanup;
- cancellation;
- token/cost/context/time budgets;
- durable approval checkpoint timing or store;
- Workspace P1;
- CLI stdout/report/JSON protocol;
- M3 Evidence redesign.

## 7. Handoff

The next execution slice is M2-C on a fresh branch from the latest `develop`:

```text
agent/m2-execution-adapter
```

M2-C must remain focused on the ExecutionAdapter boundary and its direct tests/docs. Repository status remains **NO RELEASE**.
