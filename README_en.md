# DeepSeek Runtime

> A local Agent Runtime Kernel for the DeepSeek API.
>
> **Current phase: Open-source Alpha Hardening. M1, M2-A, M2-B, M2-C, and M2-D are closed. M2-E Workspace P1 is in progress. Current release decision: NO RELEASE.**

[English](README_en.md) | [简体中文](README.md)

## Positioning

Calling a model API does not provide a reliable Agent. A Runtime must handle Provider protocols, tool contracts, policy and approval, bounded execution, budgets, recovery, evidence privacy, and release verification.

This repository has completed the M1 contracts, Workspace containment, constrained rollback, and ambiguous side-effect recovery. M2-A established ToolRegistry as the production tool collection. M2-B attached PermissionPolicy and ApprovalProvider to the Runtime path. M2-C merged the common ExecutionAdapter boundary, bounded subprocess controls, and a focused cross-platform gate into `develop`. PR #20 merged the Runtime lifecycle, task budgets, Provider-before-call cancellation, and tool-error policy into `develop`. Provider in-flight cancellation, durable checkpoints, Workspace P1, the CLI protocol, and release engineering remain incomplete. [`docs/product/PRD.md`](docs/product/PRD.md) is the sole source of truth for Alpha scope and acceptance.

## Current factual status

| Capability | Current assessment |
| --- | --- |
| DeepSeek Provider request and basic response handling | Partial |
| Text-only and basic tool loop | Verified for M2-D; PR #20, merge `2fe059d9`, run 44 |
| ToolRegistry and argument/result boundaries | Verified for M2-A; PR #14, runs 106/56 |
| Mandatory Policy and Approval path | Verified for the M2-B in-memory path; PR #16, runs 129/77 |
| ExecutionAdapter boundary | Verified for M2-C; PR #18, merge `7793a101`, runs 165/111/15 |
| Restricted subprocess controls | Verified for M2-C: minimal env, contained cwd, timeout, combined byte limit, cancellation, process-tree cleanup |
| Kernel / OS isolation | Not provided; every current adapter declares `kernel_isolation=false` |
| Durable approval checkpoint and resume | Partial; M2-D in-memory pending/resolved handoff is implemented, durable store/resume/migration remains M3 |
| Complete cancellation | Partial; Provider-before-call and tool cancellation are implemented, in-flight Provider transport cancellation remains M4 |
| Workspace containment and link defense | Verified for M1 P0 |
| Workspace read/search budgets | Planned; M2-E |
| Checkpoint and Evidence | Partial; production lifecycle handoff is implemented, durable store/Evidence totality remains M3 |
| Side-effect recovery | Verified for M1 P0; ambiguous non-idempotent effects enter manual reconciliation |
| File changes and rollback | Verified for M1 P0; opaque handles, durable journals, expiry, scope, and conflict checks |
| Cross-platform CI | M1 P0, M2-C Adapter, and M2-D Lifecycle Gates cover Linux/macOS/Windows with Python 3.11; the full release matrix remains Planned |
| wheel/sdist, provenance, and integrity | Planned/Blocked |

M2-C final evidence:

- final head: `b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`;
- squash merge: `7793a10152a49fb815aac667906080a4e1a39920`;
- Minimum CI run 165: PASS;
- M1 P0 Gate run 111: PASS on Linux/macOS/Windows;
- M2 ExecutionAdapter Gate run 15: 36/36 per platform, 108/108 total, 0 failures/errors/skips;
- retained failure: Minimum CI run 144, not rerun, deleted, or hidden.

M2-D final evidence:

- implementation final head: `10f5240d8c82df8c41aa609c96a40c3ab7f65242`; merge: `2fe059d900c4e04fab05ca92f421a41d7ff0aa01`;
- Minimum CI 229, M1 P0 173, M2 Adapter 79, and M2 Lifecycle 44 all passed;
- Lifecycle passed 64/64 on each platform, 192/192 total;
- closeout: `docs/roadmap/m2-d-closeout.md`;
- the original blocker and all failed runs remain retained.

Evidence:

- [PRD](docs/product/PRD.md)
- [Threat Model](docs/security/threat-model.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [M1 P0 Cross-platform Report](docs/testing/m1-p0-report.md)
- [M2-A ToolRegistry Closeout](docs/roadmap/m2-a-closeout.md)
- [M2-B Policy/Approval Closeout](docs/roadmap/m2-b-closeout.md)
- [M2-C ExecutionAdapter Closeout](docs/roadmap/m2-c-closeout.md)
- [M2-D Runtime Lifecycle Closeout](docs/roadmap/m2-d-closeout.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [Runtime Lifecycle Contract](docs/contracts/runtime-lifecycle.md)
- [M2-C ExecutionAdapter Test Report](docs/testing/m2-execution-adapter-report.md)
- [M2-D Runtime Lifecycle Test Report](docs/testing/m2-runtime-lifecycle-report.md)
- [Open-source Readiness Plan](docs/roadmap/open-source-readiness-plan.md)

## Current production tool-call path

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider (ASK only)
→ ExecutionAdapter
→ deterministic result normalization
→ content-minimized evidence
```

Current guarantees:

- Registry/schema/Policy/Approval rejection invokes neither Adapter nor handler.
- The default `NoIsolationLocalAdapter` preserves trusted local Python handlers but explicitly provides no timeout, running cancellation, output limit, environment minimization, process cleanup, or isolation.
- `RestrictedSubprocessAdapter` enforces argument arrays, `shell=False`, contained cwd, minimal environment, secret/loader-key stripping, ToolSpec timeout, combined stdout/stderr byte limit, cancellation handoff, and process-tree cleanup.
- Execution events exclude arguments, command, cwd, env, stdin, stdout, stderr, result, private receipt, and exception messages.
- `WorkspaceSandbox.run()` no longer calls `subprocess.run` directly and delegates to its configured Adapter.

## Security boundary

The current implementation is **not an operating-system security sandbox**.

- `NoIsolationLocalAdapter` is only for trusted local tools.
- `RestrictedSubprocessAdapter` is a process-resource boundary, not filesystem, network, syscall, user, or kernel isolation.
- The command classifier is not isolation; wrapped commands may remain classified as `SHELL_SAFE`.
- A restricted child may access resources available to the same host user.
- Process-tree cleanup is best-effort against hostile processes.
- A Python command builder is semi-trusted; the Runtime cannot stop a malicious builder from causing effects before returning a request.
- Workspace containment does not defend against malicious concurrent processes with the same user privileges.
- The Runtime does not promise universal exactly-once behavior.

See the [Threat Model](docs/security/threat-model.md) and [Security Policy](SECURITY.md).

## Current implementation slice: M2-D (implementation complete, pending merge/closeout)

M2-D extends the existing `DeepSeekRuntime`; it must not create a second Agent loop. Its implemented scope includes:

- production state transitions and lifecycle events;
- checkpoint handoff;
- Provider-before-call cancellation and final tool-during-cancel semantics;
- step/token/cost/context/time budgets;
- tool-error continue/terminate policy;
- structured RuntimeResult boundaries for the supported malformed Provider subset;
- an M2-D focused gate.

M2-D excludes Workspace P1, the CLI protocol, Provider streaming/retry, M3 durable store/Evidence work, and release engineering.

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
python scripts/m2_lifecycle_gate.py --output m2-runtime-lifecycle-local.json
```

CI output is shareable evidence; a local verbal claim is not release evidence.

## Documentation

Start at [`docs/INDEX.md`](docs/INDEX.md).

- [Product Architecture](docs/architecture/product-architecture.md)
- [Technical Architecture](docs/architecture/technical-architecture.md)
- [Runtime Core Contracts](docs/contracts/runtime-contracts.md)
- [Policy/Approval Contract](docs/contracts/policy-approval.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [Runtime Lifecycle Contract](docs/contracts/runtime-lifecycle.md)
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
