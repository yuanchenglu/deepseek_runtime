# M1 P0 Cross-platform Validation Report

> Report date: 2026-07-28 UTC  
> Repository: `yuanchenglu/deepseek_runtime`  
> Implementation pull requests: #6–#10  
> Integrated closeout pull request: #13  
> Integrated validation head: `81643dca45156e3f52d8b96d25a8a2d4310bc855`  
> Minimum CI: run 82 (`30327637525`), success  
> M1 P0 Gate: run 33 (`30327637544`), success  
> Technical gate: **PASS**  
> Milestone governance state: **M1 CLOSED**  
> Release decision: **NO RELEASE**

## 1. Decision

The M1 P0 technical exit gate passes on the integrated PR #13 state based on the fully merged `develop` implementation from PR #6–#10.

All seven M1 P0 Test Case IDs completed twenty consecutive repetitions on each platform without a failure, skip, or not-applicable result:

- `TC-WS-001`
- `TC-WS-002`
- `TC-WS-003`
- `TC-CHG-001`
- `TC-CHG-002`
- `TC-CHG-011`
- `TC-SES-007`

```text
7 Test Case IDs × 20 repetitions × 3 platforms = 420 Test Case attempts
420 passed / 0 failed / 0 skipped / 0 not applicable
```

`TC-CHG-011` executes three underlying unittest methods per attempt. The complete matrix therefore executed 540 underlying unittest method invocations.

## 2. Integrated platform summary

| Platform | Runner evidence | Python | Repetitions | Attempts | Passed | Failed | N/A | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Linux | Linux `6.17.0-1020-azure`, x86_64 | 3.11.15 | 20 | 140 | 140 | 0 | 0 | PASS |
| macOS | Darwin `25.4.0`, arm64 | 3.11.9 | 20 | 140 | 140 | 0 | 0 | PASS |
| Windows | Windows `10`, AMD64 | 3.11.9 | 20 | 140 | 140 | 0 | 0 | PASS |
| **Total** | Three operating-system families | Python 3.11 | — | **420** | **420** | **0** | **0** | **PASS** |

## 3. Test Case matrix

Each value is `passed repetitions / required repetitions`.

| Test Case | Linux | macOS | Windows | Result |
| --- | ---: | ---: | ---: | --- |
| `TC-WS-001` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-WS-002` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-WS-003` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-CHG-001` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-CHG-002` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-CHG-011` | 20/20 | 20/20 | 20/20 | PASS |
| `TC-SES-007` | 20/20 | 20/20 | 20/20 | PASS |

## 4. Manifest mapping

| Test Case | Linux/macOS implementation | Windows implementation |
| --- | --- | --- |
| `TC-WS-001` | traversal and external absolute paths are rejected repeatedly | same |
| `TC-WS-002` | external file symlink is never read or searched | same |
| `TC-WS-003` | external directory symlink is never traversed | Windows junction is not traversed |
| `TC-CHG-001` | forged handle and caller-controlled rollback payload are rejected repeatedly | same |
| `TC-CHG-002` | malicious Journal path cannot target outside the workspace | same |
| `TC-CHG-011` | restart-safe rollback, cross-workspace rejection, and expiry enforcement | same |
| `TC-SES-007` | crash after effect but before result checkpoint does not auto-retry | same |

The Windows `TC-WS-003` result uses the actual `test_windows_junction_is_not_traversed` test. It is not inferred from a skipped POSIX symlink test.

## 5. Integrated artifacts

Run 33 retained one JSON document per platform. Each document records the manifest, platform identity, every repetition, unittest output, failures, errors, skips, and final conclusion.

| Platform | Artifact | Artifact ID | SHA-256 digest |
| --- | --- | ---: | --- |
| Linux | `m1-p0-Linux` | `8676238220` | `a3ca74a50e7ab6831fc352a24aaa1f94cdf99013784d515108ae134432c7fb03` |
| macOS | `m1-p0-macOS` | `8676237125` | `4c9a7461d6a685df3c025297f79d9e799a146efe0c7303d6082a1fbbe1b0658e` |
| Windows | `m1-p0-Windows` | `8676241048` | `6342d9a008b833848603d6d9c5067d5b512037cebecccee930f9c140184d7341` |

Artifacts are retained for 30 days from 2026-07-28. The permanent gate is `.github/workflows/m1-p0-gate.yml`; the versioned denominator and runner are defined in `scripts/m1_p0_gate.py`.

## 6. Workflow trigger defect found during closeout

The first PR #13 head ran Minimum CI but did not create an independent M1 P0 Gate run. The root cause was a workflow-level concurrency expression that referenced `${{ matrix.os }}`. The `matrix` context is not available at workflow scope, so GitHub treated the workflow configuration as invalid.

The closeout PR changed the workflow-level group to use only `github.workflow` and `github.ref`. The fix did not alter the test manifest, repetition count, platform matrix, or failure behavior. The corrected head produced successful Minimum CI run 82 and M1 P0 Gate run 33.

## 7. Historical failure and correction

The first three-platform execution was run 59 (`30293591740`) at commit `66f829076678327bc96bc2d0db70f69b315ebb1c`.

Linux and macOS passed. Windows failed for two independently verified reasons:

1. **Product compatibility defect** — `ChangeJournalStore.save()` called `os.fchmod` directly, but Windows does not provide that function.
2. **Test portability defect** — the restart test created `old\n` through text mode. Windows newline conversion produced CRLF bytes while the expected pre-change hash used LF bytes.

The production implementation now capability-detects `os.fchmod`; the fixture writes exact bytes with `write_bytes(b"old\n")`.

The failed run remains retained. The correction was validated independently in later runs and again by integrated run 33; it was not erased or averaged away.

## 8. M1 implementation stack

| Slice | Pull request | Purpose | Current state |
| --- | ---: | --- | --- |
| M1-A | #6 | Core contracts, schemas, transition manifest, ADRs | Merged into `develop` |
| M1-B | #7 | Workspace containment and no-follow traversal | Merged into `develop` |
| M1-C | #8 | Opaque rollback handle and durable ChangeJournal | Merged into `develop` |
| M1-D | #9 | Side-effect uncertain recovery and reconciliation | Merged into `develop` |
| M1-E | #10 | Versioned cross-platform P0 gate and consolidated report | Merged into `develop` |

Merge order was preserved:

```text
PR #6 → PR #7 → PR #8 → PR #9 → PR #10
```

## 9. Exit-gate evaluation

| M1 exit condition | Evidence | Status |
| --- | --- | --- |
| M1-A contracts implemented and tests pass | PR #6; contract tests and schemas | PASS |
| Seven required P0 Test Case IDs pass | Integrated run 33 JSON artifacts | PASS |
| Applicable-platform P0 tests pass 20 consecutive repetitions | Linux, macOS, Windows each 140/140 | PASS |
| Failures are not hidden by rerun | Run 59 retained; fixes validated by independent later runs | PASS |
| Active reproducible P0 defects in the tested scope | No failure remains in the integrated versioned manifest | PASS |
| Active S0 defects | No S0 defect identified by M1 evidence | PASS for current evidence |
| SECURITY, Known Unknowns, Code Review, README, and Traceability synchronized | PR #13 | PASS |
| Ordered implementation merge | PR #6–#10 merged into `develop` | PASS |
| Permanent gate on integrated state | Minimum CI run 82 + M1 P0 Gate run 33 | PASS |

## 10. Boundary and non-claims

This report does not claim:

- kernel or container isolation;
- protection against a malicious concurrent process with equivalent host permissions;
- strict multi-file transactional atomicity across directories;
- encrypted ChangeJournal storage by default;
- external exactly-once semantics for arbitrary side effects;
- a non-bypassable ToolRegistry/Policy/Approval/ExecutionAdapter path;
- completion of M2–M6 requirements;
- Alpha release readiness.

## 11. Conclusion

**M1 P0 technical gate: PASS.**

**M1 implementation merge: COMPLETE.**

**M1 integrated governance closeout: CLOSED.**

M2 is authorized. The repository remains **NO RELEASE** until the later milestone gates are completed.