# M2-E Workspace P1 Test Report

> Status: **CLOSED** — direct push to `develop` as `8c097a6`; all gates green.
> PR: #22 `feat(workspace): close M2-E bounded read and search`
> Branch: `agent/m2-e-workspace-p1`
> Release decision: **NO RELEASE**

## 1. Scope

This report verifies `WS-003`–`WS-005`:

- UTF-8 byte-safe bounded reads;
- explicit truncation metadata;
- structured binary, permission, disappeared-file, and I/O outcomes;
- file-count, total-byte, elapsed-time, match-count, and per-file search budgets;
- production `WorkspaceTools` integration behind `WorkspaceResolver`;
- preservation of M1 containment, no-follow, symlink, and reparse-point controls.

## 2. Focused denominator

Permanent runner: `scripts/m2_workspace_gate.py`  
Permanent workflow: `.github/workflows/m2-workspace-p1.yml`

Platforms:

```text
Linux + Python 3.11
macOS + Python 3.11
Windows + Python 3.11
```

Test module:

```text
test_workspace_p1
```

The final implementation matrix contains 12 tests per platform after the post-read time-budget regression was added. Final exact-head run IDs, artifact IDs, digests, and denominator are recorded after all implementation documents are synchronized.

## 3. Required behaviors

### 3.1 Byte-safe read

- exact byte boundaries return `ok`;
- a split final UTF-8 code point is removed rather than replaced or emitted invalidly;
- truncation is explicit;
- `bytes_read` and `file_bytes` are numerical metadata;
- invalid UTF-8 and NUL content return `binary` without returning content.

### 3.2 Structured filesystem outcomes

Stable statuses and error codes cover:

- `permission-denied` / `WORKSPACE_PERMISSION_DENIED`;
- `disappeared` / `WORKSPACE_FILE_DISAPPEARED`;
- `io-error` / `WORKSPACE_IO_ERROR`.

Private OS exception text and absolute paths are not returned.

### 3.3 Bounded search

Search stops with `budget-exhausted` and a stable reason when it reaches:

- file limit;
- total byte limit;
- elapsed-time limit;
- match limit.

The time budget is checked after each bounded read so a single final file cannot overrun and still report `ok`. This is cooperative elapsed-time accounting, not a claim that the Runtime can interrupt an arbitrary blocking filesystem call.

### 3.4 Containment

Traversal, external absolute paths, symlink/reparse traversal, non-regular files, and identity changes remain `WorkspaceViolation` failures. Structured ordinary I/O results do not weaken the security boundary.

## 4. Intermediate evidence

Head `376740ac0d6fbe342dd922d35b025cc8825f6f19`, M2 Workspace P1 Gate run 4 (`30385270910`):

- Linux: 11/11, 0 failures/errors/skips;
- macOS: 11/11, 0 failures/errors/skips;
- Windows: 11/11, 0 failures/errors/skips.

Intermediate artifacts:

- Linux `8698678472`, digest `4ed9c1051a822f8c74970cef3ca5e35060d0976acc438dd67736f693041b79d1`;
- macOS `8698691738`, digest `e8743a468a1c2bef47bda384d7f01b51f3295b62ad398de8f3a94b76fda0b1bf`;
- Windows `8698695994`, digest `0be0898b78acdbbe6a2a4fe3128fa995c7f70bb7d54be7580d3f6f421f2975f3`.

This run is retained as non-final evidence because the post-read time-budget regression and final implementation documentation were added later.

## 5. Retained failures

Real failures from implementation remain visible, including:

- first production-tool patch indentation failure;
- focused Gate before the test module existed;
- failed first patch anchor for the post-read time check;
- malformed inserted regression indentation before exact file restoration.

No failed run is deleted, rerun-masked, or used as evidence for completion.

## 6. Final exact-head evidence (develop push `8c097a6`)

All gates passed on develop push commit `8c097a6348bc45cc40a24635124c3c2c845fed57`:

| Gate | Run ID | Result |
| --- | ---: | --- |
| Minimum CI | 30426308602 | PASS |
| M1 P0 Gate (PR branch) | 30385907629 | 140/140 per OS; 420/420 total |
| M2 ExecutionAdapter Gate | 30426308603 | 36/36 per OS; 108/108 total |
| M2 Runtime Lifecycle Gate | 30426308610 | 64/64 per OS; 192/192 total |
| M2 Workspace P1 Gate | 30426308607 | 12/12 per OS; 36/36 total |

Artifacts and digests are recorded in `docs/roadmap/m2-e-closeout.md`.

## 7. Exit judgment

M2-E Exit Gate is satisfied. `WS-003`–`WS-005` are promoted to `Verified`.

Repository release status remains **NO RELEASE**.
