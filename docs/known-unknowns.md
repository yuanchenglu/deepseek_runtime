# Known Unknowns

These items are intentionally explicit for `0.1.1a1`. M1 closed specific reproducible P0 defects; it did not remove the following product and security boundaries.

| Area | Current status | Next check |
| --- | --- | --- |
| Full DeepSeek V4 physical-trait coverage | Not claimed. Only verified or modeled traits are documented. | Expand the matrix after additional protocol and benchmark evidence. |
| Real billing accuracy | Not claimed. Cost is estimated from a pricing snapshot or explicit evidence. | Compare against provider billing exports when available. |
| Hosted multi-tenant safety | Not included. Runtime is local-first. | Do not claim hosted safety before an explicit isolation architecture and threat-model revision. |
| Operating-system isolation | Not claimed. Workspace containment and subprocess restrictions are Runtime controls, not kernel or container isolation. | Add platform isolation guidance only after a separately verified implementation exists. |
| Malicious same-account concurrent process | Not defended. A process with equivalent host permissions may race or replace paths after checks. | Keep this outside the Alpha guarantee unless handle-based platform controls and adversarial evidence are added. |
| Durable ChangeJournal confidentiality | Owner-only local storage is implemented, but owner-only is not encryption. | Add optional encryption-key injection, locking, ACL evidence, and disk-inspection tests in M3. |
| Strict multi-file atomicity | Not claimed. ChangeManager is best-effort transactional replacement with conflict checks and compensation. | Add workspace/file locking, staging, fsync, fault injection, and crash-during-restore evidence in M3. |
| Universal external exactly-once | Not claimed. A persisted running non-idempotent side effect becomes uncertain and requires reconciliation. | Add receipt verification interfaces, idempotency-key integration, and external-system fixtures in M3. |
| Complete Tool execution closure | Not complete. M1 froze ToolSpec/RecoveryPolicy contracts, but the production Runtime can still bypass a single ToolRegistry/Policy/Approval/ExecutionAdapter path. | Close the M2 no-bypass tests before describing tool execution as enforced. |
| Checkpoint privacy and recovery completeness | Partial. Contracts are separated, but the legacy production SessionStore is not yet the final RecoverableCheckpoint implementation. | Complete storage separation, corruption handling, locking, migration, and optional encryption in M3. |
| Long-running stream stability | Partially modeled. The stream parser records event structure, not full production stress behavior. | Add byte-split, multiline, malformed-event, cancellation, and live soak tests in M4. |
| Prompt privacy under user code | Runtime safe outputs redact by default, but integrations can still log raw final text, messages, or debug content. | Add integration lint checks, explicit debug gates, and logging adapters. |
| Tool argument hallucination | M1 provides ToolSpec and JSON Schema contracts, but production Runtime enforcement remains incomplete until M2. Business validation also belongs to each tool handler. | Add Registry no-bypass tests and production tool validation examples. |
| Model naming drift | Official docs can change. | Keep live smoke and README model references synchronized with official docs before each tag. |

The repository remains **NO RELEASE**.