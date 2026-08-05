# M2-E Workspace P1 Worklog

> Status: **CLOSED** — direct push to `develop` as `8c097a6`; all gates green.
> Base: `develop@c2d873ef3a1ea8288a145204ea907df5c15d0378`
> Branch: `agent/m2-e-workspace-p1`
> PR: #22 `feat(workspace): close M2-E bounded read and search`
> Release decision: **NO RELEASE**

## 1. Scope

M2-E closes the implementation gap for `WS-003`–`WS-005` without weakening the verified M1 Workspace containment boundary:

- UTF-8 byte-safe truncation;
- explicit read byte limit and truncation metadata;
- search file-count, total-byte, elapsed-time, match-count, and per-file budgets;
- structured binary, permission-denied, disappeared-file, and ordinary I/O outcomes;
- production `WorkspaceTools` remains behind the single `WorkspaceResolver`;
- Linux, macOS, and Windows focused verification.

## 2. Security boundary

Security violations remain exceptions and are not converted into ordinary file results:

- traversal or absolute external path;
- NUL path input;
- symlink or Windows reparse-point traversal;
- non-directory ancestor;
- non-regular file;
- identity change during no-follow open.

Ordinary content/filesystem conditions use content-minimized structured status:

```text
ok
truncated
binary
permission-denied
disappeared
io-error
budget-exhausted
```

No exception message, absolute host path, unreadable content, binary content, or private OS error body is returned.

## 3. Contracts added

- `WorkspaceReadResult`;
- `WorkspaceSearchBudgets`;
- `WorkspaceSearchResult`;
- `WorkspacePathMissing` as a `WorkspaceViolation` subtype;
- `WorkspaceResolver.read_bounded()`;
- `WorkspaceResolver.search_text()`.

The original `read_text(max_chars=...)` remains as a compatibility API, but the production `WorkspaceTools.read_file` path uses the new byte-bounded API.

## 4. Read behavior

- reads at most `max_bytes + 1` bytes to identify truncation;
- decodes UTF-8 strictly;
- if the byte boundary splits only the final UTF-8 sequence, trims to the last valid boundary;
- invalid UTF-8 or NUL content returns `binary`;
- reports relative path, bytes read, observed file size, truncation flag, and stable error code;
- no-follow open and before/opened identity comparison remain enforced.

## 5. Search behavior

One `WorkspaceSearchBudgets` object enforces:

- `max_files`;
- `max_bytes`;
- `max_seconds`;
- `max_matches`;
- `max_file_bytes`.

Search returns:

- structured relative-path/line/text match items;
- files and bytes scanned;
- elapsed milliseconds;
- stable stop reason (`file-limit`, `byte-limit`, `time-limit`, `match-limit`);
- structured skip counters for binary, permission, disappearance, I/O, links, non-regular files, and truncated files.

The elapsed-time budget is checked before directory work, before each entry, and immediately after each bounded file read. The final check closes the single/last-file overrun case; it is cooperative and does not claim OS-level interruption of a blocking filesystem call.

## 6. Regression matrix

`tests/test_workspace_p1.py` covers:

- UTF-8 multibyte cut boundary;
- exact byte boundary;
- invalid UTF-8 and NUL binary classification;
- permission, disappearance, and generic I/O structure/redaction;
- contained missing file versus escape rejection;
- file-count budget;
- total-byte budget;
- pre-scan time budget;
- last-file post-read time budget;
- binary search skip without content exposure;
- production `WorkspaceTools` structured output;
- budget validation fail-closed behavior.

Existing containment tests were updated only for the new structured output and retain traversal/link/reparse assertions.

## 7. Focused Gate

Permanent files:

- `scripts/m2_workspace_gate.py`;
- `.github/workflows/m2-workspace-p1.yml`.

The Gate runs on Linux, macOS, and Windows with Python 3.11 and uploads one JSON artifact per platform with explicit test denominator, failures, errors, and skips.

Intermediate head `376740ac0d6fbe342dd922d35b025cc8825f6f19` passed run 4 with 11/11 tests per platform and 0 failures/errors/skips. This is not final evidence because the post-read time-budget regression and final documentation were added later.

## 8. Retained implementation failures

The repository retains real failures from implementation, including:

- syntax/indentation failures caused by the first remote production-tool patch;
- focused Gate failure before `test_workspace_p1.py` existed;
- the failed first post-read time-budget patch anchor;
- the malformed inserted test indentation before the whole test file was restored exactly.

These runs are not deleted, rerun-masked, or replaced by an earlier green head. Exact run numbers are recorded in the final PR evidence after the final documentation head is locked.

## 9. Non-goals and remaining work

M2-E does not add:

- CLI output/report/json/exit-code protocol;
- durable checkpoint, locking, migration, or recovery;
- Provider parsing, retry, streaming, body-size, or in-flight cancellation;
- OS/kernel filesystem isolation;
- release, `master`, or tag changes.

## 10. Finalization sequence

Before PR #22 may move to Ready:

1. synchronize PRD, Traceability, Threat Model, Test Plan/Report, README, INDEX, and Plan as `Implemented`;
2. obtain one final exact head for Minimum CI, M1 P0, M2 Adapter, M2 Lifecycle, and M2 Workspace P1;
3. record Workspace artifact IDs, digests, actual denominator, and retained failures;
4. verify changed files, reviews, threads, resolver-bypass negatives, privacy, and active P0/S0/S1;
5. restore all temporary workflows to permanent read-only form;
6. squash merge to `develop`;
7. use a separate docs-only closeout PR to promote `WS-003`–`WS-005` to `Verified`;
8. start M2-F CLI immediately.

Current conclusion: **IMPLEMENTED / PRE-MERGE / NO RELEASE**.
