# Breaking-change and Compatibility Policy

> Status: M0 baseline
> Applies to: public Python API, CLI, configuration, error codes, checkpoint/evidence schemas, release artifacts

## 1. Alpha stability level

Before the first tagged Alpha, interfaces may change to close P0/P1 blockers. Changes must still be intentional, documented, tested, and traceable.

After the first tagged Alpha:

- patch releases must not intentionally break documented public behavior;
- Alpha minor releases may introduce breaking changes only through the process below;
- security fixes may remove unsafe behavior immediately when compatibility would preserve a release-blocking vulnerability.

## 2. What counts as breaking

A change is breaking when it can invalidate a supported caller, persisted state, automation, or verification process, including:

- removing or renaming a public module, class, method, field, CLI option, command, or exit code;
- changing accepted input or returned output incompatibly;
- changing machine-readable error codes or meanings;
- rejecting a previously supported checkpoint/evidence schema without migration or explicit unsupported-version handling;
- changing configuration precedence or defaults with material security/runtime impact;
- changing artifact layout, manifest fields, or release provenance rules;
- weakening a documented security or recovery guarantee.

## 3. Required process

Every breaking change requires:

1. a PRD Requirement or release-blocker justification;
2. an ADR describing the current contract, proposed contract, alternatives, migration, and risks;
3. explicit schema/API version impact;
4. compatibility and migration tests;
5. updates to architecture, test cases, traceability, Known Unknowns, README, and release notes as applicable;
6. a deprecation period when safe and technically feasible.

## 4. Deprecation

A deprecation must:

- identify the replacement;
- emit a stable, testable warning where appropriate;
- state the earliest removal version;
- avoid leaking secrets or content in the warning;
- remain covered by tests until removal.

Deprecation may be skipped for exploitable behavior, impossible-to-recover state semantics, or claims that materially misrepresent the security boundary. The release notes must explain why.

## 5. Schema compatibility

Checkpoint, Evidence, Diagnostics, and release-manifest schemas are versioned independently.

Readers must either:

- accept and validate the version;
- migrate through an explicitly tested path; or
- return a machine-readable unsupported-version error without overwriting the original data.

Unknown future versions must never be silently coerced into the current schema.

## 6. Review gate

A reviewer must reject the change when migration, evidence, security implications, or versioning are ambiguous. Compatibility is part of Definition of Done, not deferred release-note work.
