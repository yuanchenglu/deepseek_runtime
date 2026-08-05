# Architecture Decision Records

ADR records are normative technical decisions for the Open-source Alpha. A superseded ADR remains in the repository and links to its replacement.

| ADR | Decision | Status |
| --- | --- | --- |
| [ADR-001](ADR-001-tool-registry-entrypoint.md) | ToolRegistry is the only production tool entry point | Accepted |
| [ADR-002](ADR-002-checkpoint-evidence-separation.md) | Recoverable Checkpoint and Publishable Evidence are separate models | Accepted |
| [ADR-003](ADR-003-side-effect-recovery.md) | Side effects use explicit recovery policies and uncertain/manual states | Accepted |
| [ADR-004](ADR-004-restricted-subprocess-boundary.md) | Restricted subprocess execution is not OS isolation | Accepted |
| [ADR-005](ADR-005-json-schema-validation.md) | Tool arguments use JSON Schema Draft 2020-12 validation | Accepted |
| [ADR-006](ADR-006-type-checker.md) | Pyright is the repository type checker | Accepted |
| [ADR-007](ADR-007-versioning-and-errors.md) | APIs, schemas, and error codes follow explicit compatibility rules | Accepted |
| [ADR-008](ADR-008-release-branch-flow.md) | Releases flow from develop to master to tag | Accepted |
| [ADR-009](ADR-009-rollback-handle-journal.md) | Rollback authorization uses opaque handles and a durable ChangeJournal | Accepted |
| [ADR-010](ADR-010-coverage-gate-manifests.md) | Coverage and Release Gates use explicit versioned denominators | Accepted |

## Required ADR fields

Each ADR states context, decision, consequences, rejected alternatives, and verification. Material changes require a new ADR that supersedes the prior decision.
