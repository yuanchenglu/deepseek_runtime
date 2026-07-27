# DeepSeek Runtime

> A local Agent Runtime Kernel for the DeepSeek API.
>
> **Current phase: Open-source Alpha Hardening. Current release decision: NO RELEASE.**

[English](README_en.md) | [简体中文](README.md)

## Positioning

Calling a model API does not provide a reliable Agent. A Runtime must handle Provider protocols, tool contracts, policy and approval, budgets, recovery, evidence privacy, and release verification.

This repository contains several of those primitives, but the end-to-end execution path is not yet complete or non-bypassable. [`docs/product/PRD.md`](docs/product/PRD.md) is the sole source of truth for the first public Alpha scope, priority, and acceptance criteria.

## Current factual status

| Capability | Current assessment |
| --- | --- |
| DeepSeek Provider request and basic response handling | Partial |
| Text-only and basic tool loop | Partial |
| Mandatory ToolRegistry, validation, policy, and approval path | Blocked |
| Workspace containment and symlink/reparse-point defense | Blocked by P0 work |
| Checkpoint and Evidence | Partial; current models must be separated |
| Side-effect recovery | Blocked; uncertain effects must not auto-retry |
| File changes and rollback | Blocked; handle and conflict semantics need hardening |
| Evidence, diagnostics, usage, and cost | Partial |
| Cross-platform CI, wheel/sdist, artifact provenance and integrity | Planned/Blocked |

Evidence and plans:

- [Complete Code Review](docs/reviews/2026-07-27-code-review.md)
- [Current Test Report](docs/testing/test-report-2026-07-27.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [Open-source Readiness Execution Plan](docs/roadmap/open-source-readiness-plan.md)

## Security boundary

The current implementation is **not an operating-system security sandbox**.

- `NoIsolationLocalAdapter` is for trusted local development only.
- `RestrictedSubprocessAdapter` targets a minimal environment, explicit cwd, timeout, process-tree cleanup, cancellation, and output limits, but still does not provide kernel isolation.
- The current version is not suitable for untrusted multi-tenancy, arbitrary command execution, or high-value irreversible side effects.
- The Runtime does not promise universal exactly-once behavior; ambiguous effects must enter manual reconciliation.

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

## M0 minimum quality gate

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
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

Before the first Alpha, contributions should close a P0/P1 blocker, improve verification, or correct a factual documentation error.

## License and attribution

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
