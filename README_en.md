# DeepSeek Runtime

> A local Agent Runtime Kernel for the DeepSeek API.
>
> **Current phase: Open-source Alpha Hardening. M1 and M2-A are closed. M2-B Policy/Approval is the next execution slice. Current release decision: NO RELEASE.**

[English](README_en.md) | [简体中文](README.md)

## Positioning

Calling a model API does not provide a reliable Agent. A Runtime must handle Provider protocols, tool contracts, policy and approval, budgets, recovery, evidence privacy, and release verification.

This repository has completed the M1 core contracts, Workspace containment, constrained rollback, and ambiguous side-effect recovery. M2-A was merged through PR #14: `ToolRegistry` is the production tool collection, arguments use JSON Schema validation, results and malformed tool calls have structured boundaries, and the CLI has completed the Registry migration. Policy, Approval, ExecutionAdapter, and the unified Runtime lifecycle remain incomplete. [`docs/product/PRD.md`](docs/product/PRD.md) is the sole source of truth for the first public Alpha scope, priority, and acceptance criteria.

## Current factual status

| Capability | Current assessment |
| --- | --- |
| DeepSeek Provider request and basic response handling | Partial |
| Text-only and basic tool loop | Partial |
| ToolRegistry and argument/result boundaries | Verified for M2-A; PR #14, Minimum CI run 106, M1 P0 Gate run 56 |
| Mandatory Policy and Approval path | Blocked; next M2-B slice |
| Mandatory ExecutionAdapter path | Blocked; M2-C |
| Workspace containment and symlink/reparse-point defense | Verified for the M1 P0 scope; 20/20 on Linux, macOS, and Windows |
| Checkpoint and Evidence | Partial; contracts are frozen but production storage still requires separation |
| Side-effect recovery | Verified for the M1 P0 scope; persisted running non-idempotent effects enter manual reconciliation and do not auto-retry |
| File changes and rollback | Verified for the M1 P0 scope; opaque handles, durable journals, expiry, scope, and conflict checks are covered |
| Evidence, diagnostics, usage, and cost | Partial |
| Cross-platform CI | M1 P0 covers Linux/macOS/Windows with Python 3.11; the full release matrix remains Planned |
| wheel/sdist, artifact provenance and integrity | Planned/Blocked |

Evidence and plans:

- [Complete Code Review](docs/reviews/2026-07-27-code-review.md)
- [M1 Code Review Closeout](docs/reviews/2026-07-28-m1-closeout-review.md)
- [M1 P0 Cross-platform Report](docs/testing/m1-p0-report.md)
- [M1 Integrated Closeout](docs/roadmap/m1-closeout.md)
- [M2-A ToolRegistry Closeout](docs/roadmap/m2-a-closeout.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [Open-source Readiness Execution Plan](docs/roadmap/open-source-readiness-plan.md)

## Security boundary

The current implementation is **not an operating-system security sandbox**.

- `NoIsolationLocalAdapter` is for trusted local development only.
- `RestrictedSubprocessAdapter` targets a minimal environment, explicit cwd, timeout, process-tree cleanup, cancellation, and output limits, but still does not provide kernel isolation.
- Workspace containment does not promise protection against a malicious concurrent process with the same host-user permissions.
- The durable ChangeJournal is owner-only local storage by default; owner-only is not encryption.
- The current version is not suitable for untrusted multi-tenancy, arbitrary command execution, or high-value irreversible side effects.
- The Runtime does not promise universal exactly-once behavior; ambiguous effects enter manual reconciliation.

See the [Threat Model](docs/security/threat-model.md) and [Security Policy](SECURITY.md).

## Developer quick start

These commands exercise the development baseline; they do not imply that the Release Gate has passed.

```bash
git clone https://github.com/yuanchenglu/deepseek_runtime.git
cd deepseek_runtime

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

deepseek-runtime doctor --json
python -m unittest discover -s tests -v
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

Before using a live API, read the security boundary and use synthetic, non-sensitive input only:

```bash
export DEEPSEEK_API_KEY=sk-your-key-here
deepseek-runtime run --workspace . "Describe this repository's structure"
```

## Minimum quality gate

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
```

M1 P0 focused gate:

```bash
python scripts/m1_p0_gate.py --repetitions 20 --output m1-p0-local.json
```

CI output is the shareable execution evidence. A local verbal claim is not release evidence.

## Documentation

Start at [`docs/INDEX.md`](docs/INDEX.md).

Core documents:

- [PRD](docs/product/PRD.md)
- [Product Architecture](docs/architecture/product-architecture.md)
- [Technical Architecture](docs/architecture/technical-architecture.md)
- [ADR Index](docs/adr/README.md)
- [Test Plan](docs/testing/test-plan.md)
- [Test Cases](docs/testing/test-cases.md)
- [Known Unknowns](docs/known-unknowns.md)

## Contributing and support

- [Contributing](CONTRIBUTING.md)
- [Support Policy](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Reporting](SECURITY.md)

The default development flow is feature branch → PR → CI → `develop`. An exceptional direct push to `develop` is allowed only when the PR flow is persistently unavailable in the current environment, and the commit must record the root cause and remaining technical debt.

Before the first Alpha, contributions should close a P0/P1 blocker, improve verification, or correct a factual documentation error.

## License and attribution

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
