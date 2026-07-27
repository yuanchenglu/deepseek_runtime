# DeepSeek Runtime 文档索引

> 适用代码审查基线：`develop@0e1e435`
> 文档修订：以各文件所在 Git commit 为准
> 文档状态：Open-source Alpha Hardening
> 原则：PRD 是产品范围、优先级和验收标准的唯一事实源；架构、测试和路线图均引用 PRD Requirement ID。

## 核心文档

| 文档 | 目的 |
| --- | --- |
| [Code Review](reviews/2026-07-27-code-review.md) | 当前代码质量、安全性、正确性和工程化审查 |
| [产品架构](architecture/product-architecture.md) | 产品定位、用户、能力域、使用链路和边界 |
| [技术架构](architecture/technical-architecture.md) | 当前实现、目标组件、数据流、信任边界和非功能约束 |
| [PRD](product/PRD.md) | 产品需求、优先级、验收标准、非目标和 M0–M6 发布门禁 |
| [Threat Model](security/threat-model.md) | 保护资产、攻击输入、信任边界、保证与未保证边界 |
| [ADR Index](adr/README.md) | 已接受的 Runtime、安全、恢复、schema、类型和发布决策 |
| [Alpha Traceability](traceability/alpha-traceability.md) | Requirement → Milestone → PR → Test → Evidence 唯一追踪表 |
| [测试计划](testing/test-plan.md) | 测试策略、环境、明确分母、准入和退出标准 |
| [测试用例](testing/test-cases.md) | 功能、安全、恢复、协议、性能和发布用例 |
| [测试报告](testing/test-report-2026-07-27.md) | 当前基线证据、静态确认缺陷、阻塞项和发布结论 |
| [M0 Minimum CI 验证](testing/m0-ci-validation.md) | Python 3.11 最小门禁的真实执行、发现、修复和边界 |
| [开源就绪执行计划](roadmap/open-source-readiness-plan.md) | Contract-first 的 M0–M6 开源阻断项清零计划 |

## 治理与维护

| 文档 | 目的 |
| --- | --- |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | 贡献流程、PR 内容、检查命令和 Definition of Done |
| [`SECURITY.md`](../SECURITY.md) | 安全范围、私密报告渠道、严重度和响应目标 |
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
3. `architecture/*` 与 ADR：技术合同和实现决策；
4. `testing/test-cases.md`：验证场景，不得修改 Requirement 优先级；
5. `traceability/alpha-traceability.md`：执行归属和证据状态；
6. `roadmap/open-source-readiness-plan.md`：执行顺序和里程碑；
7. README：入口和已验证能力摘要，不得新增需求。

## 状态定义

| 状态 | 含义 |
| --- | --- |
| Implemented | 当前代码存在对应实现，但不等于已通过 Alpha 验证 |
| Partial | 存在局部实现，端到端能力不完整 |
| Planned | PRD 已定义，当前未实现 |
| Blocked | 存在 P0/P1 缺陷，不能作为可承诺能力发布 |
| Verified | 有可复现自动化测试和证据 |
| Static-confirmed | 通过代码控制流或数据流审查确认，尚未动态执行 |
| Not-run | 当前没有实际执行证据 |

## 文档治理

1. 新功能必须先更新 PRD；首个 Alpha 原则上不接受非阻断功能。
2. 安全边界变化必须同步 Threat Model 和相关 ADR。
3. 架构变化必须同步技术架构、错误/状态/schema 合同。
4. 每条 P0/P1 Requirement 必须对应至少一个同级自动化 Test Case。
5. Test Case 不得隐式提升或降低 Requirement 优先级。
6. 每个实现 PR 必须更新 Traceability 的 PR、Test、Evidence、Status 和 Blocker。
7. 发布报告只能引用可复现 CI、artifact 或批准的 RC 证据。
8. README 只承担项目入口职责，不重复定义产品范围。
9. PRD、测试、路线图或 Traceability 冲突时必须暂停实现，先修正文档。

## 当前发布状态

M0 最小 Python 3.11 自动化门禁已有真实绿色证据，但完整跨平台 CI、P0/P1 对抗测试、覆盖率和发布构件证据尚未形成。

**当前结论：NO RELEASE。**
