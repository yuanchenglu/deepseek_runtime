# M2-E Workspace P1 Closeout

> Milestone: M2-E Workspace P1 — Bounded Read and Search
> Status: **CLOSED**
> Implementation: direct push `8c097a6348bc45cc40a24635124c3c2c845fed57` to `develop`
> Release decision: **NO RELEASE**

## 1. Closed scope

M2-E closed the implementation gap for `WS-003`–`WS-005` without weakening the verified M1 Workspace containment boundary:

- UTF-8 byte-safe bounded reads with explicit truncation metadata;
- file-count, total-byte, elapsed-time, match-count, and per-file search budgets;
- structured binary, permission-denied, disappeared-file, and ordinary I/O outcomes;
- production `WorkspaceTools` remains behind the single `WorkspaceResolver`;
- Linux, macOS, and Windows focused verification.

No CLI protocol, durable checkpoint, Provider streaming/retry, OS/kernel isolation, or release engineering was added.

## 2. Implementation note

The M2-E implementation was pushed directly to `develop` as commit `8c097a6`. The PR branch `agent/m2-e-workspace-p1` and Draft PR #22 were used for CI validation during development; the final state was pushed to `develop` after all gates passed on the PR branch. This is recorded as an exceptional direct push; the code, tests, gate scripts, and CI workflow are all present on `develop`.

## 3. Final exact-head evidence

All gates passed on develop push commit `8c097a6348bc45cc40a24635124c3c2c845fed57`:

| Gate | Run | Result |
| --- | ---: | --- |
| Minimum CI | 30426308602 | PASS |
| M2 ExecutionAdapter Gate | 30426308603 | 36/36 per OS; 108/108 total |
| M2 Runtime Lifecycle Gate | 30426308610 | 64/64 per OS; 192/192 total |
| M2 Workspace P1 Gate | 30426308607 | 12/12 per OS; 36/36 total |

M1 P0 Gate (PR-triggered, run 30385907629 on `agent/m2-e-workspace-p1`): 140/140 per OS; 420/420 total.

## 4. Artifacts and digests

### Minimum CI

- Pyright diagnostics: `8713729465`; `sha256:8cde26023c769b3aa49d470ab75447a62e6f2e13fe03d3934fced4189b5c93b3`.

### M1 P0

- Linux: `8698921437`; `sha256:739c04f3b78edf390b77049d939d3f6f893fe3f7ecac3116efeb0c87ad4684ce`.
- macOS: `8698922029`; `sha256:9c93e7cae61dc63731482d00b6e932b65fc82328f56f20fe56700d32d5c9a222`.
- Windows: `8698938608`; `sha256:85eb466ca02b75accbe34dc0e4d07501767032df4ef52589602b644d69218666`.

### M2 ExecutionAdapter

- Linux: `8713729920`; `sha256:6cc3ad28accc3788e85137c0fae1d6ddca0774310047d80d55cabe0cd2ac1807`.
- macOS: `8713730198`; `sha256:e3f22bf5f91a8e4b344fa2e8ed87bdb2e3368b30d0d7bde75a6a121f8593a03c`.
- Windows: `8713734576`; `sha256:40b54bfcd9195948488f1c2e0c24f25581e96cc3156f8a279f5f22b368d1ea9c`.

### M2 Runtime Lifecycle

- Linux: `8713728737`; `sha256:30dfbf07a0ee9d45f244c47e79875f36f233b4e51cfb2862c27890f8a9962d2b`.
- macOS: `8713730161`; `sha256:bc3587435d7678ce06293656dbd6520c56889ed9663224076d27383068fcba62`.
- Windows: `8713733773`; `sha256:48edbef09932e8f1d79cf16496587f39524adb3c9a4e1652bb06f0893192dbf6`.

### M2 Workspace P1

- Linux: `8713731325`; `sha256:936a902bae41cba2ee7456e7e4cd0eecf0269402b501065c42e8255f153138ba`.
- macOS: `8713733131`; `sha256:3f1fbb0dab5373df7b129f31ed69e9e7eac38d939964092244699e7b72d5a9fc`.
- Windows: `8713745710`; `sha256:95cf30ae0d0bd215915f121420c74147cd37586e2749aefcbdca35cb8824f524`.

## 5. Retained failures

The following failures remain visible and were not rerun-masked or deleted:

- M2 Workspace P1 Gate runs 30385210948, 30385662767, 30385584567 (PR branch, pre-test-module and pre-regression);
- Minimum CI run 30385661952 (PR branch, indentation failure from first production-tool patch);
- M1 P0 Gate cancelled runs 30385132208, 30385153849, 30385210966, 30385667214, 30385876145;
- M1 P0 Gate failure runs 30384773280, 30384862620 (PR branch, pre-fix).

## 6. Requirement status

Promoted to `Verified` after merge to `develop` and exact-head evidence:

- WS-003: UTF-8 byte-safe bounded reads with truncation metadata — Verified;
- WS-004: search file/byte/time/match budgets — Verified;
- WS-005: structured binary/permission/disappeared/IO outcomes — Verified.

## 7. Exit judgment

M2-E Exit Gate is satisfied for its defined implementation slice. M2-F CLI Core is now the next legal work item.

Repository release status remains **NO RELEASE** until M2-F/M2-G/M3/M4/M5/M6 and the final Release Gate are complete.
