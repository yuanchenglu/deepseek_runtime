# ADR-005: Validate tool arguments with JSON Schema Draft 2020-12

- Status: Accepted
- Date: 2026-07-27
- Requirements: TOOL-001, TOOL-003, TOOL-008

## Context

The current fixed `input: string` convention cannot accurately describe production tools. Hand-written validators create inconsistent behavior and make Provider tool definitions diverge from Runtime enforcement.

## Decision

`ToolSpec.parameters` uses JSON Schema Draft 2020-12. Runtime validation uses the Python `jsonschema` package with `Draft202012Validator` and format checking only for explicitly enabled formats.

Registration validates the schema itself before accepting the tool. Execution validates the complete argument object before policy-sensitive handler execution. Validation failures return a stable `TOOL_ARGUMENT_INVALID` code with bounded, content-safe structural details.

Provider tool definitions are generated from the same registered schema; Provider serialization must not mutate the schema used for local validation.

## Consequences

- `jsonschema` becomes a Runtime dependency when ToolRegistry implementation lands.
- Unsupported custom keywords are rejected or ignored only through an explicit compatibility policy; they cannot silently change enforcement.
- Error reporting must cap path/message sizes and avoid echoing secret argument values.
- Schema snapshots are P2; enforcement behavior is P1.

## Rejected alternatives

- Custom validator: duplicates a mature standard and increases security risk.
- Pydantic-only tool models: useful internally but does not by itself provide the Provider-facing contract required here.
- Trust Provider-side validation: model output and Provider behavior are untrusted.

## Verification

`TC-TOOL-001`, `TC-TOOL-003`, `TC-TOOL-008`, malformed-schema registration tests, and secret-bearing invalid-argument tests.
