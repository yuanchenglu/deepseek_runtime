# DeepSeek Runtime M1 Code Review Closeout

> Review date: 2026-07-28
> Baseline: PR #13 integrated validation head `81643dca`
> Original review: `docs/reviews/2026-07-27-code-review.md`
> Closeout status: **CLOSED — SCOPED P0 FINDINGS VERIFIED**
> Release decision: **NO RELEASE**

## 1. Purpose

This document does not replace the original full Code Review. It records which original findings were changed by M1 and which findings remain active for M2–M6.

## 2. Original P0 findings

| Finding | Original risk | M1 implementation | Integrated evidence |
| --- | --- | --- | --- |
| CR-P0-001: caller-controlled rollback token could target external paths | Workspace-external write/delete and stale overwrite | PR #6/#8 introduced versioned RollbackHandle/ChangeJournal contracts, opaque handles, workspace binding, expiry, consumed state, post-change hash checks, and content-free audit tests | PR #13 M1 P0 Gate run 33: `TC-CHG-001/002/011` 20/20 on Linux, macOS, Windows |
| CR-P0-002: Workspace search followed external symlink/junction paths | Workspace-external read/search | PR #7 introduced one production WorkspaceResolver, no-follow traversal, candidate containment, identity checks, and Windows junction coverage | PR #13 run 33: `TC-WS-001/002/003` 20/20 on all platforms; Windows used actual junction test |

The original review also described repeated side effects as CR-P1-003. The PRD and execution plan classify the crash-after-effect replay scenario as the M1 P0 requirement `SES-007`. PR #9 transitions persisted running non-idempotent/manual effects to `side-effect-uncertain` and requires explicit reconciliation. PR #13 run 33 verified `TC-SES-007` 20/20 on all three platforms.

## 3. Integrated P0 technical result

```text
7 Test Case IDs × 20 repetitions × 3 platforms = 420 Test Case attempts
420 passed / 0 failed / 0 skipped / 0 not applicable
```

Validation evidence:

- Minimum CI run 82 (`30327637525`): PASS;
- M1 P0 Gate run 33 (`30327637544`): PASS;
- Linux artifact `8676238220`;
- macOS artifact `8676237125`;
- Windows artifact `8676241048`.

The initial Windows failure remains part of the evidence history. It was corrected in independent later commits and was not hidden by rerun.

**CR-P0-001 and CR-P0-002 are Verified for the scoped M1 threat model and manifest.**

## 4. Workflow defect found during closeout

The initial PR #13 head did not create an M1 P0 Gate run. Review found that workflow-level concurrency referenced `${{ matrix.os }}`, although `matrix` is unavailable at workflow scope. The closeout PR changed the workflow concurrency group to use `github.workflow` and `github.ref` only.

This was a CI-definition defect, not a test failure. The repair did not reduce platforms, repetitions, cases, or failure strictness. The corrected workflow produced run 33 and retained all three artifacts.

## 5. Remaining active P1 findings

| Finding | Current status | Next milestone |
| --- | --- | --- |
| CR-P1-001: Runtime does not force Security and Session integration | Active. Contracts exist, but a naked handler production path remains. | M2 |
| CR-P1-002: Checkpoint and public Evidence are not fully separated in production storage | Active. Separate contracts/schemas exist; legacy SessionStore remains. | M3 |
| CR-P1-003: side effects may repeat after crash | Scoped non-idempotent replay path is Verified; complete receipt/idempotency/backoff/fault matrix remains. | M3 |
| CR-P1-004: command sandbox can be bypassed and inherits host capabilities | Active. No complete ExecutionAdapter boundary exists. | M2 |
| CR-P1-005: malformed Provider response may fail before normalization | Active. | M2/M4 |
| CR-P1-006: ChangeManager is not strictly multi-file atomic | Boundary corrected to best-effort; lock/staging/fsync/compensation matrix remains. | M3 |

## 6. Review conclusion

M1 materially changes the repository state:

- the original Workspace and rollback P0 defects have production implementations and integrated repeated cross-platform evidence;
- ambiguous non-idempotent side effects do not auto-replay in the verified recovery scenario;
- core contracts and machine-readable manifests exist;
- the permanent M1 P0 workflow is valid and independently executable;
- M1 is closed and M2 is authorized.

M1 does **not** make the repository release-ready. The highest-priority remaining defect is the absence of one non-bypassable production path:

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