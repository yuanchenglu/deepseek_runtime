# M2-F CLI Core Closeout

> Milestone: M2-F CLI Core — Output Protocol
> Status: **CLOSED**
> Implementation: direct push `432db3e` to `develop`
> Release decision: **NO RELEASE**

## 1. Closed scope

M2-F closed the CLI output protocol gap for `CLI-002`–`CLI-006`:

- `run` default output is the final answer text on stdout;
- `--report path.json` writes safe evidence to a file (uses `to_safe_dict()`);
- `--json` outputs machine-readable JSON (safe mode, no prompt/response text);
- `--unsafe-debug-content` requires explicit flag and prints a warning to stderr;
- exit codes: 0=ok, 1=run failed, 2=workspace invalid, 3=config invalid;
- workspace not-exists or is-a-file produces a friendly error on stderr with exit 2;
- new `ErrorCode`: `WORKSPACE_INVALID`, `CONFIG_INVALID`.

No durable checkpoint, Provider streaming/retry, M3 recovery, or release engineering was added.

## 2. Final exact-head evidence

All gates passed on develop push commit `432db3e`:

| Gate | Run | Result |
| --- | ---: | --- |
| Minimum CI | 30792953108 | PASS |
| M2 ExecutionAdapter Gate | 30792953145 | 36/36 per OS; 108/108 total |
| M2 Runtime Lifecycle Gate | 30792953114 | 64/64 per OS; 192/192 total |
| M2 Workspace P1 Gate | 30792953127 | 12/12 per OS; 36/36 total |

Local: 165 tests pass, 1 skip (Windows junction).

## 3. Artifacts and digests

### Minimum CI

- Pyright diagnostics: `8847736851`; `sha256:9ae9152c55799f58b9d4624cc1a1edbd01bb6c735f2cc8a8d70b71d67ee22acc`.

### M2 ExecutionAdapter

- Linux: `8847736990`; `sha256:724c9b151ffcdd7684ccd6d79ace57a3c3977d012903f1660cc7bfa52d22deb0`.
- macOS: `8847735093`; `sha256:2ad8491c4bd986ed09a65264b180b3109ff57d47d0f571175315b93cf9c8245c`.
- Windows: `8847746579`; `sha256:6e45dfb99be57412f92272aa70d34cc7193b7746781ec1758ede1270790aba98`.

### M2 Runtime Lifecycle

- Linux: `8847736598`; `sha256:c65aba4db6fff0320ca15d3552aa8464c8c6fee84d0017ff059e342a46007281`.
- macOS: `8847736664`; `sha256:a94c32c55f7ee822db2341160f964d3868a52966e37d62c8218396ab05232b90`.
- Windows: `8847745658`; `sha256:b0eedca0ca7558342fc835aa4b62652d726e1745fbcfced55a39eec7668d994e`.

### M2 Workspace P1

- Linux: `8847737824`; `sha256:df14d83b51e0fa777546c9872aff37392d9e2a5bb359255f11843524be45fc36`.
- macOS: `8847738462`; `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Windows: `8847742571`; `sha256:3c9f044499b69cf5fe7e4a1011f63a15982283fd6ce30b0a371ec43d7ba101ad`.

## 4. Requirement status

Promoted to `Verified`:

- CLI-002: `run` default outputs final answer — Verified;
- CLI-003: `--report` writes safe evidence — Verified;
- CLI-004: `--unsafe-debug-content` requires explicit flag — Verified;
- CLI-005: exit code matrix — Verified;
- CLI-006: workspace error friendly failure — Verified.

CLI-001 remains `Verified` (doctor --json, from PR #10).

## 5. Exit judgment

M2-F Exit Gate is satisfied. M2-G Integrated Closeout is the next legal work item.

Repository release status remains **NO RELEASE**.
