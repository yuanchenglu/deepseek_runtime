# Policy and Approval Contract

> Contract status: M2-B implementation draft  
> Production path: `Provider → ToolRegistry → JSON Schema validation → PermissionPolicy → ApprovalProvider → handler`  
> Release status: **NO RELEASE**

## 1. Scope

This contract defines the minimum production authorization boundary for registered tools. It does not define subprocess isolation, timeout enforcement, output limits, cancellation, budgets, or durable checkpoint storage.

## 2. Default policy

- `READ` defaults to `ALLOW`.
- `WRITE`, `DELETE`, `NETWORK`, `SHELL_SAFE`, `SHELL_DANGEROUS`, and `GIT_MUTATING` default to `DENY`.
- Explicit rules override the default.
- Rules are evaluated in declaration order; the **first matching rule wins**.
- A missing path does not match a path-specific rule. A catch-all rule must use `path_glob="*"`.

This ordering is intentional: specific rules are placed before catch-all rules, and later rules cannot silently override an earlier match.

## 3. Tool execution order

For every valid Provider tool call, Runtime must perform these steps in order:

1. resolve the tool from `ToolRegistry`;
2. parse and validate arguments against the registered JSON Schema;
3. construct a `PermissionRequest` from registered risk and explicit policy selectors;
4. evaluate `PermissionPolicy`;
5. when the decision is `ASK`, invoke `ApprovalProvider`;
6. execute the registered handler only after final authorization;
7. normalize the result or return a structured error;
8. emit content-minimized authorization evidence.

Unknown tools, malformed tool calls, invalid arguments, policy denial, approval denial, approval timeout, unavailable approval, and handler failure must not execute a handler.

## 4. Approval outcomes

`ApprovalProvider` returns exactly one `ApprovalOutcome`:

| Outcome | Meaning |
| --- | --- |
| `approve-once` | Authorizes only the current call |
| `approve-session` | Authorizes the exact same tool/risk/argument request for the current `Runtime.run()` session |
| `deny` | Fails closed with `PERMISSION_DENIED` |
| `timeout` | Fails closed with `APPROVAL_TIMEOUT` |

An absent provider, provider exception, or invalid outcome fails closed with `APPROVAL_UNAVAILABLE`.

Session approval uses an internal canonical argument digest. The digest and raw arguments are not emitted to logs, approval prompts, Runtime evidence, or public errors.

## 5. Content minimization

Approval requests and authorization evidence may contain only:

- registered tool name;
- registered risk;
- `side_effect` flag;
- argument count;
- policy decision;
- approval outcome;
- whether an exact session approval was reused.

They must not contain argument names, values, file content, full paths, commands, URI credentials, API keys, tokens, prompts, responses, or reasoning text.

Policy matching may inspect explicit `path` and `command` selectors in memory. Audit records retain only presence flags and minimized command metadata; raw selectors are removed before the Runtime returns.

## 6. Evidence and checkpoint handoff

Each Runtime step records `authorization_events` in its evidence entry. These records are JSON-compatible and content-minimized so the later Runtime lifecycle/checkpoint slice can copy them into `RecoverableCheckpoint.approvals` without schema translation.

M2-B proves the event contract and Runtime evidence path. Durable checkpoint timing, persistence, resume behavior, and migration remain owned by M2-D/M3 and must not be claimed as complete by this slice.

## 7. Public API boundary

`DeepSeekRuntime.run()` accepts only `ToolRegistry | None`; raw handler mappings remain rejected before Provider execution. All valid Runtime tool calls pass through the policy and approval boundary. Direct handler fixtures are permitted only in tests and are not a supported Runtime execution path.

## 8. Error codes

- `PERMISSION_DENIED`
- `APPROVAL_TIMEOUT`
- `APPROVAL_UNAVAILABLE`

`POLICY_DENIED` is retained only as an in-process enum alias for compatibility and serializes as `PERMISSION_DENIED`.
