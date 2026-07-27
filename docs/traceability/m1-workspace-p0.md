# M1-B Workspace Containment Evidence

> Pull request: #7
> Stacked base: PR #6 (`agent/m1-core-contracts`)
> Validated implementation commit: `d3cb31734d440c68cf6a98195e61787649c22f0e`
> Workflow: `Minimum CI`
> Implementation run: 44 (`30290538817`), `success`
> Final evidence run: pending
> Release decision: **NO RELEASE**

## 1. Scope

This change replaces the duplicated path logic in `WorkspaceSandbox` and `WorkspaceTools` with one `WorkspaceResolver`.

The Alpha policy is conservative:

- workspace paths may not escape by `..` or an external absolute path;
- existing ancestors are inspected with `lstat`;
- symlinks and Windows reparse points are not followed, even when they target another location inside the workspace;
- recursive search uses `os.scandir(..., follow_symlinks=False)` semantics instead of `Path.rglob()`;
- only regular files are yielded and read;
- file opening uses `O_NOFOLLOW` where the platform provides it and compares pre-open and opened file identity where stable device/inode values exist;
- `.git` is excluded from default search.

## 2. Requirement mapping

| Requirement | Implementation | Test evidence | Current status | Remaining evidence |
| --- | --- | --- | --- | --- |
| WS-001 | lexical containment plus contained ancestor inspection; `WorkspaceSandbox` and `WorkspaceTools` share the resolver | traversal and external absolute paths rejected 20 consecutive times; internal file read/search succeeds | Partial | repeat on Windows and macOS; retain full M1 P0 report |
| WS-002 | no-follow traversal, symlink/reparse rejection, regular-file descriptor validation | external file symlink and directory symlink cannot be read/searched across 20 repetitions; reparse attribute classifier test | Partial | actual Windows junction/reparse test in the full platform matrix |

## 3. Test inventory

`tests/test_workspace_security.py` adds:

1. repeated traversal and external absolute path rejection;
2. normal contained file read and search;
3. repeated external file symlink non-disclosure;
4. repeated external directory symlink non-traversal;
5. rejection of a nonexistent leaf beneath a symlink parent;
6. `.git` exclusion;
7. Windows reparse attribute classification;
8. an actual Windows junction test that runs only on Windows.

Run 44 passed critical Ruff diagnostics, Pyright, all existing and new unit tests, package import, tracked-secret scan, and documentation checks.

## 4. Security boundary

This closes the known model-controlled `rglob()` symlink escape on the validated POSIX runner. It does not claim:

- kernel isolation;
- protection against a malicious concurrent process with equivalent host permissions replacing filesystem entries continuously;
- Windows junction verification before the Windows CI job executes;
- rollback safety, which remains M1-C;
- side-effect recovery safety, which remains M1-D.

The Threat Model exclusion for malicious same-host concurrent replacement remains unchanged.

## 5. Exit interpretation

The implementation is in the production `WorkspaceSandbox` and `WorkspaceTools` paths, but WS-001/WS-002 remain `Partial` until platform evidence and the consolidated M1 P0 repetition report are retained.

Repository status remains **NO RELEASE**.
