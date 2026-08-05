# Security Policy

DeepSeek Runtime is a local-first Runtime Kernel under Open-source Alpha hardening. It contains security and recovery primitives, but the current codebase is **not** an operating-system sandbox and is not approved for untrusted tenants or high-value irreversible side effects.

## Supported versions

No stable release is currently supported. Security fixes are developed on `develop`; a version becomes supported only after the Release Gate passes and a release tag is published from `master`.

| Version | Supported |
| --- | --- |
| Tagged Alpha released through the documented gate | Yes, until replaced or explicitly retired |
| `develop` snapshots | Best effort; development only |
| Untagged forks or modified builds | No project support guarantee |

## Security boundary

The authoritative security model is `docs/security/threat-model.md`.

The first Alpha is designed to defend against malformed Provider responses, untrusted model-generated tool requests, hostile workspace content, accidental secret disclosure, corrupted checkpoints, and ambiguous side-effect recovery.

It does not promise:

- kernel-level isolation in `NoIsolationLocalAdapter` or `RestrictedSubprocessAdapter`;
- protection from a malicious concurrent process under the same operating-system account;
- multi-tenant isolation;
- universal exactly-once behavior for external systems;
- safe execution of arbitrary shell, network, browser, or computer-use operations.

## M1 security-control status

M1 implemented and merged the following scoped controls:

- a shared Workspace resolver for read and search paths;
- rejection of traversal, external absolute paths, symlinks, and Windows reparse-point traversal in the tested paths;
- opaque rollback handles backed by a durable ChangeJournal;
- workspace, expiry, scope, post-change-hash, and consumed-handle checks before rollback;
- no automatic replay of persisted running non-idempotent side effects;
- explicit operator reconciliation for ambiguous side effects;
- a permanent Linux/macOS/Windows P0 test manifest.

These controls close the defined M1 P0 scenarios only. They do **not** establish a complete security execution boundary because:

- the production Runtime does not yet force every tool call through one ToolRegistry, Policy, ApprovalProvider, and ExecutionAdapter path;
- owner-only ChangeJournal storage is not encryption;
- multi-file replacement remains best-effort rather than strictly atomic;
- same-account hostile process races remain outside the Alpha guarantee;
- external systems may not support idempotency keys, receipts, or status queries.

The M1 integrated closeout evidence is maintained in `docs/roadmap/m1-closeout.md` and `docs/testing/m1-p0-report.md`.

## Secret and evidence handling

- Store the API key in explicit configuration or `DEEPSEEK_API_KEY`.
- Never place credentials in prompts, command arguments, checkpoints, Git history, public issues, or public CI logs.
- Public evidence must exclude API keys, prompt/response/reasoning content, and recoverable tool content.
- Raw Provider responses and checkpoints are private local artifacts; checkpoint encryption, when enabled, does not make public sharing safe.
- Debug-content modes are dangerous and must be explicitly enabled.
- ChangeJournal files may contain rollback material and must be treated as private local state even when owner-only permissions are applied.

## Reporting a vulnerability

Do not disclose exploit details publicly.

1. Use the repository **Security** tab and choose **Report a vulnerability** to create a private security advisory.
2. Include the affected commit or version, attack preconditions, minimal reproduction, impact, and any mitigation already tested.
3. Do not include real user data or active credentials. Use synthetic fixtures.

If private vulnerability reporting is unavailable, open a public issue containing only a request for private maintainer contact. Do not include the vulnerability details.

## Response targets

These are operational targets, not contractual guarantees:

- acknowledgment: within 5 business days;
- initial severity and scope assessment: within 10 business days;
- status update: at least every 10 business days while actively investigated;
- coordinated disclosure: after a fix or mitigation is available, unless active exploitation requires an earlier warning.

## Severity guidance

- **S0**: workspace-external write/delete, credential disclosure, release-artifact secret leak, or repeated high-value side effect;
- **S1**: core state corruption, incorrect recovery, security-policy bypass, or artifact-integrity failure;
- **S2**: limited functional/security defect without the above impact;
- **S3**: documentation or low-impact hardening issue.

S0 and S1 block every public release.

## Disclosure and credit

The project will coordinate remediation and disclosure with reporters acting in good faith. Public credit is offered when requested and legally permissible; reporters may remain anonymous.