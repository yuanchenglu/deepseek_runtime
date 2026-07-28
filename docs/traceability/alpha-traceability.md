# DeepSeek Runtime Alpha Traceability Matrix

> 版本：1.3
> 适用验证基线：PR #13 head `81643dca`
> 文档修订：以本文件所在 Git commit 为准
> 作用：`Requirement → Milestone → PR → Test → Evidence` 的唯一追踪表。

## 1. 规则

- 本表只列 P0/P1 Requirement；P2 不阻塞首个 Alpha。
- Requirement 的优先级和验收标准以 `docs/product/PRD.md` 为准。
- `Planned PR` 是执行切片；实际 PR 产生后必须补充真实编号。
- `Expected Evidence` 必须最终替换或补充为可复现 CI run、test report、artifact manifest 或批准的 RC 人工证据。
- `Verified` 只能在对应 P0/P1 Test Case 全部自动化通过且证据可访问后使用。
- `Implemented` 表示代码已存在，但集成门禁或后续里程碑条件尚未全部完成。
- `Partial` 表示只有合同、局部实现或部分证据，不得解释为 Alpha Requirement 已验收。
- 自动检查必须验证：ID 唯一、Requirement 存在、Test Case 存在、P0/P1 优先级一致、每项至少一个 Test、每项有 Milestone/PR/Evidence 字段。

### M0 已形成的实际证据

- PR #1：`ci: establish and validate M0 minimum gate`；
- `Minimum CI` run 28：commit `8a52220edead66d9cabae69f56a7fa5d8ca8181f`，结论 `success`；
- PR #2：`docs: close M0 governance baseline`；
- `Minimum CI` run 30：commit `cf1c70c510fa0633b6c65199a772bf9415e37779`，结论 `success`；
- M0 Closeout：`docs/roadmap/m0-closeout.md`；
- 当前开发策略：PR-first；`develop` 允许异常直推，但必须记录问题原因和技术债务；`master` 是发布分支；
- `OSS-001` 仍为 `Partial`：异常直推意味着仓库级 required-check enforcement 不能被视为已验证发布能力。

### M1 已形成的实际证据

- PR #6：核心合同、schemas、transition manifest、ADR 与合同测试，已合入 `develop`；
- PR #7：Workspace containment 与 symlink/reparse-point 防护，已合入 `develop`；
- PR #8：opaque rollback handle、durable ChangeJournal 与 Windows 修复，已合入 `develop`；
- PR #9：side-effect-uncertain、RecoveryPolicy 与人工 reconciliation，已合入 `develop`；
- PR #10：永久三平台 P0 Gate、版本化 runner 与 `docs/testing/m1-p0-report.md`，已合入 `develop`；
- PR #13：M1 integrated closeout、文档/治理同步与无效 workflow concurrency 修复；
- Minimum CI run 82 (`30327637525`)：结论 `success`；
- M1 P0 Gate run 33 (`30327637544`)：Linux/macOS/Windows 各 140/140，合计 420/420；
- Linux artifact `8676238220`, digest `a3ca74a50e7ab6831fc352a24aaa1f94cdf99013784d515108ae134432c7fb03`；
- macOS artifact `8676237125`, digest `4c9a7461d6a685df3c025297f79d9e799a146efe0c7303d6082a1fbbe1b0658e`；
- Windows artifact `8676241048`, digest `6342d9a008b833848603d6d9c5067d5b512037cebecccee930f9c140184d7341`；
- M1 Closeout：`docs/roadmap/m1-closeout.md`；
- M1 scoped P0 Requirements are `Verified`; M2–M6 Requirements remain independently gated.

## 2. 配置与版本

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CFG-001 | P1 | M4/M5 | Release | PR-17/18 | TC-CFG-001 | 3 Python × 3 OS CI matrix | Partial | M1 仅有 P0 Python 3.11 三 OS 矩阵；完整版本矩阵未建立 |
| CFG-002 | P1 | M4/M5 | Release | PR-17/18 | TC-CFG-002 | version consistency CI + release manifest | Blocked | 多版本源 |
| CFG-003 | P1 | M4 | Security | PR-17 | TC-CFG-003 | secret marker subprocess logs | Partial | 输出面未完全覆盖 |
| CFG-004 | P1 | M4 | Runtime | PR-17 | TC-CFG-004 | config validation unit CI | Planned | 配置 schema 未冻结 |
| CFG-005 | P1 | M4 | Runtime | PR-17 | TC-CFG-005 | isolated env unit CI | Blocked | `env or os.environ` |

## 3. Provider

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PROV-001 | P1 | M4 | Provider | PR-15 | TC-PROV-001 | mock transport CI | Implemented | 需动态复跑并接入最终 RuntimeResult |
| PROV-002 | P1 | M4 | Provider | PR-15 | TC-PROV-002 | property/fuzz artifact | Blocked | arbitrary root 未规范化 |
| PROV-003 | P1 | M4 | Provider | PR-15 | TC-PROV-003/004 | malformed fixture manifest | Planned | schema 未定义 |
| PROV-004 | P1 | M4 | Provider | PR-15 | TC-PROV-005 | error-code fixture manifest | Partial | 分类不完整 |
| PROV-005 | P1 | M4 | Provider | PR-15 | TC-PROV-006/007 | fake-clock retry CI | Planned | retry contract 未实现 |
| PROV-006 | P1 | M4 | Provider | PR-15 | TC-PROV-008 | response-size CI | Planned | 无 body limit |
| PROV-007 | P1 | M1/M4 | Provider | PR #6 / PR-15 | TC-PROV-009/010 | canonical identity snapshot | Partial | Evidence contract 已冻结；Provider identity envelope 仍不完整 |
| PROV-008 | P1 | M4 | Provider | PR-16 | TC-PROV-011/012/013 | byte-split SSE CI | Blocked | 非真正增量 parser |
| PROV-009 | P1 | M4 | Provider | PR-16 | TC-PROV-014 | stream consumer integration CI | Blocked | 无 iterator/callback 合同 |

## 4. Runtime

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUN-001 | P1 | M2 | Runtime | PR-09 | TC-RUN-001 | fake-provider integration CI | Implemented | 需接入统一 RuntimeResult |
| RUN-002 | P1 | M2 | Runtime | PR-09 | TC-RUN-002/003 | multi-round integration CI | Partial | 生命周期未统一 |
| RUN-003 | P1 | M2 | Runtime | PR-02/09 | TC-RUN-004 | architecture/negative API test | Blocked | 裸 handler 路径存在 |
| RUN-004 | P1 | M1/M2 | Runtime | PR #6 / PR-09 | TC-RUN-005 | transition manifest CI | Partial | state/transition/checkpoint 合同已冻结；生产 Runtime 尚未强制执行全部转换 |
| RUN-005 | P1 | M2 | Runtime | PR-09 | TC-RUN-006 | budget integration CI | Partial | 仅部分 step 行为 |
| RUN-006 | P1 | M2/M4 | Runtime | PR-08/09/16 | TC-RUN-012/013、TC-PROV-015 | cancellation integration CI | Planned | cancellation token 未实现 |
| RUN-007 | P1 | M2 | Runtime | PR-09 | TC-RUN-007 | budget matrix CI | Planned | token/cost/context/time 未接入 |
| RUN-008 | P1 | M2 | Runtime | PR-09 | TC-RUN-008 | tool-error policy CI | Partial | RecoveryPolicy 已实现；Runtime 级继续/终止策略未完成 |
| RUN-009 | P1 | M2 | Runtime | PR-02/09 | TC-RUN-009 | result-normalization CI | Blocked | handler 返回值未统一接入生产 Runtime |
| RUN-010 | P1 | M2/M4 | Runtime | PR-09/15 | TC-RUN-010 | malformed Provider integration CI | Blocked | evidence 先于 normalize |

## 5. Tool Contract

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TOOL-001 | P1 | M1/M2 | Runtime | PR #6 / PR-02 | TC-TOOL-001 | public API unit CI | Implemented | `ToolSpec` 类型和 schema 已实现；唯一 Registry 入口仍属 M2 |
| TOOL-002 | P1 | M2 | Runtime | PR-02 | TC-TOOL-002 | registry unit CI | Planned | Registry 未实现 |
| TOOL-003 | P1 | M2 | Runtime | PR #6 / PR-02 | TC-TOOL-003 | invalid fixture CI | Implemented | JSON Schema 验证合同已实现；生产 Runtime 尚未强制走 Registry |
| TOOL-004 | P1 | M1/M2 | Security | PR #6 / PR-02 | TC-TOOL-004 | registration negative CI | Partial | ToolSpec 合同包含 risk/side-effect；Registry 注册拒绝仍未实现 |
| TOOL-005 | P1 | M2 | Runtime | PR-02/08 | TC-TOOL-005/006 | timeout/output integration CI | Planned | limits 未接入 |
| TOOL-006 | P1 | M1/M2 | Recovery | PR #6/#9 / PR-02 | TC-TOOL-004/007 | recovery-policy CI | Partial | RecoveryPolicy 类型与恢复路径已实现；Registry 注册强制仍属 M2 |
| TOOL-007 | P1 | M2 | Runtime | PR #9 / PR-02/09 | TC-RUN-011 | unknown-tool integration CI | Partial | Session 恢复路径返回 `TOOL_NOT_FOUND`；统一 RuntimeResult 仍未完成 |

## 6. Workspace

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WS-001 | P0 | M1 | Security | PR #7/#13 | TC-WS-001 | run 33; Linux/macOS/Windows 20/20 | Verified | 无 M1 blocker；M2 继续资源限制与结构化 I/O |
| WS-002 | P0 | M1 | Security | PR #7/#13 | TC-WS-002/003 | run 33; Windows actual junction test | Verified | 无 M1 blocker；同账号恶意并发进程不在承诺范围 |
| WS-003 | P1 | M2 | Runtime | PR #7 / PR-09 | TC-WS-004 | UTF-8 boundary CI | Partial | containment 已统一；read byte-limit/UTF-8 截断语义未完成 |
| WS-004 | P1 | M2 | Runtime | PR #7 / PR-09 | TC-WS-005 | large-workspace budget CI | Planned | 无 file/byte/time budget |
| WS-005 | P1 | M2 | Runtime | PR #7 / PR-09 | TC-WS-006 | IO fixture CI | Partial | no-follow traversal 已实现；错误结构仍未统一 |

## 7. Policy、Approval 与 Execution

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-001 | P1 | M2 | Security | PR-07 | TC-SEC-001 | policy unit CI | Implemented | 需接入 Runtime |
| SEC-002 | P1 | M2 | Security | PR-07 | TC-SEC-002 | overlap fixture CI | Partial | 优先级未冻结 |
| SEC-003 | P1 | M2 | Security | PR-07 | TC-SEC-003 | approval integration CI | Blocked | ApprovalProvider 缺失 |
| SEC-004 | P1 | M2 | Security | PR-07/09 | TC-SEC-004 | no-bypass integration CI | Blocked | Runtime 直接调用 handler |
| SEC-005 | P1 | M0/M2 | Security | PR-00/08 | TC-SEC-007 | docs/type/help snapshot | Partial | README/Threat Model/ADR 已修正；生产类型与 CLI 命名尚待 M2 |
| SEC-006 | P1 | M2 | Security | PR-08 | TC-SEC-005 | child-env subprocess CI | Blocked | 继承宿主环境 |
| SEC-007 | P1 | M2 | Security | PR-08 | TC-SEC-006 | process-tree platform CI | Planned | cleanup 未实现 |
| SEC-008 | P1 | M2 | Runtime | PR-08 | TC-SEC-009 | adapter contract CI | Planned | adapter 接口未实现 |
| SEC-009 | P1 | M2 | Security | PR-07/14 | TC-SEC-008 | secret marker audit CI | Partial | 异常/参数面未全覆盖 |

## 8. ChangeManager

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHG-001 | P0 | M1 | Security | PR #8/#13 | TC-CHG-001 | run 33; forged handle 20/20 × 3 OS | Verified | 无 M1 blocker |
| CHG-002 | P0 | M1 | Security | PR #8/#13 | TC-CHG-002 | run 33; external path 20/20 × 3 OS | Verified | 无 M1 blocker |
| CHG-003 | P1 | M3 | Runtime | PR-13 | TC-CHG-003 | duplicate-path unit CI | Planned | 未拒绝重复路径 |
| CHG-004 | P1 | M3 | Runtime | PR-13 | TC-CHG-004 | concurrent fixture CI | Planned | 无 lock/完整 TOCTOU 控制 |
| CHG-005 | P1 | M3 | Runtime | PR #8 / PR-13 | TC-CHG-005 | stale rollback CI | Implemented | post-change hash 冲突保护已实现；M3 仍需并发/恢复矩阵 |
| CHG-006 | P1 | M3 | Runtime | PR-13 | TC-CHG-006 | platform metadata CI | Planned | mode/metadata 策略未定义 |
| CHG-007 | P1 | M3 | Runtime | PR #8 / PR-13 | TC-CHG-007/008 | fault-injection artifact | Partial | Journal 原子保存已实现；parent fsync/补偿与 crash-during-restore 不完整 |
| CHG-008 | P1 | M3 | Security | PR #8 / PR-13/14 | TC-CHG-009 | content-free audit CI | Partial | M1 测试证明默认 audit 不含正文；统一 audit schema 未冻结 |
| CHG-009 | P1 | M3 | Runtime | PR-13 | TC-CHG-010 | multi-file fault report | Blocked | 必须保持 best-effort 声明；锁与补偿矩阵未完成 |
| CHG-010 | P1 | M1/M3 | Recovery | PR #6/#8 / PR-13 | TC-CHG-011 | restart/expiry/scope CI | Partial | durable ChangeJournal、restart、expiry、scope 已实现；加密/锁/完整 lifecycle 属 M3 |

## 9. Session 与恢复

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SES-001 | P1 | M1/M3 | Recovery | PR #6 / PR-11 | TC-SES-001 | schema/API roundtrip CI | Partial | RecoverableCheckpoint 合同已冻结；生产 SessionStore 仍未完成 checkpoint/evidence 分离 |
| SES-002 | P1 | M1/M3 | Recovery | PR #6 / PR-11 | TC-SES-002 | continuation fixture CI | Partial | continuation 合同已冻结；完整 reasoning/provider continuation 恢复仍属 M3 |
| SES-003 | P1 | M3 | Security | PR-11 | TC-SES-003 | encrypted disk inspection | Planned | encryption injection 缺失 |
| SES-004 | P1 | M3 | Recovery | PR-11 | TC-SES-004/011 | crash/corrupt/concurrent CI | Partial | 原子保存原语存在；lock/corruption 语义不足 |
| SES-005 | P1 | M3 | Recovery | PR #6/#9 / PR-11 | TC-SES-005 | migration fixture CI | Partial | schema 1.0→1.1 与 future-version rejection 已实现；RecoverableCheckpoint migration 仍未完成 |
| SES-006 | P1 | M3 | Recovery | PR-12 | TC-SES-006 | resume integration CI | Implemented | 需纳入最终 Runtime 状态机 |
| SES-007 | P0 | M1 | Recovery | PR #9/#13 | TC-SES-007 | run 33; crash-after-effect 20/20 × 3 OS | Verified | 无 M1 blocker；完整 receipt/idempotency matrix 属 M3 |
| SES-008 | P1 | M3 | Runtime | PR #9 / PR-12 | TC-SES-008 | missing-handler recovery CI | Implemented | 恢复路径已结构化为 `TOOL_NOT_FOUND`；最终 Runtime 集成仍属 M2/M3 |
| SES-009 | P1 | M3 | Recovery | PR #9 / PR-12 | TC-SES-009 | fake-clock retry CI | Partial | attempt/max-attempt budget 已实现；backoff、time budget 与 fake-clock matrix 未完成 |
| SES-010 | P1 | M3 | Recovery | PR #6/#9 / PR-11/12 | TC-SES-010 | roundtrip integration CI | Partial | recovery/attempt/receipt/operator metadata 已持久化；完整 approvals/budgets/checkpoint roundtrip 未完成 |

## 10. Evidence 与隐私

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EVD-001 | P1 | M3 | Security | PR-14 | TC-EVD-001 | key marker leak CI | Partial | 输出面未全覆盖 |
| EVD-002 | P1 | M3 | Security | PR-14 | TC-EVD-001 | content marker leak CI | Implemented | 需动态复跑 |
| EVD-003 | P1 | M1/M3 | Runtime | PR #6 / PR-14 | TC-EVD-002 | property/fuzz artifact | Partial | PublishableEvidence 合同已冻结；total-function 实现未完成 |
| EVD-004 | P1 | M1/M3 | Runtime | PR #6 / PR-14 | TC-EVD-003 | canonical snapshot CI | Partial | schema 已冻结；wire JSON/canonical identity 仍不完整 |
| EVD-005 | P1 | M3 | Security | PR-14 | TC-EVD-004 | low-entropy threat test | Planned | 裸 hash 风险 |
| EVD-006 | P1 | M1/M3 | Runtime | PR #6 / PR-14 | TC-EVD-006 | schema compatibility CI | Partial | versioned schema 已实现；生产 Evidence 迁移与兼容门禁仍属 M3 |
| EVD-007 | P1 | M3 | Security | PR-10/14 | TC-EVD-007 | CLI/API debug gate CI | Partial | 危险开关语义不完整 |
| EVD-008 | P1 | M3 | Security | PR-14 | TC-EVD-005 | exception secret CI | Blocked | error 字段未统一脱敏 |

## 11. Observability 与预算

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBS-001 | P1 | M3 | Runtime | PR-14 | TC-OBS-007 | fake-clock latency CI | Partial | 未接入完整 lifecycle |
| OBS-002 | P1 | M3 | Runtime | PR-14 | TC-OBS-001 | usage/cost fixture CI | Partial | 分类语义混合 |
| OBS-003 | P1 | M3 | Runtime | PR-14 | TC-OBS-002 | missing-field CI | Blocked | unknown 被转为 0 |
| OBS-004 | P1 | M3 | Runtime | PR-14 | TC-OBS-003 | prompt-token fixture CI | Blocked | 输入成本漏算 |
| OBS-005 | P1 | M3 | Runtime | PR-14 | TC-OBS-004 | validation CI | Planned | 非法数值未拒绝 |
| OBS-006 | P1 | M3 | Runtime | PR-14 | TC-OBS-005 | partial-data CI | Blocked | 分母包含未知值 |
| OBS-007 | P1 | M2/M3 | Runtime | PR-09/14 | TC-OBS-006 | budget-stop integration CI | Planned | 预算未驱动 Runtime |

## 12. CLI 与文档

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLI-001 | P1 | M2/M4 | Runtime | PR-10 | TC-CLI-001 | subprocess CI | Implemented | 需保持无 Key |
| CLI-002 | P1 | M2/M4 | Runtime | PR-10 | TC-CLI-002 | golden/subprocess CI | Blocked | 默认仅摘要 |
| CLI-003 | P1 | M2/M4 | Runtime | PR-10 | TC-CLI-003 | stdout/report separation CI | Planned | 独立 report 缺失 |
| CLI-004 | P1 | M2/M4 | Security | PR-10 | TC-CLI-004 | help/golden CI | Partial | 危险提示不足 |
| CLI-005 | P1 | M2/M4 | Runtime | PR-10 | TC-CLI-005 | exit-code matrix CI | Partial | code 映射 ADR 已冻结，具体映射未实现 |
| CLI-006 | P1 | M2/M4 | Runtime | PR-10 | TC-CLI-006 | workspace error CI | Partial | 错误 UX 不统一 |
| DOC-001 | P1 | M4 | Release | PR-10/17 | TC-DOC-001 | doctor semantics CI | Partial | 诊断/在线可运行混淆 |

## 13. 开源与发布

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OSS-001 | P1 | M0/M5 | Release | PR #1/#2 / PR-18 | TC-OSS-001 | required PR checks | Partial | PR-first 流程和 PR CI 已建立；异常直推意味着 required-check enforcement 仍需 M5 明确定义和负向证据 |
| OSS-002 | P1 | M5 | Release | PR-18 | TC-OSS-001 | 3 OS × 3 Python matrix | Planned | M1 仅验证 P0 Python 3.11 三 OS；完整 release matrix 未建立 |
| OSS-003 | P1 | M0/M5 | Release | PR #1/#2 / PR-18 | TC-OSS-002 | Ruff + Pyright + coverage CI | Partial | Ruff/Pyright 已绿色；coverage 和完整矩阵尚未建立 |
| OSS-004 | P1 | M5 | Release | PR #6/#10/#13 / PR-18 | TC-OSS-002 | coverage reports + manifests | Partial | Gate manifest 与独立 workflow 已版本化并执行；coverage 配置/报告未实现 |
| OSS-005 | P1 | M0/M5 | Security | PR #1/#2 / PR-18 | TC-OSS-003 | tracked/artifact secret negative CI | Partial | tracked-file scanner 已绿色；故意 secret negative fixture 与 artifact scan 尚未实现 |
| OSS-006 | P1 | M5 | Release | PR-18 | TC-OSS-003/005 | artifact file manifest | Blocked | denylist 打包工作树 |
| OSS-007 | P1 | M5 | Release | PR-18 | TC-OSS-004 | recomputed digest + tamper failure | Blocked | 只检查长度 |
| OSS-008 | P1 | M5 | Release | PR-18 | TC-CFG-006、TC-OSS-006 | clean-venv logs | Planned | wheel/sdist gate 缺失 |
| OSS-009 | P1 | M0/M5 | Maintainer | PR #2 / PR-19 | TC-OSS-009 | governance files + docs/link CI | Partial | 治理文件与模板已落库、链接绿色；M5 仍需 release governance 复核 |
| OSS-010 | P1 | M0/M5 | Security | PR #2 / PR-19 | TC-OSS-010 | SECURITY gate + approved review | Partial | 范围/SLA/报告流程已文档化；私密报告能力与 release review 尚待验证 |
| OSS-011 | P1 | M0/M5/M6 | Maintainer | PR #2/#13 / PR-19 | TC-OSS-007 | README claim audit | Partial | README 已同步 M1 真实状态；完整逐项自动 claim audit 尚未实现 |

## 14. Release-level Evidence

| Evidence | Test/Gate | Required at M6 |
| --- | --- | --- |
| P0 repetition report | TC-WS-001–003、TC-CHG-001/002/011、TC-SES-007 | 是 |
| Full CI matrix | TC-OSS-001/002 | 是 |
| Coverage manifests | OSS-004 | 是 |
| Provider fixture manifest | TC-PROV-002–015 | 是 |
| Recovery fault matrix | TC-SES-006–011、TC-TOOL-007 | 是 |
| Artifact file manifest | TC-OSS-003/005 | 是 |
| Digest/tamper report | TC-OSS-004 | 是 |
| Clean-install logs | TC-CFG-006、TC-OSS-006 | 是 |
| Live DeepSeek smoke | TC-LIVE-001 | 是 |
| Governance/security review | TC-OSS-009/010 | 是 |
| README claim audit | TC-OSS-007 | 是 |
| Final RC test report | TC-OSS-008 | 是 |

## 15. 当前结论

M0 已关闭并建立 PR-first、异常直推需留痕的开发政策。

M1 已关闭：核心合同、Workspace containment、rollback authorization、side-effect uncertain 和永久 P0 Gate 已通过 PR #6–#10 合入 `develop`，并由 PR #13 的 Minimum CI run 82 与 M1 P0 Gate run 33 在集成态复验。`WS-001`、`WS-002`、`CHG-001`、`CHG-002`、`SES-007` 已提升为 `Verified`。

M2 的 ToolRegistry、Policy、Approval、ExecutionAdapter、统一 Runtime lifecycle、budget/cancellation、Workspace P1 和 CLI contract 是当前最高优先级阻断项。

因此当前发布结论继续保持：**NO RELEASE**。