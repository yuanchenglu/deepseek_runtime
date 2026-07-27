# ADR-009: Rollback authorization uses opaque handles and a durable ChangeJournal

- Status: Accepted
- Date: 2026-07-28
- Requirements: CHG-001, CHG-002, CHG-005, CHG-008, CHG-010

## Context

The current public `RollbackToken` contains caller-visible paths and original bytes. `ChangeManager.rollback()` trusts that payload and restores it directly, allowing forged data to target files outside the workspace. An in-memory manager-only token would close forgery but would break rollback after process restart.

## Decision

The public rollback capability is an opaque `RollbackHandle` containing only a schema version and a cryptographically random identifier with at least 256 bits of entropy.

The identifier resolves to a private durable `ChangeJournalEntry` controlled by `ChangeManager`. The journal contains:

- workspace identity;
- changeset identity;
- relative paths only;
- pre-change and post-change hashes;
- recovery bytes and file metadata;
- creation and expiry time;
- consumed state;
- schema version and storage protection.

The caller cannot submit or modify paths, hashes, original content, workspace identity, expiry or consumed state.

Before rollback, the manager must:

1. resolve the handle from protected storage;
2. reject missing, malformed, expired or consumed handles;
3. verify workspace and changeset binding;
4. resolve every journal path through current containment checks;
5. verify current content matches the recorded post-change hash;
6. apply policy/approval rules;
7. restore through bounded atomic-write primitives;
8. persist one-time consumption before reporting success.

Default retention is seven days unless a stricter product policy is configured. Cleanup runs at journal-store startup, after successful consumption, and through an explicit maintenance command. The default storage mode is owner-only filesystem permissions; an injectable encryption provider may upgrade storage to `encrypted`.

Journal files, handles and recovery bytes are private checkpoint material and must not appear in Publishable Evidence. Public audit records contain only structural identities, relative path counts, status, error code and timing.

## Consequences

- Restart-safe rollback requires a durable journal store.
- A copied handle alone is insufficient across a different workspace.
- Rollback remains best-effort across multiple files; conflict and partial-restoration states must be explicit.
- Journal encryption does not replace workspace authorization or filesystem permissions.
- Legacy `RollbackToken` remains deprecated until M1-C migration removes it from the production path.

## Rejected alternatives

- Trust a serialized caller token: permits forgery and path substitution.
- Sign a self-contained token carrying original bytes: expands secret exposure, payload size and key-management risk.
- Keep only in memory: breaks process-restart recovery.
- Store absolute paths: leaks host layout and weakens workspace rebinding checks.

## Verification

`TC-CHG-001`, `TC-CHG-002`, `TC-CHG-005`, `TC-CHG-009`, `TC-CHG-011`, restart/expiry/cross-workspace fixtures, post-change conflict tests, and public-evidence content scans.
