# DeepSeek Runtime Alpha Traceability Matrix

> 版本：1.8
> 适用验证基线：`develop@a8a0f3c8d0e417fa8ffe465cec1763063ca9eead`；M2-C implementation PR #18
> 文档修订：以本文件所在 Git commit 为准
> 作用：`Requirement → Milestone → PR → Test → Evidence` 的唯一追踪表。

## 1. 规则

- 本表只列 P0/P1 Requirement；P2 不阻塞首个 Alpha。
- Requirement 的优先级和验收标准以 `docs/product/PRD.md` 为准。
- 未创建的工作只使用语义化 planned slice，禁止预占未来 PR 编号。
- `Expected/Last Evidence` 必须最终包含可复现 CI run、test report、artifact manifest 或批准的 RC 人工证据。
- `Verified` 只能在对应 P0/P1 Test Case 全部自动化通过、代码合入 `develop` 且证据可访问后使用。
- `Implemented` 表示实现和直接测试已存在，但合入或跨切片条件尚未全部完成。
- `Partial` 表示只有合同、局部实现或部分证据，不得解释为 Alpha Requirement 已验收。
- 自动检查必须验证：ID 唯一、Requirement 存在、Test Case 存在、P0/P1 优先级一致、每项至少一个 Test、每项有 Milestone/PR/Evidence 字段。

### M0 已形成的实际证据

- PR #1：`ci: establish and validate M0 minimum gate`；
- Minimum CI run 28：commit `8a52220edead66d9cabae69f56a7fa5d8ca8181f`，`success`；
- PR #2：`docs: close M0 governance baseline`；
- Minimum CI run 30：commit `cf1c70c510fa0633b6c65199a772bf9415e37779`，`success`；
- M0 Closeout：`docs/roadmap/m0-closeout.md`；
- 当前开发策略：PR-first；`develop` 异常直推必须留痕；`master` 是发布分支；
- `OSS-001` 仍为 `Partial`：异常直推意味着仓库级 required-check enforcement 尚未形成完整发布证据。

### M1 已形成的实际证据

- PR #6–#10：核心合同、Workspace P0、rollback P0、side-effect uncertain、永久三平台 P0 Gate；
- PR #13：M1 integrated closeout；
- Minimum CI run 82 (`30327637525`)：`success`；
- M1 P0 Gate run 33 (`30327637544`)：Linux/macOS/Windows 各 140/140，合计 420/420；
- Linux artifact `8676238220`, digest `a3ca74a50e7ab6831fc352a24aaa1f94cdf99013784d515108ae134432c7fb03`；
- macOS artifact `8676237125`, digest `4c9a7461d6a685df3c025297f79d9e799a146efe0c7303d6082a1fbbe1b0658e`；
- Windows artifact `8676241048`, digest `6342d9a008b833848603d6d9c5067d5b512037cebecccee930f9c140184d7341`；
- M1 Closeout：`docs/roadmap/m1-closeout.md`；
- M1 scoped P0 Requirements are `Verified`; M2–M6 remain independently gated.

### M2-A 已形成的实际证据

- PR #14 `feat(runtime): establish ToolRegistry production path`；
- final head `a51d5b297d8233c654cc1569c5fe73b9730c28b6`；merge `b012265c4f51238c97c26c22b76d1e5e043153dc`；
- retained failures：Minimum CI runs 92、98；
- final Minimum CI run 106 (`30330564130`)：`success`；
- final M1 P0 Gate run 56 (`30330564099`)：三平台 `success`；
- strict review unresolved P0/S0/S1 = 0；
- Closeout：`docs/roadmap/m2-a-closeout.md`。

### M2-B 已形成的实际证据

- PR #16 `feat(security): enforce M2-B policy and approval path`；
- final head `7e2913204b89164ba10ec3c43c03ab7bd69435af`；merge `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- retained failures：Minimum CI runs 114、122、127；
- final Minimum CI run 129 (`30340272861`)：`success`；
- final M1 P0 Gate run 77 (`30340272870`)：三平台 `success`；
- strict review unresolved P0/S0/S1 = 0；
- Closeout：`docs/roadmap/m2-b-closeout.md`。

### M2-C 当前实施证据

- implementation PR：#18 `feat(execution): establish M2-C ExecutionAdapter boundary`；
- base：`develop@a8a0f3c8d0e417fa8ffe465cec1763063ca9eead`；
- retained failure：Minimum CI run 144 (`30342778701`)；新增 schema-negative test helper 将显式 `{}` 错误替换为默认参数，导致 unit failure；生产 schema 边界无缺陷；
- 修复方式：区分 `None` 与显式空对象，保留原断言；失败 run 未 rerun、删除或隐藏；
- code-complete evidence head：`1e1e538291faa4c4fbb2aa5ee6238c296d9d3ced`；
- Minimum CI run 159 (`30344773142`)：`success`；
- M1 P0 Gate run 105 (`30344773139`)：Linux/macOS/Windows `success`；
- M2 ExecutionAdapter Gate run 9 (`30344773173`)：Linux/macOS/Windows 各 36/36，总计 108/108，0 failures/errors/skipped；
- Linux artifact `8682439373`, digest `a645fda1a6746f8b1397537f9d01c5bc804a4c3a824d8604d558e4b16250d4cf`；
- macOS artifact `8682441110`, digest `89afa3434e0e720c0f551db7994e4642697b4842f1a4c329d68faa4c441471a6`；
- Windows artifact `8682449665`, digest `505e3f48ca6903b46f13c2d7e084491f43a6d0abc11e24e9af6b13ac79a16eb7`；
- report：`docs/testing/m2-execution-adapter-report.md`；
- 当前状态：代码、专项三平台证据和核心合同已实现；等待最终文档、最终精确内容 Gate、strict review、Ready 与 merge；
- 发布结论：**NO RELEASE**。

## 2. 配置与版本

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CFG-001 | P1 | M4/M5 | Release | M4 Config PR / M5 Release PR | TC-CFG-001 | 3 Python × 3 OS CI matrix | Partial | M1/M2 专项仅覆盖 Python 3.11；完整版本矩阵未建立 |
| CFG-002 | P1 | M4/M5 | Release | M4 Config PR / M5 Release PR | TC-CFG-002 | version consistency CI + release manifest | Blocked | 多版本源 |
| CFG-003 | P1 | M4 | Security | M4 Config PR | TC-CFG-003 | secret marker subprocess logs | Partial | Adapter 子进程面已覆盖；CLI/Provider/构件输出面未完全覆盖 |
| CFG-004 | P1 | M4 | Runtime | M4 Config PR | TC-CFG-004 | config validation unit CI | Planned | 配置 schema 未冻结 |
| CFG-005 | P1 | M4 | Security | M4 Config PR | TC-CFG-005 | isolated env unit CI | Blocked | RuntimeSettings 仍存在 `env or os.environ` 语义 |

## 3. Provider

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PROV-001 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-001 | mock transport CI | Implemented | 需接入最终 lifecycle/RuntimeResult |
| PROV-002 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-002 | property/fuzz artifact | Blocked | arbitrary root 未规范化 |
| PROV-003 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-003/004 | malformed fixture manifest | Planned | schema 未定义 |
| PROV-004 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-005 | error-code fixture manifest | Partial | 分类不完整 |
| PROV-005 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-006/007 | fake-clock retry CI | Planned | retry contract 未实现 |
| PROV-006 | P1 | M4 | Provider | M4 Provider PR | TC-PROV-008 | response-size CI | Planned | 无 body limit |
| PROV-007 | P1 | M1/M4 | Provider | PR #6 / M4 Provider PR | TC-PROV-009/010 | canonical identity snapshot | Partial | Evidence contract 已冻结；Provider identity envelope 仍不完整 |
| PROV-008 | P1 | M4 | Provider | M4 Streaming PR | TC-PROV-011/012/013 | byte-split SSE CI | Blocked | 非真正增量 parser |
| PROV-009 | P1 | M4 | Provider | M4 Streaming PR | TC-PROV-014 | stream consumer integration CI | Blocked | 无 iterator/callback 合同 |

## 4. Runtime

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUN-001 | P1 | M2 | Runtime | M2-D PR | TC-RUN-001 | fake-provider integration CI | Implemented | 需接入统一 RuntimeResult/lifecycle |
| RUN-002 | P1 | M2 | Runtime | M2-D PR | TC-RUN-002/003 | multi-round integration CI | Partial | 生命周期未统一 |
| RUN-003 | P1 | M2 | Runtime | PR #14/#18 | TC-RUN-004 | run 106 Registry-only；run 9 Adapter ordering/bypass negatives | Verified | PR #18 merge 后需 closeout 确认 Adapter boundary |
| RUN-004 | P1 | M1/M2 | Runtime | PR #6 / M2-D PR | TC-RUN-005 | transition manifest CI | Partial | state/transition/checkpoint 合同已冻结；生产 Runtime 尚未强制全部转换 |
| RUN-005 | P1 | M2 | Runtime | M2-D PR | TC-RUN-006 | budget integration CI | Partial | 仅 step 行为 |
| RUN-006 | P1 | M2/M4 | Runtime | PR #18 / M2-D PR | TC-RUN-012/013、TC-PROV-015 | run 9 Adapter cancellation + cleanup PASS | Partial | Tool-during-cancel handoff 已实现；Provider 前/请求中 cancellation 与 durable lifecycle 属 M2-D/M4 |
| RUN-007 | P1 | M2 | Runtime | M2-D PR | TC-RUN-007 | budget matrix CI | Planned | token/cost/context/time 未接入 |
| RUN-008 | P1 | M2 | Runtime | M2-D PR | TC-RUN-008 | tool-error policy CI | Partial | RecoveryPolicy 已实现；Runtime 级继续/终止策略未完成 |
| RUN-009 | P1 | M2 | Runtime | PR #14/#18 | TC-RUN-009、TC-TOOL-005/006 | run 106 normalization；run 9 timeout/output PASS | Verified | NoIsolation capability 明确不提供 limit；bounded path 由 Restricted Adapter 保证 |
| RUN-010 | P1 | M2/M4 | Runtime | PR #14 / M2-D/M4 Provider PR | TC-RUN-010 | run 98 retained；run 106 malformed subset PASS | Partial | arbitrary root、choices/message 全矩阵仍属后续 Provider/Runtime PR |

## 5. Tool Contract

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TOOL-001 | P1 | M1/M2 | Runtime | PR #6/#14 | TC-TOOL-001 | run 106 | Verified | 无 M2-A blocker |
| TOOL-002 | P1 | M2 | Runtime | PR #14 | TC-TOOL-002 | run 106 | Verified | 无 M2-A blocker |
| TOOL-003 | P1 | M2 | Runtime | PR #6/#14 | TC-TOOL-003 | run 106 | Verified | 无 M2-A blocker |
| TOOL-004 | P1 | M1/M2 | Security | PR #6/#14 | TC-TOOL-004 | run 106 | Verified | 无 M2-A blocker |
| TOOL-005 | P1 | M2 | Runtime | PR #18 | TC-TOOL-005/006 | M2 Gate run 9；timeout/output byte limit PASS × 3 OS | Implemented | 等待 PR #18 final Gate/merge；NoIsolation 显式声明不提供 limit |
| TOOL-006 | P1 | M1/M2 | Recovery | PR #6/#9/#14 / M2-D PR | TC-TOOL-004/007 | registration/recovery evidence | Partial | receipt/idempotency/retry 与 Adapter private receipt 尚未接入 lifecycle |
| TOOL-007 | P1 | M2 | Runtime | PR #9/#14 | TC-RUN-011 | run 106 | Verified | 无 M2-A blocker |

## 6. Workspace

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WS-001 | P0 | M1 | Security | PR #7/#13/#18 | TC-WS-001 | run 33；M1 run 105 regression PASS | Verified | 无 M1 blocker |
| WS-002 | P0 | M1 | Security | PR #7/#13/#18 | TC-WS-002/003 | run 33；M1 run 105 regression PASS | Verified | 同账号恶意并发进程不在承诺范围 |
| WS-003 | P1 | M2 | Runtime | PR #7 / M2-E PR | TC-WS-004 | UTF-8 boundary CI | Partial | containment 已统一；read byte-limit/UTF-8 截断语义未完成 |
| WS-004 | P1 | M2 | Runtime | M2-E PR | TC-WS-005 | large-workspace budget CI | Planned | read/search file/byte/time budget 未实现 |
| WS-005 | P1 | M2 | Runtime | PR #7 / M2-E PR | TC-WS-006 | IO fixture CI | Partial | no-follow traversal 已实现；错误结构仍未统一 |

## 7. Policy、Approval 与 Execution

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-001 | P1 | M2 | Security | PR #16/#17 | TC-SEC-001 | run 129；merged `f8a5799a` | Verified | 无 M2-B blocker |
| SEC-002 | P1 | M2 | Security | PR #16/#17 | TC-SEC-002 | run 129；merged `f8a5799a` | Verified | 无 M2-B blocker |
| SEC-003 | P1 | M2 | Security | PR #16 / M2-D/M3 Recovery PR | TC-SEC-003 | run 129 | Partial | durable approval checkpoint timing、resume、migration 属 M2-D/M3 |
| SEC-004 | P1 | M2 | Security | PR #16/#17/#18 | TC-SEC-004 | run 129；M2 Gate run 9 Adapter ordering/bypass PASS | Verified | PR #18 merge 后记录 integrated closeout |
| SEC-005 | P1 | M0/M2 | Security | PR #18 | TC-SEC-007 | run 9 wrapped-command negative + capability snapshot × 3 OS | Implemented | 等待 final Gate/merge；CLI help 最终文案仍需 M2-F 复核 |
| SEC-006 | P1 | M2 | Security | PR #18 | TC-SEC-005 | run 9 minimal env/API-key/loader-key negatives × 3 OS | Implemented | 等待 final Gate/merge |
| SEC-007 | P1 | M2 | Security | PR #18 | TC-SEC-006 | run 9 descendant cleanup × 3 OS | Implemented | best-effort 对 hostile process 的非保证必须保留 |
| SEC-008 | P1 | M2 | Runtime | PR #18 | TC-SEC-009 | run 9 Fake/NoIsolation/Restricted capability contract × 3 OS | Implemented | 等待 final Gate/merge |
| SEC-009 | P1 | M2 | Security | PR #16/#18 / M3 Evidence PR | TC-SEC-008 | run 129 approval privacy；run 9 Adapter env/error/evidence privacy | Partial | M2 execution surfaces 已覆盖；CLI、Provider、checkpoint、构件全输出面仍属后续 |

## 8. ChangeManager

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHG-001 | P0 | M1 | Security | PR #8/#13 | TC-CHG-001 | run 33 | Verified | 无 M1 blocker |
| CHG-002 | P0 | M1 | Security | PR #8/#13 | TC-CHG-002 | run 33 | Verified | 无 M1 blocker |
| CHG-003 | P1 | M3 | Runtime | M3 Change PR | TC-CHG-003 | duplicate-path unit CI | Planned | 未拒绝重复路径 |
| CHG-004 | P1 | M3 | Runtime | M3 Change PR | TC-CHG-004 | concurrent fixture CI | Planned | 无 lock/完整 TOCTOU 控制 |
| CHG-005 | P1 | M3 | Runtime | PR #8 / M3 Change PR | TC-CHG-005 | stale rollback CI | Implemented | M3 并发/恢复矩阵未完成 |
| CHG-006 | P1 | M3 | Runtime | M3 Change PR | TC-CHG-006 | platform metadata CI | Planned | mode/metadata 策略未定义 |
| CHG-007 | P1 | M3 | Runtime | PR #8 / M3 Change PR | TC-CHG-007/008 | fault-injection artifact | Partial | parent fsync/补偿与 crash-during-restore 不完整 |
| CHG-008 | P1 | M3 | Security | PR #8/#13/#14 / M3 Evidence PR | TC-CHG-009 | content-free audit CI | Partial | 统一 audit schema 未冻结 |
| CHG-009 | P1 | M3 | Runtime | M3 Change PR | TC-CHG-010 | multi-file fault report | Blocked | best-effort、锁与补偿矩阵未完成 |
| CHG-010 | P1 | M1/M3 | Recovery | PR #6/#8/#13 / M3 Recovery PR | TC-CHG-011 | restart/expiry/scope CI | Partial | 加密/锁/完整 lifecycle 属 M3 |

## 9. Session 与恢复

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SES-001 | P1 | M1/M3 | Recovery | PR #6 / M3 Recovery PR | TC-SES-001 | schema/API roundtrip CI | Partial | SessionStore 未完成 checkpoint/evidence 分离 |
| SES-002 | P1 | M1/M3 | Recovery | PR #6 / M3 Recovery PR | TC-SES-002 | continuation fixture CI | Partial | 完整 reasoning/provider continuation 恢复未完成 |
| SES-003 | P1 | M3 | Security | M3 Recovery PR | TC-SES-003 | encrypted disk inspection | Planned | encryption injection 缺失 |
| SES-004 | P1 | M3 | Recovery | M3 Recovery PR | TC-SES-004/011 | crash/corrupt/concurrent CI | Partial | lock/corruption 语义不足 |
| SES-005 | P1 | M3 | Recovery | PR #6/#9 / M3 Recovery PR | TC-SES-005 | migration fixture CI | Partial | RecoverableCheckpoint migration 未完成 |
| SES-006 | P1 | M3 | Recovery | M3 Recovery PR | TC-SES-006 | resume integration CI | Implemented | 需纳入最终 Runtime 状态机 |
| SES-007 | P0 | M1 | Recovery | PR #9/#13 | TC-SES-007 | run 33 | Verified | 完整 receipt/idempotency matrix 属 M3 |
| SES-008 | P1 | M3 | Runtime | PR #9 / M3 Recovery PR | TC-SES-008 | missing-handler recovery CI | Implemented | 最终 Runtime 集成仍属 M2/M3 |
| SES-009 | P1 | M3 | Recovery | PR #9 / M3 Recovery PR | TC-SES-009 | fake-clock retry CI | Partial | backoff、time budget 与 fake-clock matrix 未完成 |
| SES-010 | P1 | M3 | Recovery | PR #6/#9/#18 / M3 Recovery PR | TC-SES-010 | approval event roundtrip；Adapter private receipt pending | Partial | approvals/budgets/receipt/checkpoint 完整 roundtrip 未完成 |

## 10. Evidence 与隐私

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EVD-001 | P1 | M3 | Security | PR #16/#18 / M3 Evidence PR | TC-EVD-001 | approval/Adapter key-marker subsets | Partial | 全输出面未覆盖 |
| EVD-002 | P1 | M3 | Security | PR #14/#16/#18 / M3 Evidence PR | TC-EVD-001 | content-free execution/authorization events | Implemented | 需纳入 M3 全矩阵 |
| EVD-003 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | TC-EVD-002 | property/fuzz artifact | Partial | total-function 实现未完成 |
| EVD-004 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | TC-EVD-003 | canonical snapshot CI | Partial | canonical identity 仍不完整 |
| EVD-005 | P1 | M3 | Security | M3 Evidence PR | TC-EVD-004 | low-entropy threat test | Planned | 裸 hash 风险 |
| EVD-006 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | TC-EVD-006 | schema compatibility CI | Partial | 生产 migration/compat gate 属 M3 |
| EVD-007 | P1 | M3 | Security | PR #10/#14 / M3 Evidence PR | TC-EVD-007 | CLI/API debug gate CI | Partial | 危险开关语义不完整 |
| EVD-008 | P1 | M3 | Security | PR #18 / M3 Evidence PR | TC-EVD-005 | Adapter exception message negatives | Partial | Provider/CLI/checkpoint exception 全面覆盖未完成 |

## 11. Observability 与预算

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBS-001 | P1 | M3 | Runtime | PR #18 / M3 Observability PR | TC-OBS-007 | Adapter duration metadata | Partial | 完整 lifecycle latency 未接入 |
| OBS-002 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-001 | usage/cost fixture CI | Partial | 分类语义混合 |
| OBS-003 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-002 | missing-field CI | Blocked | unknown 被转为 0 |
| OBS-004 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-003 | prompt-token fixture CI | Blocked | 输入成本漏算 |
| OBS-005 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-004 | validation CI | Planned | 非法数值未拒绝 |
| OBS-006 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-005 | partial-data CI | Blocked | 分母包含未知值 |
| OBS-007 | P1 | M2/M3 | Runtime | M2-D / M3 Observability PR | TC-OBS-006 | budget-stop integration CI | Planned | 预算未驱动 Runtime |

## 12. CLI 与文档

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLI-001 | P1 | M2/M4 | Runtime | PR #10 / M2-F PR | TC-CLI-001 | subprocess CI | Implemented | 需保持无 Key |
| CLI-002 | P1 | M2/M4 | Runtime | M2-F PR | TC-CLI-002 | golden/subprocess CI | Blocked | 默认仅摘要 |
| CLI-003 | P1 | M2/M4 | Runtime | M2-F PR | TC-CLI-003 | stdout/report separation CI | Planned | 独立 report 缺失 |
| CLI-004 | P1 | M2/M4 | Security | PR #18 / M2-F PR | TC-CLI-004 | Adapter warning docs；help/golden pending | Partial | CLI help/unsafe adapter UX 待 M2-F |
| CLI-005 | P1 | M2/M4 | Runtime | M2-F PR | TC-CLI-005 | exit-code matrix CI | Partial | 具体映射未实现 |
| CLI-006 | P1 | M2/M4 | Runtime | M2-F PR | TC-CLI-006 | workspace error CI | Partial | 错误 UX 不统一 |
| DOC-001 | P1 | M4 | Release | PR #10 / M4 Docs PR | TC-DOC-001 | doctor semantics CI | Partial | 诊断/在线可运行混淆 |

## 13. 开源与发布

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OSS-001 | P1 | M0/M5 | Release | PR #1/#2 / M5 Release PR | TC-OSS-001 | required PR checks | Partial | required-check enforcement 仍需 M5 |
| OSS-002 | P1 | M5 | Release | M5 Release PR | TC-OSS-001 | 3 OS × 3 Python matrix | Planned | 专项矩阵不等于完整 release matrix |
| OSS-003 | P1 | M0/M5 | Release | PR #1/#2/#18 / M5 Release PR | TC-OSS-002 | Ruff + Pyright + tests；coverage pending | Partial | coverage 和完整矩阵未建立 |
| OSS-004 | P1 | M0/M5 | Release | PR #6/#10/#13/#18 / M5 Release PR | TC-OSS-002 | versioned gate + JSON artifacts | Partial | coverage 配置/报告未实现 |
| OSS-005 | P1 | M0/M5 | Security | PR #1/#2/#18 / M5 Release PR | TC-OSS-003 | tracked scan + child-env negatives | Partial | artifact scan/negative fixture 未完成 |
| OSS-006 | P1 | M5 | Release | M5 Packaging PR | TC-OSS-003/005 | artifact file manifest | Blocked | denylist 打包工作树 |
| OSS-007 | P1 | M5 | Release | M5 Packaging PR | TC-OSS-004 | recomputed digest + tamper failure | Blocked | 只检查长度 |
| OSS-008 | P1 | M5 | Release | M5 Packaging PR | TC-CFG-006、TC-OSS-006 | clean-venv logs | Planned | wheel/sdist gate 缺失 |
| OSS-009 | P1 | M0/M5 | Maintainer | PR #2 / M5 Governance PR | TC-OSS-009 | governance files + docs/link CI | Partial | M5 release governance 复核未完成 |
| OSS-010 | P1 | M0/M5 | Security | PR #2 / M5 Governance PR | TC-OSS-010 | SECURITY gate + approved review | Partial | 私密报告能力与 release review 待验证 |
| OSS-011 | P1 | M0/M5/M6 | Maintainer | PR #2/#13/#14/#16/#17/#18 / M5 Claim Audit PR | TC-OSS-007 | README/Threat/contract synchronization | Partial | 完整逐项自动 claim audit 未实现 |

## 14. Release-level Evidence

| Evidence | Test/Gate | Required at M6 |
| --- | --- | --- |
| P0 repetition report | TC-WS-001–003、TC-CHG-001/002/011、TC-SES-007 | 是 |
| Full CI matrix | TC-OSS-001/002 | 是 |
| Coverage manifests | OSS-004 | 是 |
| Provider fixture manifest | TC-PROV-002–015 | 是 |
| Recovery fault matrix | TC-SES-006–011、TC-TOOL-007 | 是 |
| M2 ExecutionAdapter matrix | TC-SEC-005–009、TC-TOOL-005/006、TC-RUN-013 | 是，作为 M2 组成证据 |
| Artifact file manifest | TC-OSS-003/005 | 是 |
| Digest/tamper report | TC-OSS-004 | 是 |
| Clean-install logs | TC-CFG-006、TC-OSS-006 | 是 |
| Live DeepSeek smoke | TC-LIVE-001 | 是 |
| Governance/security review | TC-OSS-009/010 | 是 |
| README claim audit | TC-OSS-007 | 是 |
| Final RC test report | TC-OSS-008 | 是 |

## 15. 当前结论

M0、M1、M2-A、M2-B 已关闭。

M2-C 已在 PR #18 实现 Adapter 合同、三种 Adapter、Runtime 强制接入、WorkspaceSandbox 迁移、最小环境、cwd containment、timeout、byte output、cancellation handoff、process-tree cleanup 与 execution evidence。代码完成态 Minimum CI run 159、M1 P0 Gate run 105 和 M2 ExecutionAdapter Gate run 9 全绿，专项分母为三平台各 36/36。

PR #18 尚未完成最终文档精确内容 Gate、strict review、Ready 和 merge，因此 M2-C 当前是 **IN PROGRESS**，相关 Requirement 不得提前全部标记为 `Verified`。

M2-D lifecycle/budget/cancellation、M2-E Workspace P1、M2-F CLI contract 与 M2-G integrated closeout 仍为阻断项。

当前发布结论：**NO RELEASE**。
