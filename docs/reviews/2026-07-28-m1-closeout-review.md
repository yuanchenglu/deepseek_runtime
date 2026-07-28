# DeepSeek Runtime M1 Code Review Closeout

> Review date: 2026-07-28
> Baseline: integrated `develop` after PR #6–#10
> Original review: `docs/reviews/2026-07-27-code-review.md`
> Closeout status: **PENDING INTEGRATED CI**
> Release decision: **NO RELEASE**

## 1. Purpose

This document does not replace the original full Code Review. It records which original findings were changed by M1 and which findings remain active for M2–M6.

## 2. Original P0 findings

| Finding | Original risk | M1 implementation | Evidence status |
| --- | --- | --- | --- |
| CR-P0-001: caller-controlled rollback token could target external paths | Workspace-external write/delete and stale overwrite | PR #6/#8 introduced versioned RollbackHandle/ChangeJournal contracts, opaque handles, workspace binding, expiry, consumed state, post-change hash checks, and content-free audit tests | Pre-merge three-platform matrix PASS; integrated closeout PR pending |
| CR-P0-002: Workspace search followed external symlink/junction paths | Workspace-external read/search | PR #7 introduced one production WorkspaceResolver, no-follow traversal, candidate containment, identity checks, and Windows junction coverage | Pre-merge three-platform matrix PASS; integrated closeout PR pending |

The original review also described repeated side effects as CR-P1-003. The PRD and execution plan classify the crash-after-effect replay scenario as the M1 P0 requirement `SES-007`. PR #9 now transitions persisted running non-idempotent/manual effects to `side-effect-uncertain` and requires explicit reconciliation.

## 3. P0 technical result

The retained M1 matrix executed:

```text
7 Test Case IDs × 20 repetitions × 3 platforms = 420 Test Case attempts
420 passed / 0 failed / 0 skipped / 0 not applicable
```

The Windows `TC-WS-003` result used an actual junction/reparse-point test. The initial Windows failure remains retained and was corrected in later commits; it was not hidden by rerun.

The P0 findings are marked **Implemented** until the integrated closeout PR executes the permanent gate against the fully merged `develop` state. After that run passes and is recorded, these scoped findings may be marked **Verified**.

## 4. Remaining active P1 findings

| Finding | Current status | Next milestone |
| --- | --- | --- |
| CR-P1-001: Runtime does not force Security and Session integration | Active. Contracts exist, but a naked handler production path remains. | M2 |
| CR-P1-002: Checkpoint and public Evidence are not fully separated in production storage | Active. Separate contracts/schemas exist; legacy SessionStore remains. | M3 |
| CR-P1-003: side effects may repeat after crash | Scoped replay path implemented; complete receipt/idempotency/backoff/fault matrix remains. | M3 |
| CR-P1-004: command sandbox can be bypassed and inherits host capabilities | Active. No complete ExecutionAdapter boundary exists. | M2 |
| CR-P1-005: malformed Provider response may fail before normalization | Active. | M2/M4 |
| CR-P1-006: ChangeManager is not strictly multi-file atomic | Boundary corrected to best-effort; lock/staging/fsync/compensation matrix remains. | M3 |

## 5. Review conclusion

M1 materially changes the repository state:

- the original Workspace and rollback P0 defects have production implementations and repeated cross-platform evidence;
- ambiguous non-idempotent side effects no longer auto-replay in the implemented recovery path;
- core contracts and machine-readable manifests now exist;
- the repository is ready to begin M2 after integrated M1 closeout.

M1 does **not** make the repository release-ready. The highest-priority remaining defect is still the absence of one non-bypassable production path:

```text
Provider
→ Runtime lifecycle
→ ToolRegistry
→ JSON Schema validation
→ Policy
→ Approval
→ ExecutionAdapter
→ checkpoint/evidence
→ RuntimeResult
```

Until M2 closes that path and later milestones complete recovery, Provider, CLI, packaging, and release evidence, the repository remains **NO RELEASE**.