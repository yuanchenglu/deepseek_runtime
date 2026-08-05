# ADR-006: Use Pyright as the repository type checker

- Status: Accepted
- Date: 2026-07-27
- Requirements: OSS-003, NFR-MAINT

## Context

The Runtime contracts rely on explicit Provider, Tool, State, Error, Checkpoint, and Evidence types. The repository needs one reproducible type checker rather than optional local preferences.

## Decision

Pyright is the normative type checker.

M0 runs Pyright against `src/deepseek_runtime` on Python 3.11 in basic mode and fails on errors. The checked surface expands with each milestone. New public APIs and new/modified contract code must not introduce type errors or untyped public signatures.

Configuration is stored in repository-controlled configuration. CI output is the authoritative evidence.

## Consequences

- Contributors may use another editor or secondary checker, but Pyright determines the gate.
- Existing code is not declared fully typed merely because M0 basic mode passes.
- Strictness can be raised per module after defects are fixed; weakening a diagnostic to pass CI requires documented justification.
- Generated, fixture, or platform-specific exclusions must be narrow and reviewable.

## Rejected alternatives

- Support both Mypy and Pyright as equal gates: duplicate policy and inconsistent diagnostics.
- Mypy as the sole checker: viable, but Pyright provides fast CI/editor feedback and aligns with the selected baseline workflow.
- No type checker until API freeze: would allow unstable contracts to spread before M1/M2.

## Verification

The `Minimum CI` workflow runs Pyright on every `develop` push and pull request. `TC-OSS-002` covers the combined lint/type/coverage release gate in later milestones.
