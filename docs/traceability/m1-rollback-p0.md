# M1-C Rollback Authorization Evidence

> Pull request: #8
> Stacked base: PR #7 (`agent/m1-workspace-p0`)
> Validated implementation commit: `144c16f09f175a387dfd184f4e9883cf3e9a86dd`
> Workflow: `Minimum CI`
> Implementation run: 48 (`30291608906`), `success`
> Standard final validation: pending
> Release decision: **NO RELEASE**

## 1. Scope

The production `ChangeManager` no longer trusts a caller-provided rollback payload.

- `apply()` returns an opaque `RollbackHandle` containing only a random identifier and schema version.
- Private original bytes, relative paths, pre/post hashes, file mode, workspace identity, expiry and consumed state live in a durable `ChangeJournalStore`.
- Journal data is persisted before file writes through atomic owner-only files outside the workspace by default.
- `rollback()` resolves the protected journal entry, then revalidates workspace binding, expiry, one-time use, every current post-change hash and write permission before restoring anything.
- `RollbackToken` remains only as a source-compatibility alias to `RollbackHandle`; it contains no caller-controlled paths or original bytes.

## 2. Requirement mapping

| Requirement | Implementation | Test evidence | Current status | Remaining evidence |
| --- | --- | --- | --- | --- |
| CHG-001 | opaque 256-bit-class random handle; store lookup is authoritative | unknown handle and forged payload rejected 20 consecutive times | Partial | consolidated P0 report and cross-platform run |
| CHG-002 | journal paths must be relative and are resolved again through `WorkspaceSandbox` | malicious `../outside.txt` journal rejected; external file unchanged | Partial | consolidated P0 report and Windows run |
| CHG-005 | rollback requires current content hash to equal recorded post-change hash | external edit produces `ROLLBACK_CONFLICT` and is preserved | Partial | multi-file conflict/fault matrix in M3 |
| CHG-008 | public handle and audit events exclude original/new contents | explicit content-marker audit test | Partial | complete Evidence exporter migration in M3 |
| CHG-010 | atomic durable store, workspace binding, restart, expiry and consumed state | restart manager rollback, cross-workspace rejection, expiry, consumed reuse rejection | Partial | lock/concurrency, optional encryption and full retention maintenance evidence |

## 3. Adversarial tests

`tests/test_change_journal_security.py` verifies:

1. opaque handle shape and restart-safe rollback;
2. unknown handle and old-style forged payload rejection across 20 repetitions;
3. malicious external journal path rejection;
4. cross-workspace handle rejection;
5. expiry enforcement;
6. post-change conflict detection;
7. one-time consumption and created-file deletion;
8. audit records contain no original or new file content.

Run 48 passed critical Ruff diagnostics, Pyright, all existing and new unit tests, package import, tracked-secret scan and documentation checks.

## 4. Storage and privacy boundary

Default journal location:

```text
~/.deepseek-runtime/state/change-journal/
```

It can be relocated with `DEEPSEEK_RUNTIME_STATE_DIR` or dependency injection. Directories are requested as owner-only (`0700`) and entries as owner-only (`0600`) where the platform supports POSIX modes. Files are written through a temporary file, `fsync`, atomic replace and directory `fsync` on non-Windows systems.

Owner-only storage is not encryption. Encryption-at-rest remains an injectable M3 capability and a release requirement where the environment requires it.

## 5. Non-claims

This change does not claim:

- multi-file rollback is transactionally atomic;
- rollback can recover automatically from every crash during restoration;
- journal storage is encrypted by default;
- concurrent processes are serialized by a journal lock;
- Windows ACL semantics have been independently verified;
- side-effect tool recovery is fixed.

Those remain M1-D/M3/M5 work. Repository status remains **NO RELEASE**.
