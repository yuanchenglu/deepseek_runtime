# M2-C ExecutionAdapter Test Report

> Report status: merged implementation evidence  
> Implementation PR: #18 `feat(execution): establish M2-C ExecutionAdapter boundary`  
> Final head: `b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`  
> Merge commit: `7793a10152a49fb815aac667906080a4e1a39920`  
> Closeout: `docs/roadmap/m2-c-closeout.md`  
> Release decision: **NO RELEASE**

## 1. Scope

This report covers the M2-C execution boundary only:

- `ExecutionAdapter` common contract;
- `FakeExecutionAdapter`;
- `NoIsolationLocalAdapter`;
- `RestrictedSubprocessAdapter`;
- Runtime ordering: Registry/schema/Policy/Approval before Adapter;
- WorkspaceSandbox command-path migration;
- minimal child environment and unsafe loader-key stripping;
- cwd containment;
- timeout and cancellation handoff;
- combined stdout/stderr byte limits;
- process-tree cleanup;
- direct and Runtime error privacy;
- honest non-isolation capability claims.

It does not validate the complete Runtime lifecycle, Provider cancellation, durable checkpoint timing, token/cost/context/time budgets, Workspace read/search budgets, CLI protocol, recovery receipt integration, or kernel isolation.

## 2. Retained failure evidence

### Minimum CI run 144 — FAIL

- Run ID: `30342778701`;
- failing step: full unit suite;
- lint: PASS;
- Pyright: PASS;
- root cause: a new Runtime test helper used `arguments or default`, so the explicit invalid fixture `{}` was replaced by valid default arguments;
- production schema validation was not the cause;
- fix: distinguish `None` from an explicit empty object and preserve the schema-failure assertion;
- the failed run was not rerun, deleted, or hidden.

No M2 ExecutionAdapter Gate failure occurred on the final exact head.

## 3. Final exact-head CI evidence

Evidence head: `b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`.

### 3.1 Minimum CI

- Workflow: Minimum CI;
- Run: 165;
- Run ID: `30345881483`;
- Result: PASS;
- Included:
  - critical Ruff rules;
  - Pyright `errorCount=0`;
  - complete unit suite;
  - package import smoke;
  - tracked-secret scan;
  - documentation traceability/link checks.

### 3.2 M1 P0 regression gate

- Workflow: M1 P0 Gate;
- Run: 111;
- Run ID: `30345881511`;
- Result: PASS on Linux, macOS, and Windows.

M1 P0 controls did not regress while M2-C changed Runtime and WorkspaceSandbox execution paths.

## 4. M2 ExecutionAdapter Gate

- Workflow: M2 ExecutionAdapter Gate;
- Run: 15;
- Run ID: `30345881606`;
- Result: PASS;
- Python: 3.11;
- denominator per platform: 36 tests;
- total denominator: 108 tests;
- failed/errors/skipped/expected-failures/unexpected-successes: 0/0/0/0/0.

| Platform | Result | Tests | Artifact | Digest |
| --- | --- | ---: | --- | --- |
| Linux | PASS | 36/36 | `8682866620` | `sha256:cb57b08c75d0f897ac52c8e3af52be2b0d4baee65dc5dfe43d4c9022315565a8` |
| macOS | PASS | 36/36 | `8682871026` | `sha256:c8bd863f9114ff0a09faafb0525123772b1fec88dd54b4d7da1310cf0703d7eb` |
| Windows | PASS | 36/36 | `8682875863` | `sha256:a7369240153ee8095540e0015561e1ee80da7a9b3c802e4cc102927c61dcb3de` |

Each artifact is a JSON record containing platform, Python version, test patterns, explicit denominator, and all unittest result counts.

## 5. Focused gate denominator

The 36 tests per platform are discovered from:

- `test_execution_adapters.py`;
- `test_execution_adapter_limits.py`;
- `test_execution_adapter_privacy.py`;
- `test_execution_boundary_claims.py`;
- `test_execution_runtime.py`;
- `test_workspace_execution_adapter.py`.

## 6. Test mapping

| Requirement/Test | Final evidence | Merged conclusion |
| --- | --- | --- |
| `SEC-005` / `TC-SEC-007` | wrapped network commands remain classifiable without isolation; all capabilities declare `kernel_isolation=false` | Verified |
| `SEC-006` / `TC-SEC-005` | host/explicit API-key and secret env absent; loader injection keys stripped on three OS | Verified |
| `SEC-007` / `TC-SEC-006` | parent starts descendant; timeout/cancel cleanup prevents descendant marker on three OS | Verified |
| `SEC-008` / `TC-SEC-009` | Fake/NoIsolation/Restricted share the interface and expose distinguishable capabilities | Verified |
| `SEC-009` / `TC-SEC-008` | handler/builder/adapter exceptions omit messages; execution evidence excludes command/env/stdin/stdout/stderr/arguments/results | Verified for the SEC-009 M2 execution surfaces |
| `TOOL-005` / `TC-TOOL-005` | Restricted adapter enforces ToolSpec timeout and returns `TOOL_TIMEOUT` | Verified |
| `TOOL-005` / `TC-TOOL-006` | combined retained bytes are bounded; overflow is marked `truncated` | Verified |
| `RUN-006` / `TC-RUN-013` | Runtime cancellation reaches Adapter and the child tree is cleaned | Partial; Provider-before/during cancellation remains M2-D/M4 |
| `RUN-003` / `TC-RUN-004` | Runtime rejects raw handler mappings and requires Adapter inside the supported production path | Verified |

Broader Provider/CLI/checkpoint/release privacy remains independently tracked under CFG/EVD/OSS and is not implied by the SEC-009 M2 result.

## 7. Additional regression coverage

The focused denominator also covers:

- Fake adapter never calling handlers;
- Policy/schema rejection invoking no Adapter;
- exact Runtime authorization/execution event ordering;
- invalid Adapter rejected before Provider call;
- external cwd rejected before process start;
- command string rejected in favor of an argument tuple;
- environment key/value validation;
- Windows `taskkill` helper using minimal environment;
- builder and local handler exception non-disclosure;
- Popen/cwd/pipe errors becoming structured failures;
- pipe-reader failure not becoming partial success;
- blocking stdin not bypassing timeout;
- combined retained stdout/stderr never exceeding the byte limit;
- WorkspaceSandbox injected Adapter as the only command path;
- WorkspaceSandbox default Restricted adapter and structured timeout;
- malformed Adapter command-result rejection.

## 8. Known boundaries

- `NoIsolationLocalAdapter` intentionally does not enforce timeout, running cancellation, output limits, process cleanup, environment minimization, or kernel isolation. Its capability map records these as false.
- `RestrictedSubprocessAdapter` is not a kernel sandbox. A child can access resources available to the same host user unless the host adds stronger isolation.
- Process-tree cleanup is best-effort against hostile processes, despite passing the supported-platform fixture.
- Restricted handlers are pure command builders; M2-C cannot prevent arbitrary side effects inside a malicious builder before it returns.
- `ExecutionOutcome.private_receipt` is not durably checkpointed in M2-C.
- Provider cancellation and complete Runtime lifecycle semantics remain M2-D/M4.

## 9. Strict review

Resolved findings included:

1. false capability claims on the Fake Adapter;
2. host secret and loader/runtime environment injection;
3. blocking stdin bypassing timeout/cancellation polling;
4. Windows cleanup helper inheriting host environment;
5. handler/builder/Popen/cwd/pipe exceptions escaping or disclosing private text;
6. silent partial-success risk after reader failure;
7. command-classifier language overstating isolation;
8. duplicate direct subprocess production path in `WorkspaceSandbox.run()`.

Final unresolved P0/S0/S1 findings: **0**. PR review threads: **0**.

## 10. Exit assessment

M2-C implementation is merged and its scoped Exit Gate is satisfied:

1. Runtime has one ordered Registry/Policy/Approval/Adapter production chain;
2. the three Adapter contracts are public and capability claims are testable;
3. the Restricted controls pass on Linux, macOS, and Windows;
4. the failed run is retained and explained;
5. final exact-head Minimum CI, M1 regression, and M2 focused gates are green;
6. strict review has zero unresolved P0/S0/S1 findings;
7. PR #18 is squash-merged into `develop`;
8. docs-only PR #19 records the merged state and M2-D handoff.

M2-D, M2-E, M2-F, M2-G, M3–M6 remain release blockers. Current repository decision: **NO RELEASE**.
