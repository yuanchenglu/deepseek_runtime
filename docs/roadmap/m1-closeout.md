# M1 Integrated Closeout

> Status date: 2026-07-28
> Target branch: `develop`
> Implementation PRs: #6, #7, #8, #9, #10
> Closeout PR: #13
> Closeout status: **CLOSED — INTEGRATED GATE PASS**
> Release decision: **NO RELEASE**

## 1. Purpose

M1 froze the minimum Error, Runtime State, Tool, Recovery, Checkpoint/Evidence, RollbackHandle, and ChangeJournal contracts and closed the scoped Workspace, rollback-authorization, and side-effect-replay P0 defects.

This closeout does not rely only on the pre-merge stacked-branch matrix. The permanent gate executed again from PR #13, whose base is the fully integrated `develop` state after PR #6–#10 merged.

## 2. Merged implementation stack

| Slice | Pull request | Scope | Merge state |
| --- | ---: | --- | --- |
| M1-A | #6 | Core contracts, schemas, transition manifest, ADRs | Merged into `develop` |
| M1-B | #7 | Workspace containment and no-follow traversal | Merged into `develop` |
| M1-C | #8 | Opaque rollback handles and durable ChangeJournal | Merged into `develop` |
| M1-D | #9 | Side-effect-uncertain recovery and reconciliation | Merged into `develop` |
| M1-E | #10 | Versioned three-platform P0 gate and canonical report | Merged into `develop` |

Integrated merge head before the closeout branch: `develop@59a634a5fdfef06240e48d3ae594b0d4dc3ffdc8`.

## 3. Integrated validation evidence

The first PR #13 head exposed a workflow-definition defect: workflow-level concurrency referenced `${{ matrix.os }}`, where the `matrix` context is unavailable. The invalid configuration prevented GitHub from creating an `M1 P0 Gate` run.

PR #13 fixed the trigger by using a workflow-level group based only on `github.workflow` and `github.ref`. No test rule or denominator was weakened.

Validated head: `81643dca45156e3f52d8b96d25a8a2d4310bc855`.

| Gate | Run | Result |
| --- | ---: | --- |
| Minimum CI | 82 (`30327637525`) | PASS |
| M1 P0 Gate | 33 (`30327637544`) | PASS |

The integrated M1 P0 JSON artifacts report:

```text
Linux:   140/140 passed
macOS:   140/140 passed
Windows: 140/140 passed
Total:   420/420 passed
Failed:  0
Skipped: 0
N/A:     0
```

Each of the seven Test Case IDs passed 20/20 repetitions on every platform. Windows `TC-WS-003` executed `test_windows_junction_is_not_traversed`; it was not inferred from a skipped POSIX test.

## 4. Integrated artifacts

| Platform | Artifact | Artifact ID | SHA-256 digest | Python |
| --- | --- | ---: | --- | --- |
| Linux | `m1-p0-Linux` | `8676238220` | `a3ca74a50e7ab6831fc352a24aaa1f94cdf99013784d515108ae134432c7fb03` | 3.11.15 |
| macOS | `m1-p0-macOS` | `8676237125` | `4c9a7461d6a685df3c025297f79d9e799a146efe0c7303d6082a1fbbe1b0658e` | 3.11.9 |
| Windows | `m1-p0-Windows` | `8676241048` | `6342d9a008b833848603d6d9c5067d5b512037cebecccee930f9c140184d7341` | 3.11.9 |

Artifacts are retained for 30 days from 2026-07-28.

## 5. Exit Gate evaluation

| M1 exit condition | Integrated evidence | Status |
| --- | --- | --- |
| M1-A contracts implemented and reviewed | PR #6; contract schemas and tests | PASS |
| Required seven P0 Test Case IDs pass | Run 33 JSON artifacts | PASS |
| Applicable-platform P0 tests pass 20 consecutive repetitions | 140/140 per platform; 420/420 total | PASS |
| Failures are not hidden by rerun | Windows failure run 59 remains retained; correction validated by later independent runs | PASS |
| Active reproducible P0 defects in the scoped manifest | 0 failures in integrated manifest | PASS |
| Active S0 defects | No S0 identified by M1 evidence | PASS for current evidence |
| SECURITY, Known Unknowns, Code Review, README, Traceability synchronized | PR #13 | PASS |
| Integrated `develop` state validated | Minimum CI run 82 + M1 P0 Gate run 33 | PASS |

**M1 Exit Gate: PASS. M1 is CLOSED.**

## 6. Remaining boundaries

M1 does not claim:

- a non-bypassable ToolRegistry/Policy/Approval/Execution path;
- kernel or container isolation;
- protection from a malicious same-account concurrent process;
- strict cross-directory multi-file atomicity;
- encrypted ChangeJournal storage by default;
- universal exactly-once external side effects;
- completion of checkpoint/evidence separation;
- M2–M6 readiness.

Those remain explicit later-milestone work.

## 7. Next executable milestone

M2 is authorized in this order:

1. ToolRegistry as the only production tool entry;
2. JSON Schema argument validation and ToolExecutionResult normalization;
3. Policy and ApprovalProvider on every tool call;
4. ExecutionAdapter boundary, including RestrictedSubprocess controls;
5. RuntimeResult, lifecycle, checkpoint timing, cancellation, and budgets;
6. Workspace P1 limits and structured I/O failures;
7. CLI stdout/report/json/exit-code contract;
8. complete the M2 P1 test manifest and Exit Gate.

Repository status remains **NO RELEASE**.