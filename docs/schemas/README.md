# Versioned JSON Schemas

These files are normative wire/storage contracts for DeepSeek Runtime.

| Schema | Visibility | Purpose |
| --- | --- | --- |
| `error-v1.schema.json` | Public-safe | Stable machine-readable Runtime error |
| `recoverable-checkpoint-v1.schema.json` | Private | Complete state required for recovery |
| `publishable-evidence-v1.schema.json` | Public-safe | Shareable structural evidence without recoverable content |
| `change-journal-entry-v1.schema.json` | Private | Durable rollback authorization and recovery record |

## Rules

- Draft: JSON Schema 2020-12.
- `schema_version` is independent from the Python package version.
- Unknown future major/incompatible versions fail structurally; they are not interpreted heuristically.
- A schema change requires matching Python serializer/deserializer tests.
- Public-safe schemas must not acquire prompt, response, reasoning, argument, result, secret, original-file content or other recoverable plaintext fields.
- Private schemas must never be described or exported as public evidence.
- `$id` values identify contract documents; they are not live network dependencies and validation must work offline.

## Change process

1. Update or supersede the relevant ADR.
2. Add a new schema version for incompatible changes.
3. Add migration and future-version fixtures.
4. Update the Runtime transition manifest where lifecycle semantics change.
5. Update Traceability and evidence before marking any Requirement `Verified`.
