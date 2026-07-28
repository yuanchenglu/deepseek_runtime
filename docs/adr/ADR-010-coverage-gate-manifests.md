# ADR-010: Coverage and Release Gates use explicit manifests

- Status: Accepted
- Date: 2026-07-28
- Requirements: OSS-001, OSS-003, OSS-004, OSS-011

## Context

Percentages such as “90% Provider normalization” or “95% state coverage” are not auditable without a stable denominator. A global line-coverage number can also hide untested security, recovery and release paths.

## Decision

Every quantitative gate is backed by a versioned manifest that defines its denominator, required evidence and evaluation rule.

### State-transition manifest

`docs/contracts/runtime-state-transitions.json` enumerates every legal state edge. Transition coverage is:

```text
covered legal transitions / total legal transitions in the manifest
```

Illegal-edge rejection is a separate mandatory test class and is not added to the denominator as arbitrary state pairs.

### Provider normalization manifest

M4 must list every supported Provider outcome class and fixture:

- success text;
- tool calls;
- non-object root;
- missing/empty/malformed choices;
- malformed message/tool call;
- non-2xx classifications;
- timeout, DNS/TLS/network failure;
- retryable rate limit/server failure;
- response-size violation;
- SSE framing and malformed events.

Coverage is the number of passing named fixtures divided by the manifest fixture count. Alpha requires 100% of P0/P1 fixtures, not “approximately 90%”.

### Security and recovery manifests

P0 adversarial and crash-window cases are named records. Each required platform/run count is part of the denominator. Reruns do not erase failed attempts.

### Source coverage

Line/branch coverage is supporting evidence. M5 configuration must define:

- measured packages;
- omitted generated/vendor files;
- line and branch thresholds;
- critical modules requiring stricter thresholds;
- retained machine-readable report.

A threshold cannot replace named P0/P1 cases.

### Release Gate manifest

The Release Gate is a boolean conjunction of named requirements. Missing, stale, skipped, flaky or inaccessible evidence is failure. Gate coverage is not averaged; all mandatory entries must pass.

## Consequences

- Denominators change only through reviewed manifest changes.
- New legal transitions or supported protocol cases automatically expand required tests.
- CI reports both named-case completion and source coverage.
- Partial metrics cannot be presented as release readiness.

## Rejected alternatives

- Global coverage percentage only: hides semantic gaps.
- Dynamic denominator based on tests discovered at runtime: allows absent tests to improve the score.
- Weighted average Release Gate: permits a critical failure to be masked by unrelated passes.
- Manual spreadsheet without repository versioning: cannot be reproduced from a commit.

## Verification

- transition manifest equals the Python transition table;
- every manifest item maps to at least one Test Case and CI result;
- missing manifest evidence produces `No Release`;
- source coverage configuration and reports are committed or retained as build artifacts;
- PRD/Test/Traceability scripts reject orphaned P0/P1 entries.
