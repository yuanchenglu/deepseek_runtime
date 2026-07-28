# M2-C ExecutionAdapter Test Report

> Report status: implementation-branch evidence  
> PR: #18 `feat(execution): establish M2-C ExecutionAdapter boundary`  
> Evidence head: `1e1e538291faa4c4fbb2aa5ee6238c296d9d3ced`  
> Release decision: **NO RELEASE**

## 1. Scope

This report covers the M2-C execution boundary only:

- `ExecutionAdapter` common contract;
- `FakeExecutionAdapter`;
- `NoIsolationLocalAdapter`;
- `RestrictedSubprocessAdapter`;
- Runtime ordering: Registry/schema/Policy/Approval before Adapter;
- WorkspaceSandbox command-path migration;
- minimal child environment;
- cwd containment;
- timeout and cancellation;
- byte output limits;
- process-tree cleanup;
- direct and Runtime error privacy;
- honest non-isolation capability claims.

It does not validate the complete Runtime lifecycle, Provider cancellation, durable checkpoint timing, token/cost/context/time budgets, Workspace read/search budgets, CLI protocol, recovery receipt integration, or kernel isolation.

## 2. Retained failure evidence

### Minimum CI run 144 — FAIL

- Run ID: `30342778701`
- Failing step: full unit suite
- Lint: PASS
- Pyright: PASS
- Root cause: a new Runtime test helper used `arguments or default`, so the explicit invalid fixture `{}` was replaced by valid default arguments. The production schema boundary was not the cause.
- Fix: distinguish `None` from an explicit empty object; keep the schema-failure assertion unchanged.
- The failed run was not rerun, deleted, or hidden.

No M2 ExecutionAdapter Gate failure has been observed on the code-complete evidence head.

## 3. Code-complete CI evidence

Evidence head: `1e1e538291faa4c4fbb2aa5ee6238c296d9d3ced`.

### Minimum CI

- Workflow: Minimum CI
- Run: 159
- Run ID: `30344773142`
- Result: PASS
- Included:
  - critical Ruff rules;
  - Pyright `errorCount=0`;
  - complete unit suite;
  - package import smoke;
  - tracked-secret scan;
  - documentation traceability/link checks.

### M1 P0 regression gate

- Workflow: M1 P0 Gate
- Run: 105
- Run ID: `30344773139`
- Result: PASS on Linux, macOS, and Windows.

M1 P0 controls did not regress while M2-C changed Runtime and WorkspaceSandbox execution paths.

## 4. M2 ExecutionAdapter Gate

- Workflow: M2 ExecutionAdapter Gate
- Run: 9
- Run ID: `30344773173`
- Result: PASS
- Python: 3.11
- Denominator per platform: 36 tests
- Total denominator: 108 tests
- failed/errors/skipped/expected-failures/unexpected-successes: 0/0/0/0/0

| Platform | Result | Tests | Artifact | Digest |
| --- | --- | ---: | --- | --- |
| Linux | PASS | 36/36 | `8682439373` | `sha256:a645fda1a6746f8b1397537f9d01c5bc804a4c3a824d8604d558e4b16250d4cf` |
| macOS | PASS | 36/36 | `8682441110` | `sha256:89afa3434e0e720c0f551db7994e4642697b4842f1a4c329d68faa4c441471a6` |
| Windows | PASS | 36/36 | `8682449665` | `sha256:505e3f48ca6903b46f13c2d7e084491f43a6d0abc11e24e9af6b13ac79a16eb7` |

Each artifact is a JSON record containing platform, Python version, test patterns, explicit denominator, and all unittest result counts.

## 5. Test mapping

| Requirement/Test | Evidence in the focused gate | Current branch conclusion |
| --- | --- | --- |
| `SEC-005` / `TC-SEC-007` | wrapped network commands remain `SHELL_SAFE`; both adapters declare `kernel_isolation=false` | Implemented; no command classifier is described as isolation |
| `SEC-006` / `TC-SEC-005` | host and explicit API-key/secret env keys absent in child; loader injection keys stripped | Implemented |
| `SEC-007` / `TC-SEC-006` | parent starts descendant; timeout cleanup prevents descendant marker on all three OS | Implemented |
| `SEC-008` / `TC-SEC-009` | Fake/NoIsolation/Restricted share interface and have distinguishable capabilities | Implemented |
| `SEC-009` / `TC-SEC-008` | handler/builder/adapter exceptions omit messages; evidence excludes command/env/stdin/stdout/stderr/arguments | Partial; later CLI/M3 output surfaces remain |
| `TOOL-005` / `TC-TOOL-005` | Restricted adapter enforces ToolSpec timeout and returns `TOOL_TIMEOUT` | Implemented for adapters claiming timeout capability |
| `TOOL-005` / `TC-TOOL-006` | combined stdout/stderr retained bytes are bounded; overflow is marked `truncated` in result/evidence | Implemented for adapters claiming byte-limit capability |
| `RUN-006` / `TC-RUN-013` | Runtime cancellation token reaches Adapter; child tree is cleaned | Partial; Provider-before/during cancellation remains M2-D |
| `RUN-003` / `TC-RUN-004` | Runtime still rejects raw handler mappings; Adapter is now mandatory inside supported Runtime call path | Implemented on PR branch; merge required before Verified |

## 6. Additional regression coverage

The 36-test focused denominator also covers:

- Fake adapter never calling handlers;
- Policy/schema rejection invoking no Adapter;
- exact Runtime execution-event ordering;
- invalid Adapter rejected before Provider call;
- external cwd rejected before process start;
- command string rejected in favor of argument tuple;
- environment key/value validation;
- Windows `taskkill` helper using minimal environment;
- builder and local handler exception non-disclosure;
- blocking stdin not bypassing timeout;
- combined retained stdout/stderr never exceeding byte limit;
- WorkspaceSandbox injected Adapter as the only command path;
- WorkspaceSandbox default Restricted adapter and structured timeout;
- malformed Adapter command result rejection.

## 7. Known boundaries

- `NoIsolationLocalAdapter` intentionally does not enforce timeout, running cancellation, output limits, process cleanup, environment minimization, or kernel isolation. Its capability map records all of these as false.
- `RestrictedSubprocessAdapter` is not a kernel sandbox. A child can access resources available to the same host user unless the host environment adds stronger isolation.
- Process-tree cleanup is best-effort against hostile processes, despite passing the supported-platform fixture.
- Restricted handlers are pure command builders; M2-C cannot prevent arbitrary side effects performed inside a malicious builder before it returns.
- `ExecutionOutcome.private_receipt` is not durably checkpointed in M2-C.
- Provider cancellation and complete Runtime lifecycle semantics remain M2-D.

## 8. Exit assessment

The implementation branch has reproducible code-complete evidence for the M2-C Adapter boundary, and M1 P0 regression controls remain green.

M2-C is not closed until:

1. Traceability, PRD status, Threat Model, README, roadmap, and index are synchronized;
2. final exact-content Minimum CI, M1 P0 Gate, and M2 ExecutionAdapter Gate are green;
3. strict review has zero unresolved P0/S0/S1 findings;
4. PR #18 is Ready and merged into `develop`;
5. a docs-only merged-state closeout records the final merge and integrated evidence.

Current repository decision: **NO RELEASE**.
