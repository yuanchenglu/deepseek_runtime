# M2-D Runtime Lifecycle Worklog

> Status: IMPLEMENTATION COMPLETE / PRE-MERGE
> Base: `develop@45b7c448d437df9ced5b5776f017a008376dabbb`
> Branch: `agent/m2-runtime-lifecycle`
> PR: #20 `feat(runtime): establish M2-D lifecycle and budget path`
> Release decision: **NO RELEASE**

## 1. Scope

M2-D extends the existing `DeepSeekRuntime` production loop with:

- explicit lifecycle state and content-minimized events;
- transition validation against the frozen manifest;
- private checkpoint handoff at critical states;
- Provider-before-call cancellation and final tool-cancellation semantics;
- step/token/USD-cost/context/time budgets;
- deterministic tool-error continue/terminate policy;
- structured malformed-Provider boundaries supported by this slice;
- private structural receipts for successful side-effect execution;
- a focused Linux/macOS/Windows M2-D Gate.

## 2. Exclusions and handoff

M2-D does not add:

- a second production Agent loop or per-tool state machine;
- Workspace P1 read/search budgets;
- CLI stdout/report/json/exit-code protocol;
- Provider retry, streaming, response-body limit, or in-flight transport cancellation;
- durable/encrypted/locked checkpoint storage, migration, or resume;
- M3 Evidence totality/canonical identity/redaction redesign;
- packaging, `master`, tag, or release changes.

Durable store, locking, corruption handling, migration, resume, and optional encryption remain M3. Provider in-flight cancellation remains M4.

## 3. Entry evidence

- M2-C implementation merge: `7793a10152a49fb815aac667906080a4e1a39920`;
- M2-C docs closeout merge: `45b7c448d437df9ced5b5776f017a008376dabbb`;
- entry repository status: M0/M1/M2-A/M2-B/M2-C CLOSED, M2-D NEXT.

## 4. Blocker and root cause

Original blocking regression:

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

For the second and later ASK call in one Provider tool batch, the global lifecycle was already `TOOL_RUNNING`. `on_authorized()` updated the private call state but did not hand off a new checkpoint, so the Adapter could start without a snapshot containing the resolved approval and current call execution state.

## 5. Implemented fix

The fix preserves the single global Runtime lifecycle:

- ASK pending is handed off before `ApprovalProvider` I/O;
- approve-once and approve-session are handed off before Adapter execution;
- deny, timeout, unavailable, and invalid outcomes are handed off before the structured tool result;
- the later-call `TOOL_RUNNING` reuse branch now explicitly hands off current state;
- no second production state machine was introduced;
- public evidence remains content-minimized.

Strict regression coverage now includes:

- approve-once later-batch checkpoint ordering;
- cached approve-session later-batch checkpoint ordering;
- deny;
- timeout;
- missing ApprovalProvider;
- ApprovalProvider exception;
- invalid ApprovalProvider outcome.

The original regression remains present and unchanged in intent.

## 6. Implemented Runtime behavior

- text-only and multi-round tool execution;
- transition/event validation;
- private `RecoverableCheckpoint` handoff;
- Provider-before-call cancellation;
- pure cancellation versus uncertain side-effect terminal semantics;
- step/token/known-USD-cost/context/time thresholds;
- unknown usage/cost remains unknown rather than becoming zero;
- configurable tool-error continue/terminate behavior;
- supported malformed Provider response subset returns structured `RuntimeResult`;
- successful side effects carry private structural receipts;
- public lifecycle/evidence surfaces exclude prompt, response, tool arguments/results, receipt body, and exception body.

## 7. Retained failures

Failures are retained and are not rerun-masked or deleted:

- Minimum CI runs 184, 199, 205, 207, 211;
- M2 Runtime Lifecycle Gate runs 1, 13, 16, 20, 22, 26.

Run 26 failed on Linux, macOS, and Windows due to the later-batch approval checkpoint blocker. The regression was fixed without reducing its assertions.

## 8. Intermediate evidence only

Head `1d2b1377849800816641a800370eb1c916123125` passed:

- Minimum CI run 214 (`30381265145`);
- M1 P0 Gate run 158 (`30381265158`);
- M2 ExecutionAdapter Gate run 64 (`30381265222`);
- M2 Runtime Lifecycle Gate run 29 (`30381265198`), 62/62 per platform, 186/186 total.

Those runs predate the complete approval outcome matrix and final documentation synchronization. They are retained as intermediate evidence and are not the final exact-head evidence.

## 9. Finalization sequence

The implementation PR may move to Ready only after:

1. this worklog and all authoritative documents are synchronized;
2. temporary write-capable patch jobs are removed and the permanent read-only lifecycle Gate is restored;
3. Minimum CI, M1 P0, M2 ExecutionAdapter, and M2 Runtime Lifecycle all pass on one final exact head;
4. final lifecycle artifact IDs, digests, and actual denominators are recorded in PR #20;
5. changed files, reviews, review threads, security boundaries, and public claims are strictly reviewed;
6. unresolved P0/S0/S1 = 0.

After squash merge to `develop`, a docs-only closeout PR will promote only merged and evidenced Requirements to `Verified`, then M2-E begins immediately.

Current conclusion: **IMPLEMENTED / PRE-MERGE / NO RELEASE**.
