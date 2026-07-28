# M2-D Runtime Lifecycle Closeout

> Milestone: M2-D Runtime Lifecycle, Budget, and Cancellation
> Status: **CLOSED**
> Implementation PR: #20
> Implementation final head: `10f5240d8c82df8c41aa609c96a40c3ab7f65242`
> Squash merge to `develop`: `2fe059d900c4e04fab05ca92f421a41d7ff0aa01`
> Release decision: **NO RELEASE**

## 1. Closed scope

M2-D closed the implementation and verification gap for the existing single `DeepSeekRuntime` production loop:

- validated Runtime state transitions and lifecycle events;
- private `RecoverableCheckpoint` handoff at critical lifecycle boundaries;
- ASK pending checkpoint before ApprovalProvider I/O;
- approve-once/approve-session checkpoint before Adapter execution;
- deny/timeout/unavailable/invalid outcome checkpoint before structured return;
- Provider-before-call cancellation;
- tool cancellation and uncertain non-idempotent side-effect semantics;
- step/token/known-USD-cost/context/time budgets;
- unknown usage/cost preserved as unknown;
- deterministic tool-error continue/terminate policy;
- structured RuntimeResult boundaries for the supported malformed-Provider subset;
- private structural receipts for successful side effects;
- content-minimized public evidence;
- Linux/macOS/Windows focused lifecycle verification.

No second production Agent loop or per-tool state machine was introduced.

## 2. Blocker closure

The blocking regression was retained and passed:

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

Root cause: later ASK calls in one tool batch reused global `TOOL_RUNNING` without an execution-before-Adapter checkpoint handoff. The fix added the missing handoff while preserving the global Provider-round/tool-batch lifecycle.

Additional regression coverage verifies cached approve-session, deny, timeout, missing/failed ApprovalProvider, and invalid outcome.

## 3. Final exact-head evidence

All substantive gates passed on implementation head `10f5240d8c82df8c41aa609c96a40c3ab7f65242`:

| Gate | Run | Result |
| --- | ---: | --- |
| Minimum CI | 229 / `30383164778` | PASS |
| M1 P0 Gate | 173 / `30383164880` | 140/140 per OS; 420/420 total |
| M2 ExecutionAdapter Gate | 79 / `30383164777` | 36/36 per OS; 108/108 total |
| M2 Runtime Lifecycle Gate | 44 / `30383164780` | 64/64 per OS; 192/192 total |

Focused artifacts report 0 failures, 0 errors, and 0 skips.

## 4. Artifacts and digests

### Minimum CI

- Pyright diagnostics: `8697843499`; `sha256:f966ff3a70d95f52de5ad372cb9f432bd49bfb35e203496d15e45a8b16174ce6`.

### M1 P0

- Linux: `8697841298`; `sha256:a231b354c1ab989c86be785dd001233493fda6bdcaf8a72db1f980cda5a0ab80`.
- macOS: `8697847806`; `sha256:25c36e5cdfa0fc5c542242d14fa27526fec2bdca5d5805e45d6945a6f12dfdfb`.
- Windows: `8697858032`; `sha256:fe08e5c9dfa1530b46cf1e6444aab8be3ff008a2b4dddc574b3df86520f96ed6`.

### M2 ExecutionAdapter

- Linux: `8697875773`; `sha256:f404acd4765f49dcf1fb74174cb76217a7733cfe20f60974a98b2f40ce55b35e`.
- macOS: `8697875328`; `sha256:d535416e2c1c004778e9d5b433c773b97dfd1dd5affd20e2a88dcd448b756eef`.
- Windows: `8697888550`; `sha256:6f21210889f19b00ab23b9433e4fb2202c6ee87a92ec36072f4b0dcf92f1215e`.

### M2 Runtime Lifecycle

- Linux: `8697840147`; `sha256:709d250611a70ad395291b74edb20ee6aed2b20ac0f99e6edc288785f4b1faf6`.
- macOS: `8697841308`; `sha256:4bc847bf2bf003444cb0351d14d44e7c0877a00a6515224c529c26832d1c9569`.
- Windows: `8697849136`; `sha256:37eb28ff37523f17bc347bfcbddfda9fbafdd5cef806ec2c2e094e1271057ca1`.

## 5. Retained failures

The following failures remain visible and were not rerun-masked or deleted:

- Minimum CI runs 184, 199, 205, 207, 211;
- M2 Runtime Lifecycle Gate runs 1, 13, 16, 20, 22, 26.

Run 26 preserves the three-platform failure evidence for the later-batch approval checkpoint blocker.

## 6. Requirement status

Promoted to `Verified` after merge and exact-head evidence:

- RUN-001, RUN-002, RUN-004, RUN-005, RUN-007, RUN-008;
- OBS-003 and OBS-007 for M2 budget/unknown semantics;
- the in-memory checkpoint-timing portion of SEC-003 remains evidenced but SEC-003 as a whole stays `Partial` because durable store/resume/migration belong to M3.

Still Partial/Planned:

- RUN-006: Provider in-flight transport cancellation remains M4;
- RUN-010: arbitrary Provider JSON/malformed matrix remains M4;
- TOOL-006 and SES-010: full durable receipt/checkpoint roundtrip remains M3;
- durable storage, locking, corruption handling, migration, optional encryption remain M3.

## 7. Exit judgment

M2-D Exit Gate is satisfied for its defined implementation slice. M2-E Workspace P1 is now the next legal work item.

Repository release status remains **NO RELEASE** until M2-E/M2-F/M2-G/M3/M4/M5/M6 and the final Release Gate are complete.
