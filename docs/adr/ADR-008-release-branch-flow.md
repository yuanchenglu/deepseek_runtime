# ADR-008: Release flow is develop → master → tag

- Status: Accepted
- Date: 2026-07-27
- Requirements: OSS-001, OSS-006–OSS-011

## Context

Development and public release evidence must remain distinguishable. Direct development on the release branch makes it difficult to prove which reviewed commit produced a tag and artifact, while long-lived divergence between branches creates untested combinations.

## Decision

- `develop` is the integration branch for ordinary work.
- Focused branches and pull requests target `develop`.
- Release Candidate fixes land in `develop` first.
- After every Release Gate passes, the exact verified `develop` commit is merged to `master`.
- Tags are created only from `master`.
- Release artifacts are created only by the protected tag workflow.
- Hotfixes branch from `master`, land in `master`, and are immediately backported to `develop` using the same or equivalent change.

The release manifest records source commit, tag, package version, workflow identity, artifact digests, and schema version.

## Consequences

- `master` is not a development branch and may lag `develop` during hardening.
- A green `develop` commit is not a release until RC and artifact gates pass.
- Branch protection should require the relevant checks and prevent direct release-branch development where repository settings permit.
- If an emergency hotfix cannot be backported cleanly, release activity pauses until divergence is resolved.

## Rejected alternatives

- Develop directly on `master`: weak provenance and review separation.
- Tag from feature/develop branches: allows release artifacts not represented by the release branch.
- Maintain unrelated master/develop histories: creates unbounded drift.

## Verification

`TC-OSS-001`–`TC-OSS-011`, tag-workflow provenance checks, version/tag/artifact consistency, and comparison showing no unexplained release-branch divergence.
