# M1 Integrated Closeout

> Status date: 2026-07-28
> Target branch: `develop`
> Implementation PRs: #6, #7, #8, #9, #10
> Closeout status: **PENDING INTEGRATED CI**
> Release decision: **NO RELEASE**

## 1. Purpose

M1 froze the minimum Error, Runtime State, Tool, Recovery, Checkpoint/Evidence, RollbackHandle, and ChangeJournal contracts and closed the scoped Workspace, rollback-authorization, and side-effect-replay P0 defects.

This closeout does not rely only on the pre-merge stacked-branch matrix. It requires the permanent gate to execute again against a Pull Request whose base is the fully integrated `develop` state after PR #6–#10 merged.

## 2. Merged implementation stack

| Slice | Pull request | Scope | Merge state |
| --- | ---: | --- | --- |
| M1-A | #6 | Core contracts, schemas, transition manifest, ADRs | Merged into `develop` |
| M1-B | #7 | Workspace containment and no-follow traversal | Merged into `develop` |
| M1-C | #8 | Opaque rollback handles and durable ChangeJournal | Merged into `develop` |
| M1-D | #9 | Side-effect-uncertain recovery and reconciliation | Merged into `develop` |
| M1-E | #10 | Versioned three-platform P0 gate and canonical report | Merged into `develop` |

Integrated merge head before this closeout branch: `develop@59a634a5fdfef06240e48d3ae594b0d4dc3ffdc8`.

## 3. Existing technical evidence

The retained pre-merge matrix is documented in `docs/testing/m1-p0-report.md`:

```text
Linux:   140/140 passed
macOS:   140/140 passed
Windows: 140/140 passed
Total:   420/420 passed
Failed:  0
Skipped: 0
N/A:     0
```

The failed Windows run remains retained in the evidence history. It was corrected by capability-detecting `os.fchmod` and using byte-exact newline fixtures; no rerun was used to erase the failure.

## 4. Integrated closeout gate

This Pull Request must run both:

- `Minimum CI / Python 3.11 baseline`;
- permanent `M1 P0 Gate` on Linux, macOS, and Windows.

The M1 P0 jobs must execute these seven Test Case IDs twenty times per platform:

- `TC-WS-001`;
- `TC-WS-002`;
- `TC-WS-003`;
- `TC-CHG-001`;
- `TC-CHG-002`;
- `TC-CHG-011`;
- `TC-SES-007`.

M1 cannot be marked closed until all jobs complete successfully and the final run identifiers are recorded in this file and Traceability.

## 5. Exit Gate evaluation

| M1 exit condition | Current evidence | Status |
| --- | --- | --- |
| M1-A contracts implemented and reviewed | PR #6; contract schemas and tests | PASS |
| Required seven P0 Test Case IDs pass | Pre-merge matrix run 67 | PASS; integrated rerun pending |
| Applicable-platform P0 tests pass 20 consecutive repetitions | 140/140 per platform in retained artifacts | PASS; integrated rerun pending |
| Failures are not hidden by rerun | Windows failure run 59 retained and corrected in later commits | PASS |
| Active reproducible P0 defects in the scoped manifest | No remaining failure in retained matrix | PASS for current evidence |
| Active S0 defects | No S0 identified by M1 evidence | PASS for current evidence |
| SECURITY, Known Unknowns, Code Review, README, Traceability synchronized | Included in this closeout branch | PENDING CI |
| Integrated `develop` state validated | This PR | PENDING CI |

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

After the integrated gate passes and this PR merges, execute M2 in this order:

1. ToolRegistry as the only production tool entry;
2. JSON Schema argument validation and ToolExecutionResult normalization;
3. Policy and ApprovalProvider on every tool call;
4. ExecutionAdapter boundary, including RestrictedSubprocess controls;
5. RuntimeResult, lifecycle, checkpoint timing, cancellation, and budgets;
6. Workspace P1 limits and structured I/O failures;
7. CLI stdout/report/json/exit-code contract;
8. complete the M2 P1 test manifest and Exit Gate.

Repository status remains **NO RELEASE**.