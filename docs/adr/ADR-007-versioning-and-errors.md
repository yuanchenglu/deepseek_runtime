# ADR-007: Explicit compatibility for APIs, schemas, and error codes

- Status: Accepted
- Date: 2026-07-27
- Requirements: CFG-002, RUN-010, SES-005, EVD-006, CLI-005

## Context

Runtime callers and persisted state depend on public types, machine-readable errors, CLI exits, and independently versioned schemas. String exceptions and implicit schema changes make recovery and integration behavior unverifiable.

## Decision

The project uses explicit compatibility domains:

1. package/API version;
2. checkpoint schema version;
3. evidence schema version;
4. diagnostics schema version;
5. release-manifest schema version;
6. machine-readable error-code registry and CLI exit mapping.

Each serialized document declares its schema name and version. Readers validate supported versions, migrate only through tested paths, and reject unsupported future versions without modifying the source data.

Error codes are stable identifiers. Human messages may improve without changing semantics; callers must not parse English text. Removing, renaming, or materially redefining an error code is a breaking change under the compatibility policy.

The package version has one authoritative source. Build metadata, diagnostics, artifacts, manifests, and tags derive from or verify against it.

## Consequences

- Schema migrations are explicit code with fixtures, not opportunistic dictionary access.
- Unknown fields follow a documented per-schema policy; unknown versions never silently downgrade.
- CLI exit codes are bounded categories mapped from stable Runtime errors.
- Public API and schema changes require release notes and, when breaking, a superseding ADR.

## Rejected alternatives

- Infer compatibility from package version alone: persisted schemas evolve independently.
- Depend on exception class/message only: unstable across refactors and unsuitable for external automation.
- Best-effort loading of future schemas: risks silent corruption.

## Verification

`TC-CFG-002`, `TC-RUN-010`, `TC-SES-005`, `TC-EVD-006`, `TC-CLI-005`, artifact-version consistency, and unsupported-future-version fixtures.
