# M1 P0 Cross-platform Validation Report

> Report date: 2026-07-27 UTC  
> Repository: `yuanchenglu/deepseek_runtime`  
> Matrix validation head: `0e60610e47076bfb5bafbf0520f3e49886267902`  
> Pull request: #10  
> Matrix workflow: `Minimum CI` run 67 (`30294382210`)  
> Standard branch validation before report consolidation: run 69 (`30294676040`)  
> Rewritten clean-history validation: run 72 (`30295621991`), success  
> Technical gate: **PASS**  
> Milestone governance state: **READY FOR APPROVAL / NOT MERGED**  
> Release decision: **NO RELEASE**

## 1. Decision

The M1 P0 technical exit gate passes on Linux, macOS, and Windows.

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

This closes the known reproducible defects in the scoped M1 P0 scenarios. It does not merge the implementation PRs, replace human contract review, or authorize an Alpha release.

## 2. Platform summary

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

The Windows `TC-WS-003` result uses an actual junction/reparse-point test. It is not inferred from a skipped POSIX symlink test.

## 5. Retained artifacts

Run 67 retained one JSON document per platform for 30 days. Each document records the manifest, platform identity, every repetition, unittest output, failures, errors, skips, and final conclusion.

| Artifact | Artifact ID | SHA-256 digest |
| --- | ---: | --- |
| `m1-p0-Linux` | `8664022565` | `750b310da753b9bb6ea9ed5718156ebc4d7dad7fd0a36057d9bdf92fe0556ee2` |
| `m1-p0-macOS` | `8664028904` | `963c1e5f468732fa54bd039528ede6f71129cab497da54c62573e2899cfd6a7e` |
| `m1-p0-Windows` | `8664037860` | `c7b9275f42270c5a8ca9e05c91b2d36725ba41b4d83b3c020b198f39b9ff1bd6` |

The permanent gate is `.github/workflows/m1-p0-gate.yml`. The versioned denominator and runner are defined in `scripts/m1_p0_gate.py`.

## 6. Failure history and correction

The first three-platform execution was run 59 (`30293591740`) at commit `66f829076678327bc96bc2d0db70f69b315ebb1c`.

Linux and macOS passed. Windows failed for two independently verified reasons:

1. **Product compatibility defect** — `ChangeJournalStore.save()` called `os.fchmod` directly, but Windows does not provide that function.
2. **Test portability defect** — the restart test created `old\n` through text mode. Windows newline conversion produced CRLF bytes while the expected pre-change hash used LF bytes.

The production implementation now capability-detects `os.fchmod`; the fixture now writes exact bytes with `write_bytes(b"old\n")`.

The rollback root branch passed Minimum CI run 63 after these corrections. The fixes were then synchronized into the full stack and validated by run 67. The failed run was retained and was not rerun or averaged away.

## 7. M1 stack

| Slice | Pull request | Purpose | Current state |
| --- | ---: | --- | --- |
| M1-A | #6 | Core contracts, schemas, transition manifest, ADRs | Ready for review; not merged |
| M1-B | #7 | Workspace containment and no-follow traversal | Ready for review; not merged |
| M1-C | #8 | Opaque rollback handle and durable ChangeJournal | Ready for review; not merged |
| M1-D | #9 | Side-effect uncertain recovery and reconciliation | Ready for review; not merged |
| M1-E | #10 | Versioned cross-platform P0 gate and consolidated report | Ready for review; not merged |

Required merge order:

```text
PR #6 → PR #7 → PR #8 → PR #9 → PR #10
```

Each successor must be retargeted to `develop` after its base PR merges.

## 8. Exit-gate evaluation

| M1 exit condition | Evidence | Status |
| --- | --- | --- |
| M1-A contracts implemented and tests pass | PR #6; Minimum CI runs 38 and 40 | Technical PASS; human approval pending |
| Seven required P0 Test Case IDs pass | Run 67 and retained JSON artifacts | PASS |
| Applicable-platform P0 tests pass 20 consecutive repetitions | Linux, macOS, Windows each 140/140 | PASS |
| Failures are not hidden by rerun | Run 59 retained; fixes validated in new commits and run 67 | PASS |
| Active reproducible P0 defects in the tested scope | No failure remains in the versioned manifest | PASS for tested scope |
| Active S0 defects | No S0 defect identified by M1 evidence | PASS for current evidence |
| SECURITY, Known Unknowns, Code Review, Traceability synchronized | Slice evidence and this report exist; final status update follows merge | PENDING GOVERNANCE CLOSEOUT |
| Protected-branch review and ordered merge | PR #6–#10 remain unmerged | PENDING HUMAN APPROVAL |

## 9. Boundary and non-claims

This report does not claim:

- kernel or container isolation;
- protection against a malicious concurrent process with equivalent host permissions;
- strict multi-file transactional atomicity across directories;
- encrypted ChangeJournal storage by default;
- external exactly-once semantics for arbitrary side effects;
- completion of M2–M6 requirements;
- Alpha release readiness.

The repository remains **NO RELEASE** until the protected-branch review chain is merged and later milestone gates are completed.

## 10. Conclusion

**M1 P0 technical gate: PASS.**

**M1 governance closure: PENDING HUMAN APPROVAL AND ORDERED MERGE.**

After PR #6–#10 merge, the permanent `M1 P0 Gate` must run on the integrated `develop` state and Traceability statuses must be updated before M1 is marked closed.
