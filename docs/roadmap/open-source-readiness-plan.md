# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.3.3  
> 状态日期：2026-07-29  
> 计划状态：**Execution in progress — M0/M1/M2-A/M2-B/M2-C/M2-D closed; M2-E Workspace P1 next**  
> 已合入开发基线：`develop@2fe059d900c4e04fab05ca92f421a41d7ff0aa01`  
> 当前远程工作分支：`agent/m2-d-closeout`  
> 当前工作入口：PR #21 `docs(readiness): close M2-D runtime lifecycle milestone`；merge 后立即创建 M2-E implementation PR  
> 当前 PR head：必须从 GitHub 动态获取  
> 全计划自主执行提示词：`docs/roadmap/full-plan-autonomous-handoff.md`  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将 DeepSeek Runtime 做到：边界真实、执行可控、恢复正确、证据可信、构件可验证，并发布首个可持续维护的 Open-source Alpha。

M0–M6 期间不通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 当前事实快照

- 当前交接容器没有本地 Git 工作树，也没有未提交、未 push 的本地文件；
- M2-D implementation PR #20 已从 exact head `10f5240d` squash merge 为 `develop@2fe059d9`；
- docs-only closeout PR #21 正在把合入态 Requirement 提升为 Verified；
- 原 M2-D blocker 已修复：同一 tool batch 后续 ASK 的 resolved outcome 在 Adapter 执行前 handoff；deny、timeout、unavailable、invalid outcome 在结构化返回前 handoff；
- 不得通过删除测试、降低断言、隐藏失败 run 或只引用较早绿色 head 将 M2-D 标记为完成；
- 新会话必须使用 `docs/roadmap/full-plan-autonomous-handoff.md`，关闭 M2-D 后自动连续推进 M2-E、M2-F、M2-G、M3、M4、M5、M6，不等待用户反复发送“继续”。

## 3. 总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | Workspace、rollback authorization、uncertain side effect 已验证 | PR #6–#10、PR #13、Gate run 33 |
| M2-A ToolRegistry 唯一入口 | **CLOSED** | Registry-only Runtime path 已合入 | PR #14、runs 106/56、PR #15 |
| M2-B Policy 与 Approval | **CLOSED** | Runtime tool call 强制经过 Policy/Approval | PR #16、runs 129/77、PR #17 |
| M2-C ExecutionAdapter | **CLOSED** | 统一 Adapter、进程资源控制和三平台专项 Gate 已合入 | PR #18、runs 165/111/15、PR #19 |
| M2-D Runtime Lifecycle、Budget、Cancellation | **CLOSED** | exact-head 四套 Gate 全绿；implementation merge `2fe059d9`；closeout PR #21 | PR #20/#21、runs 229/173/79/44 |
| M2-E Workspace P1 | **NEXT** | read/search byte/file/time 与结构化 I/O 未完成 | `WS-003`–`005` |
| M2-F CLI 核心 | **NOT STARTED** | stdout/report/json/exit-code 协议未完成 | `CLI-001`–`006` |
| M2-G Integrated Closeout | **NOT STARTED** | M2 全部 P1 尚未综合验收 | Traceability |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | durable recovery/evidence gate 未建立 | Traceability |
| M4 Provider、配置与协议收口 | **NOT STARTED** | Provider normalization/streaming/config 未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

### 3.1 进度判断

- 基线、治理和 P0 安全合同已完成；
- M2 Runtime/Tool/Security 主链中 A/B/C/D 已关闭，E 为当前唯一合法下一切片，F/G 未开始；
- M3 durable recovery/evidence、M4 Provider、M5 packaging/release matrix、M6 RC 仍是主要未完成工作；
- 当前整体 Alpha 发布就绪度约为 **35%–40%**，仅用于资源规划，不替代 Requirement/Test/Evidence Gate；
- 当前必须保持 **NO RELEASE**。

## 4. 已关闭阶段

### 4.1 M0

- PRD、测试、Traceability、Threat Model 和路线图的权威顺序已确定；
- LICENSE、NOTICE、CONTRIBUTING、SECURITY、SUPPORT 和治理文档已建立；
- Minimum CI 覆盖 Ruff、Pyright、unit、import、tracked-secret scan 和文档追踪；
- 开发流程明确为 PR-first，`develop` 异常直推必须留痕。

### 4.2 M1

- Error、Runtime State、Checkpoint/Evidence、ToolSpec、RecoveryPolicy、RollbackHandle 和 ChangeJournal 最小合同已冻结；
- Workspace read/search 统一经过 `WorkspaceResolver`；
- symlink 与 Windows reparse-point/junction P0 场景进入固定 Gate；
- rollback 使用 opaque handle + durable ChangeJournal；
- forged、expired、cross-workspace、external-path、stale rollback 结构化拒绝；
- side-effect crash window 进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不自动盲目重试；
- M1 P0 Gate run 33：Linux/macOS/Windows 各 140/140，总计 420/420。

### 4.3 M2-A

- 实施 PR #14，closeout PR #15；
- merge `b012265c4f51238c97c26c22b76d1e5e043153dc`；
- final Minimum CI run 106、M1 P0 Gate run 56 PASS；
- retained failures：runs 92、98。

### 4.4 M2-B

- 实施 PR #16，closeout PR #17；
- merge `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- final Minimum CI run 129、M1 P0 Gate run 77 PASS；
- retained failures：runs 114、122、127。

### 4.5 M2-C

- 实施 PR #18，closeout PR #19；
- implementation merge `7793a10152a49fb815aac667906080a4e1a39920`；
- closeout merge `45b7c448d437df9ced5b5776f017a008376dabbb`；
- final Minimum CI run 165、M1 P0 Gate run 111、M2 ExecutionAdapter Gate run 15 PASS；
- retained failure：Minimum CI run 144。

生产调用链：

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider（仅 ASK）
→ ExecutionAdapter
→ deterministic result normalization
→ content-minimized execution evidence
```

## 5. M2-D 已关闭

### 5.1 合入态能力

- `LifecycleEvent`、`LifecycleTrace` 与 transition manifest 一致性检查；
- Provider round / tool batch 粒度的单一生产 lifecycle；
- private `RecoverableCheckpoint` handoff；
- Provider-before-call cancellation；
- pure tool cancellation 与 side-effect uncertain；
- step/token/USD cost/context/time budgets；
- unknown usage/cost 保持 unknown；
- `ToolErrorPolicy.CONTINUE/TERMINATE`；
- malformed Provider structured `RuntimeResult` subset；
- public usage evidence 数值白名单；
- side-effect success private structural receipt；
- 三平台 M2 Runtime Lifecycle focused Gate；
- Runtime lifecycle 合同、worklog、测试报告和严格 review tests。

### 5.2 Blocker closure

原严格回归 `test_later_batch_approval_is_checkpointed_before_execution` 已在不增加第二套生产状态机的前提下修复。新增矩阵覆盖 approve-session、deny、timeout、missing/failed ApprovalProvider 与 invalid outcome：pending 在 Provider I/O 前 handoff；resolved outcome 在 Adapter 执行或结构化返回前 handoff。该回归与断言均保留。

### 5.3 M2-D Exit Gate

- [x] approval checkpoint regression 与 resolved outcome matrix 通过；
- [x] final exact-head Minimum CI run 229 成功；
- [x] M1 P0 Gate run 173 三平台各 140/140；
- [x] M2 ExecutionAdapter Gate run 79 三平台各 36/36；
- [x] M2 Runtime Lifecycle Gate run 44 三平台各 64/64；
- [x] artifact ID、digest、测试分母和 retained failures 已记录；
- [x] changed files、reviews、threads、P0/S0/S1 strict review 完成；
- [x] PR #20 Ready 并 squash merge 为 `2fe059d9`；
- [x] docs-only closeout PR #21 建立并同步 Verified 状态；
- [x] M2-E Workspace P1 成为下一执行切片。

## 6. 后续执行顺序

```text
M2-D closeout
→ M2-E Workspace P1
→ M2-F CLI 核心
→ M2-G Integrated Closeout
→ M3 Recovery / Change / Evidence / Observability
→ M4 Provider / Config / Protocol
→ M5 CI Matrix / Packaging / Governance
→ M6 RC / Alpha Release Gate
```

完整自主执行规则见：

```text
docs/roadmap/full-plan-autonomous-handoff.md
```

新会话不得只完成 M2-D 后停止。除必须由用户提供密钥、权限、签名或外部人工审核的硬阻断外，应自动连续执行整个 Plan。

## 7. 开发纪律

默认流程：

```text
latest develop
→ agent/<scope>
→ Draft PR
→ tests / Traceability / docs / CI
→ strict review
→ Ready for Review
→ required CI green
→ squash merge to develop
→ docs-only closeout
→ next milestone
```

直推 `develop` 只作为 PR 流程无法解决的异常兜底。直推 commit 必须包含：

```text
<type>(<scope>): <变更说明>

## 问题原因
[PR 流程无法通过的真实根因]

## 技术债务
- [未解决问题]
- [后续验证项]
```

禁止：

- 在 `master` 直接开发；
- 删除或隐藏失败证据；
- rerun-mask；
- 降低 Ruff、Pyright、test assertion、安全合同或 release criteria；
- 用 cast、fallback、skip 或文档措辞掩盖真实缺陷；
- 将 `Implemented` 写成 `Verified`；
- 伪造 live smoke、人工审核、artifact 或外部凭据结果；
- 在 M6 Gate 前发布、打正式 tag 或更新 `master`。

## 8. 最终发布条件

只有以下条件全部满足，才允许执行发布：

- 全部 P0/P1 Requirement 为 `Verified`；
- Active P0/P1/S0/S1 = 0；
- 完整 OS/Python matrix 通过；
- coverage、Provider fixtures、recovery matrix、artifact manifest、digest/tamper、clean install、live smoke、governance/security review、README claim audit 和最终 RC report 全部通过；
- 所有证据可访问并与最终 RC head 对应。

任一条件不满足，结论必须保持：

```text
NO RELEASE
```
