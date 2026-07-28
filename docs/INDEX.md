# DeepSeek Runtime 文档索引

> 适用验证基线：PR #13 head `81643dca`
> 文档修订：以各文件所在 Git commit 为准
> 文档状态：Open-source Alpha Hardening；M1 Closed；M2 authorized
> 原则：PRD 是产品范围、优先级和验收标准的唯一事实源；架构、测试和路线图均引用 PRD Requirement ID。

## 核心文档

| 文档 | 目的 |
| --- | --- |
| [原始 Code Review](reviews/2026-07-27-code-review.md) | M0 基线上的完整代码质量、安全性、正确性和工程化审查 |
| [M1 Code Review Closeout](reviews/2026-07-28-m1-closeout-review.md) | M1 对原始 P0/P1 finding 的关闭、保留和下一阶段判断 |
| [产品架构](architecture/product-architecture.md) | 产品定位、用户、能力域、使用链路和边界 |
| [技术架构](architecture/technical-architecture.md) | 当前实现、目标组件、数据流、信任边界和非功能约束 |
| [PRD](product/PRD.md) | 产品需求、优先级、验收标准、非目标和 M0–M6 发布门禁 |
| [Threat Model](security/threat-model.md) | 保护资产、攻击输入、信任边界、保证与未保证边界 |
| [Known Unknowns](known-unknowns.md) | 当前未承诺、未验证和后续必须复核的边界 |
| [ADR Index](adr/README.md) | 已接受的 Runtime、安全、恢复、schema、类型和发布决策 |
| [Runtime Core Contracts](contracts/runtime-contracts.md) | Error、State、Tool、Checkpoint、Evidence、Recovery 与 ChangeJournal 合同 |
| [State Transition Manifest](contracts/runtime-state-transitions.json) | 合法状态转换及 checkpoint/retry/approval/receipt 分母 |
| [Versioned Schemas](schemas/README.md) | Error、Checkpoint、Evidence 与 ChangeJournal JSON Schema |
| [Alpha Traceability](traceability/alpha-traceability.md) | Requirement → Milestone → PR → Test → Evidence 唯一追踪表 |
| [M1-A Contract Evidence](traceability/m1-core-contracts.md) | PR #6 合同实现、Run 38、状态与剩余阻塞 |
| [M1 Workspace Evidence](traceability/m1-workspace-p0.md) | PR #7 containment 实现和对抗测试证据 |
| [M1 Rollback Evidence](traceability/m1-rollback-p0.md) | PR #8 opaque handle、ChangeJournal 和回滚约束证据 |
| [M1 Side-effect Evidence](traceability/m1-side-effect-p0.md) | PR #9 uncertain/reconciliation 实现证据 |
| [测试计划](testing/test-plan.md) | 测试策略、环境、明确分母、准入和退出标准 |
| [测试用例](testing/test-cases.md) | 功能、安全、恢复、协议、性能和发布用例 |
| [基线测试报告](testing/test-report-2026-07-27.md) | M0 基线证据、静态确认缺陷和发布结论 |
| [M0 Minimum CI 验证](testing/m0-ci-validation.md) | Python 3.11 最小门禁的真实执行、发现、修复和边界 |
| [M1 P0 三平台报告](testing/m1-p0-report.md) | Linux/macOS/Windows 集成态重复 Gate、失败历史和 artifact |
| [M0 Closeout](roadmap/m0-closeout.md) | M0 Exit Gate、当前分支政策和异常直推纪律 |
| [M1 Integrated Closeout](roadmap/m1-closeout.md) | PR #6–#10 合并态复验、M1 Exit Gate 和 M2 准入条件 |
| [开源就绪执行计划](roadmap/open-source-readiness-plan.md) | Contract-first 的 M0–M6 开源阻断项清零计划 |

## 治理与维护

| 文档 | 目的 |
| --- | --- |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | PR-first 流程、异常直推纪律、检查命令和 Definition of Done |
| [`SECURITY.md`](../SECURITY.md) | 安全范围、M1 控制状态、私密报告渠道、严重度和响应目标 |
| [`SUPPORT.md`](../SUPPORT.md) | 当前支持范围、问题入口和不支持场景 |
| [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | 社区行为与执行原则 |
| [`NOTICE`](../NOTICE) | 源码沿革和归属声明 |
| [Breaking-change Policy](governance/breaking-change-policy.md) | API、CLI、schema 和 error-code 兼容流程 |
| [Dependency License Review](governance/dependency-license-review.md) | 当前 manifest、许可风险和 M5 复核要求 |
| [Dependency/Security Update Policy](governance/dependency-security-update-policy.md) | 依赖引入、版本、更新、漏洞和 No-Go 规则 |

## 文档权威顺序

发生冲突时按以下顺序处理：

1. `product/PRD.md`：范围、优先级、Requirement 和验收标准；
2. `security/threat-model.md`：安全保证、非保证和信任边界；
3. `architecture/*`、`contracts/*`、`schemas/*` 与 ADR：技术合同和实现决策；
4. `testing/test-cases.md`：验证场景，不得修改 Requirement 优先级；
5. `traceability/alpha-traceability.md`：执行归属和证据状态；
6. `roadmap/open-source-readiness-plan.md` 与 milestone closeout：执行顺序和里程碑状态；
7. README：入口和已验证能力摘要，不得新增需求。

## 状态定义

| 状态 | 含义 |
| --- | --- |
| Implemented | 当前代码存在对应实现，但不等于已通过完整 Alpha 验证 |
| Partial | 存在局部实现、合同或证据，端到端能力不完整 |
| Planned | PRD 已定义，当前未实现 |
| Blocked | 存在 P0/P1 缺陷，不能作为可承诺能力发布 |
| Verified | 有可复现自动化测试和可访问证据 |
| Static-confirmed | 通过代码控制流或数据流审查确认，尚未动态执行 |
| Not-run | 当前没有实际执行证据 |

## 文档治理

1. 新功能必须先更新 PRD；首个 Alpha 原则上不接受非阻断功能。
2. 安全边界变化必须同步 Threat Model、SECURITY 和相关 ADR。
3. 架构变化必须同步技术架构、错误/状态/schema 合同。
4. 每条 P0/P1 Requirement 必须对应至少一个同级自动化 Test Case。
5. Test Case 不得隐式提升或降低 Requirement 优先级。
6. 每个实现 PR 必须更新 Traceability 的 PR、Test、Evidence、Status 和 Blocker。
7. 发布报告只能引用可复现 CI、artifact 或批准的 RC 证据。
8. README 只承担项目入口职责，不重复定义产品范围。
9. PRD、测试、路线图或 Traceability 冲突时必须暂停实现，先修正文档。
10. 默认走功能分支 → PR → CI → `develop`；异常直推必须记录问题原因和技术债务。

## 当前发布状态

M1 已关闭。PR #13 的 Minimum CI run 82 与 M1 P0 Gate run 33 在完整合并态验证了 Linux/macOS/Windows 各 140/140，合计 420/420。`WS-001`、`WS-002`、`CHG-001`、`CHG-002`、`SES-007` 已标记为 `Verified`。

M2 已获准执行。ToolRegistry、Policy、Approval、ExecutionAdapter、统一 Runtime lifecycle、预算/取消、Workspace P1 和 CLI contract 仍是当前阻断项。

**当前结论：NO RELEASE。**