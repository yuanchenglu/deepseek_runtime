# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.7  
> 状态日期：2026-07-28  
> 计划状态：**Execution in progress — M0/M1/M2-A/M2-B/M2-C closed, M2-D next**  
> 当前开发基线：`develop@7793a10152a49fb815aac667906080a4e1a39920`  
> 当前工作分支：`agent/m2-c-closeout`  
> 当前工作入口：Draft PR #19 `docs(roadmap): close M2-C and hand off M2-D`  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将 DeepSeek Runtime 做到：边界真实、执行可控、恢复正确、证据可信、构件可验证，并发布首个可持续维护的 Open-source Alpha。

M0–M6 期间不通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | Workspace、rollback authorization、uncertain side effect 已验证 | PR #6–#10、PR #13、Gate run 33 |
| M2-A ToolRegistry 唯一入口 | **CLOSED** | Registry-only Runtime path 已合入 | PR #14、runs 106/56、PR #15 |
| M2-B Policy 与 Approval | **CLOSED** | 受支持 Runtime tool call 强制经过 Policy/Approval | PR #16、runs 129/77、PR #17 |
| M2-C ExecutionAdapter | **CLOSED** | 统一 Adapter、进程资源控制和三平台专项 Gate 已合入 | PR #18、runs 165/111/15、merge `7793a101` |
| M2-D Runtime Lifecycle、Budget、Cancellation | **NEXT** | 生产状态转换、关键 checkpoint、完整取消和预算未闭环 | `RUN-001`–`008`、`OBS-007`、`SEC-003` |
| M2-E Workspace P1 | **NOT STARTED** | read/search byte/file/time 与结构化 I/O 未完成 | `WS-003`–`005` |
| M2-F CLI 核心 | **NOT STARTED** | stdout/report/json/exit-code 协议未完成 | `CLI-001`–`006` |
| M2-G Integrated Closeout | **NOT STARTED** | M2 全部 P1 尚未综合验收 | Traceability |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | P1 Requirement 仍有 Blocked/Partial | Traceability |
| M4 Provider、配置与协议收口 | **NOT STARTED** | Provider normalization/streaming/config 未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

客观结论：

- M0、M1、M2-A、M2-B、M2-C 已关闭；M2 总里程碑仍未关闭；
- ToolRegistry、Policy/Approval 与 ExecutionAdapter 已形成生产链；
- durable checkpoint timing、完整 Runtime lifecycle、budgets 和 Provider cancellation 仍未完成；
- M2–M5 仍有大量 P1 Requirement 未 `Verified`；
- 当前必须保持 **NO RELEASE**。

## 3. 已完成结果

### 3.1 M0

- PRD、测试、Traceability、Threat Model 和路线图的权威顺序已确定；
- LICENSE、NOTICE、CONTRIBUTING、SECURITY、SUPPORT 和治理文档已建立；
- Minimum CI 覆盖 Ruff、Pyright、unit、import、tracked-secret scan 和文档追踪；
- 开发流程明确为 PR-first，`develop` 异常直推必须留痕。

### 3.2 M1

- Error、Runtime State、Checkpoint/Evidence、ToolSpec、RecoveryPolicy、RollbackHandle 和 ChangeJournal 最小合同已冻结；
- Workspace read/search 统一经过 `WorkspaceResolver`；
- symlink 与 Windows reparse-point/junction P0 场景进入固定 Gate；
- rollback 使用 opaque handle + durable ChangeJournal；
- forged、expired、cross-workspace、external-path、stale rollback 结构化拒绝；
- side-effect crash window 进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不自动盲目重试；
- M1 P0 Gate run 33：Linux/macOS/Windows 各 140/140，总计 420/420。

### 3.3 M2-A：ToolRegistry

- 实施 PR #14，closeout PR #15；
- final head `a51d5b297d8233c654cc1569c5fe73b9730c28b6`；
- merge `b012265c4f51238c97c26c22b76d1e5e043153dc`；
- final Minimum CI run 106、M1 P0 Gate run 56 PASS；
- retained failures：runs 92、98；
- `RUN-003`、`RUN-009`、`TOOL-001`–`004`、`TOOL-007` Verified。

### 3.4 M2-B：Policy 与 Approval

- 实施 PR #16，closeout PR #17；
- final head `7e2913204b89164ba10ec3c43c03ab7bd69435af`；
- merge `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- final Minimum CI run 129、M1 P0 Gate run 77 PASS；
- retained failures：runs 114、122、127；
- READ 默认 ALLOW，非 READ 默认 DENY；
- last-match policy precedence、missing-path、approve-once/session、deny、timeout、unavailable fail-closed 已验证；
- `SEC-001`、`SEC-002`、`SEC-004` Verified；`SEC-003` 因 durable checkpoint/resume 保持 Partial。

### 3.5 M2-C：ExecutionAdapter

- 实施 PR #18，closeout PR #19；
- final head `b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`；
- merge `7793a10152a49fb815aac667906080a4e1a39920`；
- retained failure：Minimum CI run 144；
- final Minimum CI run 165：PASS；
- final M1 P0 Gate run 111：Linux/macOS/Windows PASS；
- M2 ExecutionAdapter Gate run 15：三平台各 36/36，总计 108/108，0 failed/errors/skipped；
- artifacts：Linux `8682866620`、macOS `8682871026`、Windows `8682875863`；
- strict review unresolved P0/S0/S1 = 0。

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

已关闭能力：

- 公共 `ExecutionAdapter`、`ExecutionContext`、`ExecutionOutcome`、capability 与 cancellation 合同；
- `FakeExecutionAdapter`、`NoIsolationLocalAdapter`、`RestrictedSubprocessAdapter`；
- minimal child environment 与 secret/loader-key stripping；
- contained cwd；
- ToolSpec timeout 与 combined stdout/stderr byte limit；
- timeout/cancel 后 process-tree cleanup；
- handler/builder/Popen/cwd/pipe failure 结构化且不泄漏异常正文；
- Runtime Adapter 强制接入；
- `WorkspaceSandbox.run()` 移除第二套直接 `subprocess.run` 生产路径；
- execution evidence 内容最小化；
- 所有当前 Adapter 均明确 `kernel_isolation=false`。

已 `Verified`：

- `TOOL-005`；
- `SEC-005`–`009`；
- `RUN-003`、`RUN-009` 的 Adapter 组成边界。

保持 `Partial`：

- `RUN-006`：Adapter-during-cancel 已实现；Provider-before-cancel、request cancellation、final lifecycle state 与 durable checkpoint 属 M2-D/M4。

M2-C 明确不承诺 container、VM、seccomp、Seatbelt、Job Object 或其他内核隔离，也不防御恶意 Tool builder 在返回 `SubprocessRequest` 前直接产生副作用。

## 4. 当前 closeout 工作现场

PR #19 为 docs-only：

1. 新增 `docs/roadmap/m2-c-closeout.md`；
2. 更新本路线图为 v2.2.7；
3. 更新 `docs/traceability/alpha-traceability.md` 为 v1.9；
4. 同步 PRD、Threat Model、README、测试报告和文档索引；
5. 不修改 `src/`、`tests/`、workflow、schema、packaging 或 `master`；
6. 不实现 M2-D 功能。

PR #19 Exit Gate：

- [x] PR #18 head、merge、失败/成功 run 与 artifact digest 写入 closeout；
- [x] Traceability 合并态与 M2-D blocker 同步；
- [ ] PRD 状态同步；
- [ ] 双语 README、Threat Model、测试报告和文档索引同步；
- [ ] changed files 全部为 docs；
- [ ] Minimum CI 全绿；
- [ ] M1 P0 Gate 与 M2 ExecutionAdapter Gate 全绿；
- [ ] strict docs review；
- [ ] Ready 后 squash merge 到 `develop`。

## 5. M2-D：Runtime Lifecycle、Budget、Cancellation

### 5.1 目标

把当前顺序式 Runtime loop 收敛为可测试、可观测、可 checkpoint 的单一生产生命周期，并实现任务级停止条件：

```text
CREATED
→ PROVIDER_PENDING
→ PROVIDER_COMPLETED
→ TOOL_REQUESTED
→ APPROVAL_PENDING?
→ TOOL_RUNNING
→ TOOL_SUCCEEDED | TOOL_FAILED | TOOL_UNCERTAIN
→ PROVIDER_PENDING
→ COMPLETED | FAILED | CANCELLED | BUDGET_EXCEEDED
```

M2-D 只扩展现有 `DeepSeekRuntime`，禁止创建第二套 Agent loop。

### 5.2 必须实现

1. 生产 Runtime 状态与已冻结 transition manifest 对齐；
2. 合法转换与非法前驱统一验证；
3. 每个关键转换发出内容最小化 lifecycle event；
4. 关键状态可转换为 `RecoverableCheckpoint` handoff；
5. Provider 调用前 cancellation 不发送请求；
6. Tool 执行中 cancellation 传入 Adapter 并形成最终 `CANCELLED` 语义；
7. step/token/cost/context/time budgets 实际驱动停止；
8. 未知 usage/cost 不转换为 0，也不虚构预算余量；
9. tool error continue/terminate policy 可配置且确定；
10. malformed Provider 支持范围内返回 `RuntimeResult`，不抛未处理异常；
11. lifecycle/checkpoint/evidence 不泄露 prompt、response、reasoning、tool arguments/results 或 secret；
12. 建立 M2-D focused Gate。

### 5.3 目标 Requirement/Test

- `RUN-001` / `TC-RUN-001`：text-only lifecycle；
- `RUN-002` / `TC-RUN-002/003`：单轮与多轮 tool loop；
- `RUN-004` / `TC-RUN-005`：状态转换、event、checkpoint handoff；
- `RUN-005` / `TC-RUN-006`：max steps；
- `RUN-006` / `TC-RUN-012/013`：Provider-before-cancel 与 Tool-during-cancel；
- `RUN-007` / `TC-RUN-007`：token/cost/context/time budgets；
- `RUN-008` / `TC-RUN-008`：tool error policy；
- `RUN-010` / `TC-RUN-010`：malformed Provider total-function subset；
- `OBS-007` / `TC-OBS-006`：budget-stop evidence；
- `SEC-003`：approval event checkpoint timing handoff，不提前完成 M3 resume/migration。

### 5.4 合同决策

- `RuntimeResult` 是所有正常终止路径的唯一返回 envelope；
- cancellation 与 budget stop 必须有 machine-readable error code；
- Provider request 中断能力若现有 transport 不支持，M2-D 至少关闭 Provider-before-call，进行中 request cancellation 明确移交 M4；
- checkpoint handoff 不等于 M3 durable/encrypted/locked store；
- usage/cost 缺失保持 unknown；
- side-effect uncertain 不得被 error policy 自动继续或重试。

### 5.5 明确不做

M2-D 不混入：

- Workspace read/search P1 budgets（M2-E）；
- CLI stdout/report/json/exit-code 协议（M2-F）；
- Provider streaming、retry、body-size 与完整 normalization（M4）；
- durable encrypted checkpoint store、migration、locking（M3）；
- ChangeManager、Evidence totality/canonical redesign（M3）；
- container/VM/kernel sandbox；
- Packaging、release matrix 或 `master`。

### 5.6 分支与 PR

PR #19 合入后，从最新 `develop` 创建：

```text
agent/m2-runtime-lifecycle
```

Draft PR 建议标题：

```text
feat(runtime): establish M2-D lifecycle and budget path
```

实施顺序：

```text
state/event contract
→ lifecycle recorder
→ Runtime integration
→ cancellation semantics
→ budgets
→ tool error policy
→ malformed Provider boundaries
→ focused tests/Gate
→ Traceability/docs
→ final exact-head CI
→ strict review
→ Ready/merge
```

## 6. 后续 M2 顺序

### M2-E：Workspace P1

UTF-8 byte-safe truncation、read limit、search file/byte/time budgets、binary/permission/file-disappeared 结构化结果。目标用例：`TC-WS-004`–`006`。

### M2-F：CLI 核心

stdout 最终回答、stderr 进度、`--report`、`--json`、unsafe debug、稳定 exit code、workspace 错误 UX。目标用例：`TC-CLI-001`–`006`。

### M2-G：Integrated Closeout

必须通过 `TC-RUN-001`–`013`、`TC-TOOL-001`–`007`、`TC-WS-004`–`006`、`TC-SEC-001`–`009`、`TC-CLI-001`–`006`；无 Registry/Policy/Approval/Adapter bypass；transition 合法/非法类别覆盖 100%；Active P1 Runtime/Tool/Security defect = 0；在 integrated `develop` 复跑 closeout。

## 7. M3–M6 摘要

### M3

checkpoint/evidence 分离；atomic save、fsync、locking、corruption、migration、optional encryption；three crash windows；ChangeManager conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider normalization、malformed schema、error mapping、retry/budget/size、request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 只允许 P0/P1 fix、测试稳定性、文档事实和 release pipeline fix。最终 Gate 要求所有 P0/P1 `Verified`，Active P0/P1/S0/S1 = 0，测试/矩阵/构件/claim traceability 全部通过。任一 Gate 不满足，结论必须是 `No Release`。

## 8. 执行纪律

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
```

禁止：

- 在 `master` 直接开发；
- 用 rerun 覆盖失败证据；
- 降低 Pyright/Ruff/test assertion；
- 用 cast、fallback 或文档措辞掩盖真实合同错误；
- 将后续里程碑工作混入当前 PR；
- 在 M6 Gate 前发布、打正式 tag 或把 `master` 当开发分支。

当前结论：**NO RELEASE**。
