# Support Policy

DeepSeek Runtime is currently in Open-source Alpha hardening. Support is community-based and prioritized by release risk.

## Supported scope

Maintainers prioritize:

1. security vulnerabilities and possible secret disclosure;
2. P0/P1 requirements in `docs/product/PRD.md`;
3. reproducible regressions in tagged releases;
4. installation, CI, and release-artifact failures;
5. factual documentation corrections.

Feature requests outside the Alpha scope may be deferred or closed as not planned.

## Where to ask

- Security vulnerability: follow `SECURITY.md`; do not use a public issue for exploit details.
- Reproducible bug: open an issue with version/commit, operating system, Python version, minimal reproduction, expected behavior, actual behavior, and sanitized logs.
- Design proposal: reference the affected PRD Requirement and ADR.
- Usage question: use an issue or discussion channel if enabled, with synthetic data only.

## Service level

This is an open-source project, not a paid support service. Response times are not guaranteed. Security response targets are listed separately in `SECURITY.md`.

## Supported environments

A platform/version is supported only when it is included in the release matrix and the corresponding release evidence is green. The target Alpha matrix is Python 3.11–3.13 on Linux, macOS, and Windows; until M5/M6 completes, current support remains development-only.

## Unsupported use

The project does not provide support guarantees for:

- untrusted multi-tenant execution;
- claims of kernel-level sandboxing;
- arbitrary command or network execution without an external isolation boundary;
- irreversible, high-value external side effects without reconciliation controls;
- modified forks whose changes are not included in the reproduction;
- leaked, shared, or embedded credentials.
