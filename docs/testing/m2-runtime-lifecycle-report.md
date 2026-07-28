# M2-D Runtime Lifecycle Test Report

> Report status: implementation PR in progress
> Implementation PR: #20 `feat(runtime): establish M2-D lifecycle and budget path`
> Release decision: **NO RELEASE**

## 1. Scope

This report covers:

- validated Runtime lifecycle transitions;
- content-minimized lifecycle events;
- private RecoverableCheckpoint handoff;
- Provider-before-call cancellation;
- tool-during-cancel terminal semantics;
- step/token/cost/context/time budgets;
- unknown usage/cost preservation;
- tool-error continue/terminate policy;
- supported malformed-Provider RuntimeResult boundaries;
- M1 and M2-C regression gates.

It does not claim:

- durable/encrypted/locked checkpoint storage;
- complete checkpoint migration/resume;
- in-flight Provider transport cancellation;
- full Provider normalization/retry/streaming/body limits;
- Workspace P1 budgets;
- CLI protocol;
- M3 Evidence totality/canonical/redaction;
- release readiness.

## 2. Retained failures

### Minimum CI run 184 (`30355769206`) — FAIL

- Ruff: PASS;
- Pyright: PASS;
- full unit suite: FAIL;
- root causes recovered through the first M2-D structured artifact:
  - test helper privacy assertion matched benign text;
  - pre-cancelled legacy Adapter test conflicted with new Provider-before-call cancellation;
  - UTF-8 bytes were not checkpoint JSON-compatible;
  - successful side-effect local/fake execution lacked structural receipts;
  - transition JSON manifest lacked `TOOL_RUNNING → CANCELLED`.

### M2 Runtime Lifecycle Gate run 1 (`30356166222`) — FAIL

- Linux artifact: `8686877838`;
- denominator: 52 tests;
- result: 5 failures, 2 errors;
- the artifact retained full tracebacks;
- all root causes above were fixed without reducing lifecycle, schema, receipt, or cancellation assertions.

### Minimum CI run 199 (`30358472836`) — FAIL

- M2-D focused Gate run 4 was green on three platforms;
- full unit suite exposed one compatibility regression outside the focused denominator;
- exact root cause: the prior M2-C cancellation test cancelled immediately after Provider response, so M2-D correctly stopped before Adapter execution and produced no tool message;
- fix: the test now schedules cancellation from the command builder after Restricted subprocess execution begins, using a non-side-effect ToolSpec to preserve the expected `CANCELLED` terminal state.

### M2 Runtime Lifecycle Gate run 13 (`30358197108`) — FAIL

- focused failure: same legacy cancellation test;
- temporary full-unit diagnostic initially reported `scripts` import errors because the diagnostic script did not add the repository root to `sys.path`;
- the diagnostic path was corrected, full unit passed, and the temporary diagnostic job/script were removed before finalization.

All failed runs remain retained. None were rerun to replace their conclusions, deleted, or hidden.

## 3. Focused gate

Permanent workflow: `M2 Runtime Lifecycle Gate`.

The gate runs on Linux, macOS, and Windows with Python 3.11 and uploads one JSON artifact per platform containing:

- explicit test denominator;
- failures/errors/skips with tracebacks;
- expected failures/unexpected successes;
- platform and Python version;
- final success state.

Covered modules:

- `test_runtime_lifecycle.py`;
- `test_runtime_lifecycle_review.py`;
- `test_execution_runtime.py`;
- `test_tool_registry_runtime.py`;
- `test_policy_approval_runtime.py`;
- `test_policy_approval_audit_semantics.py`;
- transition manifest equality test.

## 4. Strict review cases

Additional review tests prove:

- `PROVIDER_COMPLETED` checkpoint contains the assistant message and Provider continuation;
- real ASK checkpoint contains `approval_outcome="pending"` before host approval I/O;
- unknown usage strings do not enter public evidence;
- terminate policy preserves original `TOOL_ARGUMENT_INVALID` or other machine code;
- multi-tool batch records the first real approval pending without inventing per-call state machines;
- reaching token/cost/context/time thresholds stops execution;
- generic `cost` is not interpreted as USD;
- lifecycle event counts have no off-by-one error;
- negative lifecycle steps are rejected;
- successful side-effect execution has a private structural receipt;
- pure cancellation ends in `CANCELLED`;
- ambiguous side-effect cancellation ends in `TOOL_SIDE_EFFECT_UNCERTAIN`.

## 5. Current implementation assessment

Before PR #20 merges:

- code and direct tests are `Implemented`;
- Requirement rows remain `Implemented` or `Partial`, not `Verified`;
- final exact-head CI and artifacts must be inserted before Ready;
- merged-state promotion is reserved for a docs-only M2-D closeout after squash merge.

## 6. Remaining blockers

- final exact-head Minimum CI;
- final M1 P0 regression gate;
- final M2 ExecutionAdapter regression gate;
- final M2 Runtime Lifecycle three-platform gate;
- final artifact IDs/digests and denominator;
- Traceability/PRD/Threat Model/README synchronization;
- strict code/docs review and PR Ready/merge;
- docs-only merged-state closeout.

Current repository conclusion: **NO RELEASE**.
