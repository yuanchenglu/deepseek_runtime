# M1-A Core Contract Evidence

> Pull request: #6
> Validated commit: `408c3929c2a008a916822c50308c88a7fdf3cc6e`
> Workflow: `Minimum CI`
> Run: 38 (`30289181531`)
> Result: `success`
> Release decision: **NO RELEASE**

## 1. Scope

This evidence records contract-level implementation only. It does not mark any end-to-end Runtime, recovery, Workspace or rollback Requirement `Verified`.

## 2. Requirement mapping

| Requirement | Contract evidence | Test evidence | Current status | Remaining blocker |
| --- | --- | --- | --- | --- |
| RUN-004 | `RuntimeState`, `TransitionRule`, 32-edge manifest | transition manifest equality; illegal edge; approval/receipt enforcement | Partial | production Runtime does not emit/enforce the state machine |
| TOOL-001 | immutable `ToolSpec` public type | construction and Provider-definition tests | Partial | ToolRegistry and production registration path absent |
| TOOL-003 | Draft 2020-12 local validation | valid/invalid arguments; safe structural error; mutation isolation | Partial | production handler path bypasses ToolSpec validation |
| TOOL-006 | `RecoveryPolicy` enum and running-call decision | pure/keyed/non-idempotent recovery tests | Partial | Session recovery does not use the policy |
| CHG-010 | opaque `RollbackHandle`; private `ChangeJournalEntry` schema | opacity, roundtrip and relative-path rejection | Partial | durable journal store and ChangeManager migration absent |
| SES-001 | independent `RecoverableCheckpoint` and `PublishableEvidence` | private roundtrip; evidence rejects recoverable fields | Partial | legacy SessionStore remains mixed and unmigrated |
| SES-002 | Provider continuation field in private checkpoint | continuation roundtrip | Partial | real Provider continuation not wired into persistence |
| SES-005 | exact schema version and structured future-version error | `CHECKPOINT_VERSION_UNSUPPORTED` fixture | Partial | migrations and persisted fixture corpus absent |
| SES-007 | explicit uncertain state and recovery actions | non-idempotent running maps to uncertain | Partial | crash window and resume implementation remain unsafe |
| SES-010 | approval/receipt/budget checkpoint fields | roundtrip and transition receipt test | Partial | production persistence not migrated |
| EVD-006 | `publishable-evidence-v1` schema | schema validation and private-field rejection | Partial | current evidence exporter not migrated |
| OSS-004 | versioned transition denominator; ADR-010 | manifest equality test | Partial | branch/line coverage reports and remaining manifests absent |

## 3. CI evidence

Run 38 passed:

- package and dependency installation;
- critical Ruff diagnostics;
- Pyright error gate;
- all existing and new unit tests;
- package import smoke;
- tracked-file secret scan;
- documentation traceability and core-link checks.

The first PR run, Run 37, correctly failed on two Pyright assignment errors in `sanitize_public()`. The fix renamed the list-branch local variable; no type rule was disabled and no contract behavior changed.

## 4. Test inventory added

`tests/test_contracts.py` contains 11 tests covering:

1. safe error-detail redaction;
2. legal/illegal state transitions;
3. approval and receipt requirements;
4. transition manifest synchronization;
5. recovery-policy decisions;
6. immutable ToolSpec schemas and local argument validation;
7. side-effect recovery-policy constraints;
8. private checkpoint roundtrip;
9. future checkpoint version rejection;
10. public evidence private-field rejection;
11. opaque rollback handle, private journal and JSON Schema validation.

## 5. Non-claims

This evidence does not claim:

- ToolRegistry is the production entry point;
- Workspace symlink/reparse-point escape is fixed;
- legacy `RollbackToken` is safe;
- crash-after-effect no longer retries;
- checkpoint storage is encrypted or concurrency-safe;
- P0 repetition tests have passed;
- the repository is ready to release.

M1-B/M1-C/M1-D must close those gaps before M1 can exit.
