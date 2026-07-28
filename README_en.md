# DeepSeek Runtime

> A local Agent Runtime Kernel for the DeepSeek API.
>
> **Current phase: Open-source Alpha Hardening. M1, M2-A, and M2-B are closed. M2-C ExecutionAdapter is in progress in Draft PR #18. Current release decision: NO RELEASE.**

[English](README_en.md) | [简体中文](README.md)

## Positioning

Calling a model API does not provide a reliable Agent. A Runtime must handle Provider protocols, tool contracts, policy and approval, bounded execution, budgets, recovery, evidence privacy, and release verification.

This repository has completed the M1 contracts, Workspace containment, constrained rollback, and ambiguous side-effect recovery. M2-A established ToolRegistry as the production tool collection. M2-B attached PermissionPolicy and ApprovalProvider to the Runtime path. M2-C is establishing the common ExecutionAdapter boundary, bounded subprocess controls, and focused cross-platform evidence in PR #18. The complete Runtime lifecycle, budgets, Provider cancellation, durable checkpoints, Workspace P1, CLI protocol, and release engineering remain incomplete. [`docs/product/PRD.md`](docs/product/PRD.md) is the sole source of truth for Alpha scope and acceptance.

## Current factual status

| Capability | Current assessment |
| --- | --- |
| DeepSeek Provider request and basic response handling | Partial |
| Text-only and basic tool loop | Partial |
| ToolRegistry and argument/result boundaries | Verified for M2-A; PR #14, Minimum CI run 106, M1 P0 Gate run 56 |
| Mandatory Policy and Approval path | Verified for the M2-B in-memory path; PR #16, runs 129/77 |
| ExecutionAdapter boundary | Implemented on Draft PR #18; code-complete runs 159/105 and M2 Gate run 9 with 36/36 per OS; not merged |
| Restricted subprocess controls | Implemented on PR #18: minimal env, contained cwd, timeout, combined byte output, cancellation handoff, process-tree cleanup |
| Kernel / OS isolation | Not provided; every current adapter declares `kernel_isolation=false` |
| Durable approval checkpoint and resume | Partial; persistence timing, resume, and migration remain M2-D/M3 |
| Complete cancellation | Partial; tool-execution handoff exists, Provider-before/during cancellation remains M2-D/M4 |
| Workspace containment and link defense | Verified for M1 P0; 20/20 on Linux, macOS, and Windows |
| Workspace read/search budgets | Planned; M2-E |
| Checkpoint and Evidence | Partial |
| Side-effect recovery | Verified for M1 P0; ambiguous non-idempotent effects enter manual reconciliation |
| File changes and rollback | Verified for M1 P0; opaque handles, durable journals, expiry, scope, and conflict checks |
| Cross-platform CI | M1 P0 and M2-C Adapter gates cover Linux/macOS/Windows with Python 3.11; full release matrix remains Planned |
| wheel/sdist, provenance, and integrity | Planned/Blocked |

Evidence:

- [PRD](docs/product/PRD.md)
- [Threat Model](docs/security/threat-model.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [M1 P0 Cross-platform Report](docs/testing/m1-p0-report.md)
- [M2-A ToolRegistry Closeout](docs/roadmap/m2-a-closeout.md)
- [M2-B Policy/Approval Closeout](docs/roadmap/m2-b-closeout.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [M2-C ExecutionAdapter Test Report](docs/testing/m2-execution-adapter-report.md)
- [Open-source Readiness Plan](docs/roadmap/open-source-readiness-plan.md)

## Current production tool-call path

PR #18 targets:

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider (ASK only)
→ ExecutionAdapter
→ result normalization
→ content-minimized evidence
```

Current guarantees:

- Registry/schema/Policy/Approval rejection invokes neither Adapter nor handler.
- The default `NoIsolationLocalAdapter` preserves trusted local Python handlers but explicitly provides no timeout, running cancellation, output limit, environment minimization, process cleanup, or isolation.
- `RestrictedSubprocessAdapter` enforces argument arrays, `shell=False`, contained cwd, minimal environment, secret/loader-key stripping, ToolSpec timeout, combined stdout/stderr byte limit, cancellation handoff, and process-tree cleanup.
- Execution events exclude arguments, command, cwd, env, stdin, stdout, stderr, result, and exception messages.
- `WorkspaceSandbox.run()` no longer calls `subprocess.run` directly and delegates to its configured Adapter.

## Security boundary

The current implementation is **not an operating-system security sandbox**.

- `NoIsolationLocalAdapter` is only for trusted local tools.
- `RestrictedSubprocessAdapter` is a process-resource boundary, not filesystem, network, syscall, user, or kernel isolation.
- The command classifier is not isolation; wrapped commands may remain classified as `SHELL_SAFE`.
- A restricted child may access resources available to the same host user.
- Process-tree cleanup is best-effort against hostile processes, despite passing the supported-platform fixture.
- A Python command builder is semi-trusted; M2-C cannot stop a malicious builder from causing effects before returning a request.
- Workspace containment does not defend against malicious concurrent processes with the same user privileges.
- The Runtime does not promise universal exactly-once behavior.

See the [Threat Model](docs/security/threat-model.md) and [Security Policy](SECURITY.md).

## Developer quick start

These commands exercise the development baseline; they do not imply Release Gate completion.

```bash
git clone https://github.com/yuanchenglu/deepseek_runtime.git
cd deepseek_runtime

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

deepseek-runtime doctor --json
python -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Use only synthetic, non-sensitive input with a live API:

```bash
export DEEPSEEK_API_KEY=sk-your-key-here
deepseek-runtime run --workspace . "Describe this repository's structure"
```

## Quality gates

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
```

Focused gates:

```bash
python scripts/m1_p0_gate.py --repetitions 20 --output m1-p0-local.json
python scripts/m2_execution_gate.py --output m2-execution-local.json
```

CI output is shareable evidence; a local verbal claim is not release evidence.

## Documentation

Start at [`docs/INDEX.md`](docs/INDEX.md).

- [Product Architecture](docs/architecture/product-architecture.md)
- [Technical Architecture](docs/architecture/technical-architecture.md)
- [Runtime Core Contracts](docs/contracts/runtime-contracts.md)
- [Policy/Approval Contract](docs/contracts/policy-approval.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [Test Plan](docs/testing/test-plan.md)
- [Test Cases](docs/testing/test-cases.md)
- [Known Unknowns](docs/known-unknowns.md)

## Contributing and support

- [Contributing](CONTRIBUTING.md)
- [Support Policy](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Reporting](SECURITY.md)

Default flow: feature branch → Draft PR → tests/Traceability/docs/CI → strict review → Ready → `develop`. `master` is only for a release that passes the final Release Gate.

## License and attribution

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
