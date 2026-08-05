# ADR-002: Separate Recoverable Checkpoint from Publishable Evidence

- Status: Accepted
- Date: 2026-07-27
- Requirements: SES-001–SES-005, EVD-001–EVD-008

## Context

Recovery requires complete conversation, continuation, arguments, results, approvals, receipts, and budgets. Public diagnostics require the opposite: content-minimized, redacted, shareable structure. One schema cannot satisfy both purposes without either breaking recovery or leaking recoverable content.

## Decision

Define two independent versioned models:

### `RecoverableCheckpoint`

Contains the minimum complete state needed to continue execution correctly. It is local/private, may be encrypted at rest, and is never treated as publishable evidence.

### `PublishableEvidence`

Contains structural identity, lengths, usage, cost, timings, redacted metadata, state transitions, and machine-readable errors. It contains no recoverable prompt, response, reasoning, argument, result, or secret plaintext.

The models have separate serializers, schema versions, migration rules, storage paths, retention rules, and tests. Evidence generation must be a total function over supported JSON-compatible input and must not mutate the checkpoint.

## Consequences

- Existing mixed session/evidence serialization must be replaced.
- Debug content, when explicitly enabled, is a third local-dangerous output mode and is never silently promoted to public evidence.
- Checkpoint encryption is defense at rest, not authorization to publish the file.
- Unsupported future checkpoint versions fail without overwriting original data.

## Rejected alternatives

- Redact the checkpoint before storage: destroys continuation semantics.
- Publish a hash of every field: low-entropy content can remain guessable and hashes do not provide recoverability.
- Use one schema with optional secret fields: too easy for public exporters to include the wrong fields.

## Verification

`TC-SES-001`–`TC-SES-005`, `TC-EVD-001`–`TC-EVD-007`, encrypted/plaintext disk inspection, and schema compatibility fixtures.
