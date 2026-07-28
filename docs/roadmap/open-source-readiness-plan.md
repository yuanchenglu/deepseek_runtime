# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.4  
> 状态日期：2026-07-28  
> 计划状态：**Execution in progress — M0/M1/M2-A closed, M2-B next**  
> 当前开发基线：`develop@b012265c4f51238c97c26c22b76d1e5e043153dc`  
> 当前工作分支：`agent/m2-a-closeout`  
> 当前工作入口：Draft PR #15 `docs(roadmap): close M2-A and hand off M2-B`  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将 DeepSeek Runtime 做到：边界真实、执行可控、恢复正确、证据可信、构件可验证，并发布首个可持续维护的 Open-source Alpha。

M0–M6 期间不通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | Workspace、rollback authorization、uncertain side effect 已验证 | PR #6–#10、PR #13、Gate runs 33/40 |
| M2-A ToolRegistry 唯一入口 | **CLOSED** | Registry-only Runtime path 已合入 `develop` | PR #14、Minimum CI run 106、M1 P0 Gate run 56 |
| M2-B Policy 与 Approval | **NEXT** | 旧 Policy 未接入生产 Registry，ApprovalProvider 缺失 | `SEC-001`–`004/008` |
| M2-C–M2-G | **NOT STARTED** | Adapter、lifecycle/budget/cancellation、Workspace P1、CLI、integrated closeout 未完成 | Traceability |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | P1 Requirement 仍有 Blocked/Partial | Traceability |
| M4 Provider、配置与 CLI 协议收口 | **NOT STARTED** | Provider、streaming、配置和稳定协议未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

客观结论：

- M0、M1、M2-A 已关闭；M2 总里程碑仍远未关闭；
- M2-A 只关闭 ToolRegistry 唯一入口，不代表 Policy、Approval、Adapter 或 lifecycle 已完成；
- M2–M5 仍有大量 P1 Requirement 未 `Verified`；
- 当前必须保持 **NO RELEASE**。

## 3. 已完成结果

### M0

- PRD、测试、Traceability、Threat Model 和路线图的权威顺序已确定；
- LICENSE、NOTICE、CONTRIBUTING、SECURITY、SUPPORT 和治理文档已建立；
- Minimum CI 覆盖 Ruff 关键规则、Pyright、unit tests、import、secret scan 和文档追踪；
- 开发流程明确为“PR 优先，直推 `develop` 仅作为异常兜底”。

### M1

- Error、Runtime State、Checkpoint/Evidence、ToolSpec、RecoveryPolicy、RollbackHandle 和 ChangeJournal 最小合同已冻结；
- Workspace read/search 统一经过 `WorkspaceResolver`；
- symlink 和 Windows reparse-point/junction P0 场景进入固定 Gate；
- rollback 使用 opaque handle + durable ChangeJournal；
- forged、expired、cross-workspace、external-path、stale rollback 有结构化拒绝；
- side-effect crash window 进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不自动盲目重试；
- PR #6 → #7 → #8 → #9 → #10 已按顺序合入 `develop`；
- PR #13 完成 integrated closeout。

M1 证据：

- Run 33：Linux/macOS/Windows 各 140/140，总计 420/420，0 failed/skipped/N/A；
- Windows `TC-WS-003` 实际执行 junction/reparse-point 测试；
- artifacts：Linux `8676238220`、macOS `8676237125`、Windows `8676241048`；
- 最终精确内容：Minimum CI run 89 PASS，M1 P0 Gate run 40 三平台 PASS。

### M2-A

M2-A 已由 PR #14 `feat(runtime): establish ToolRegistry production path` squash 合入 `develop`。

合并态：

- 最终 PR head：`a51d5b297d8233c654cc1569c5fe73b9730c28b6`；
- merge commit：`b012265c4f51238c97c26c22b76d1e5e043153dc`；
- Minimum CI run 106：PASS；
- M1 P0 Gate run 56：Linux/macOS/Windows 全部 PASS；
- 严格 Code Review：未解决 P0/S0/S1 = 0；
- closeout：`docs/roadmap/m2-a-closeout.md`。

已关闭能力：

- `ToolRegistry` 是 Runtime 的生产工具集合；
- `DeepSeekRuntime.run()` 只接受 `ToolRegistry | None`；
- CLI 默认传 `WorkspaceTools(...).catalog()`，`--no-tools` 传 `None`；
- 不保留裸 `{}` 或 `dict[str, handler]` production fallback；
- duplicate、handler、risk、side-effect、limits、`RecoveryPolicy` 注册合同；
- JSON Schema Draft 2020-12 参数校验；
- Provider definitions 从 `ToolSpec` 生成；
- unknown tool、invalid result、handler exception、malformed tool-call 的结构化边界；
- malformed tool-call 不执行 handler，也不会使 Evidence 或 safe serialization 崩溃。

已 `Verified`：

- `RUN-003` / `TC-RUN-004`；
- `RUN-009` / `TC-RUN-009`；
- `TOOL-001`–`004` / `TC-TOOL-001`–`004`；
- `TOOL-007` / `TC-RUN-011`。

保留失败证据：

1. Minimum CI run 92：CLI 裸 `{}` fallback 导致 Pyright 失败；
2. Minimum CI run 98：malformed `function` 在校验前触发旧 Evidence helper 异常。

两次失败均通过修复实现和补回归测试解决，未 rerun 掩盖、未降低规则、未降低断言。

## 4. 当前 closeout 工作现场

PR #15 只同步合并后的事实状态：

1. 新增 `docs/roadmap/m2-a-closeout.md`；
2. 更新本路线图为 v2.2.4；
3. 更新 `docs/traceability/alpha-traceability.md` 为 M2-A merged/Verified；
4. 更新 `README.md` 与 `README_en.md`；
5. 不修改生产代码；
6. 不实现 M2-B 功能。

PR #15 完成条件：

- [x] 实际 PR、merge commit、失败与成功 CI evidence 写入文档；
- [x] M2-A Requirement 状态与 Blocker 同步；
- [x] 双语 README 不再声称 PR #14 待 merge；
- [x] 明确 M2-B 是下一切片；
- [ ] Minimum CI 全绿；
- [ ] M1 P0 Gate 全绿；
- [ ] 严格文档 review；
- [ ] Ready 后合入 `develop`。

## 5. M2-B：Policy 与 Approval

### 5.1 目标

M2-B 必须把 Policy decision 与 Approval 强制接入 PR #14 建立的 Registry execution path，做到每一次工具执行都无法绕过：

```text
Provider tool call
→ ToolRegistry resolve + argument validation
→ PermissionRequest
→ PermissionPolicy decision
→ ALLOW / DENY / ASK
→ ApprovalProvider（仅 ASK）
→ approved execution 或 structured refusal
```

### 5.2 最小合同

1. READ 默认 `ALLOW`；
2. 非 READ 默认 `DENY`；
3. 显式规则优先于默认值；
4. overlap/priority 行为稳定、可测试；
5. `ASK` 必须进入 `ApprovalProvider`；
6. 支持 approve-once、approve-session、deny、timeout；
7. 缺失 ApprovalProvider 时 `ASK` fail-closed；
8. 用户摘要不得包含 secret、完整参数、命令正文或文件正文；
9. policy decision 与 approval outcome 进入可发布 Evidence/Checkpoint 最小字段；
10. handler 只有在最终 `ALLOW` 后才能执行。

### 5.3 目标 Requirement/Test

- `SEC-001` / `TC-SEC-001`：默认策略；
- `SEC-002` / `TC-SEC-002`：规则优先级与 overlap；
- `SEC-003` / `TC-SEC-003`：ApprovalProvider；
- `SEC-004` / `TC-SEC-004`：不可绕过；
- `SEC-009` / `TC-SEC-008`：摘要与 secret marker。

### 5.4 明确不做

M2-B 不混入：

- subprocess timeout/output/process-tree cleanup；
- ExecutionAdapter；
- cancellation；
- token/cost/context/time budget；
- Workspace P1；
- CLI stdout/report/json 协议；
- M3 checkpoint store 或 Evidence schema 重构。

## 6. 后续 M2 顺序

### M2-C：ExecutionAdapter

依赖 M2-A/B。实现 Fake、NoIsolation、RestrictedSubprocess；minimal env、cwd、timeout、process-tree cleanup、cancellation、output limits、structured failure；不承诺 kernel isolation。

目标用例：`TC-SEC-005`–`007`、`TC-SEC-009`、`TC-TOOL-005/006`、`TC-RUN-013`。

### M2-D：Runtime Lifecycle、Budget、Cancellation

状态转换、lifecycle event、关键 checkpoint、统一 `RuntimeResult`、max steps/token/cost/context/time、provider-before-cancel、tool-during-cancel、tool-error policy、malformed Provider 结构化失败。

目标用例：`TC-RUN-001`–`013`，不含 P2 `TC-RUN-014`。

### M2-E：Workspace P1

UTF-8 byte-safe truncation、read limit、search file/byte/time budgets、binary/permission/file-disappeared 结构化结果。

目标用例：`TC-WS-004`–`006`。

### M2-F：CLI 核心

stdout 最终回答、stderr 进度、`--report`、`--json`、unsafe debug、稳定 exit code、workspace 错误 UX。

目标用例：`TC-CLI-001`–`006`。

### M2-G：Integrated Closeout

必须通过 `TC-RUN-001`–`013`、`TC-TOOL-001`–`007`、`TC-WS-004`–`006`、`TC-SEC-001`–`009`、`TC-CLI-001`–`006`；无裸 handler path；每次工具执行有 policy event；side-effect tool 有 recovery policy；transition 合法/非法类别覆盖 100%；Runtime 状态模块 branch coverage ≥95%；Active P1 Runtime/Tool/Security defect = 0；在 integrated `develop` 复跑 closeout。

## 7. M3–M6 摘要

### M3

checkpoint/evidence 分离；atomic save、fsync、locking、corruption、migration、optional encryption；three crash windows；ChangeManager conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider normalization、malformed schema、error mapping、retry/budget/size、request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 只允许 P0/P1 fix、测试稳定性、文档事实、release pipeline fix。最终 Gate 要求所有 P0/P1 `Verified`，Active P0/P1/S0/S1 = 0，测试/矩阵/构件/claim traceability 全部通过。任一 Gate 不满足，结论必须是 `No Release`。

## 8. 开发流程

### 第一优先：PR

1. 从最新 `develop` 创建 `agent/<scope>`；
2. 创建 Draft PR；
3. 补 tests、Traceability、文档和 CI；
4. 转 Ready；
5. CI 全绿后合入 `develop`；
6. Release Gate 全通过后才执行 `develop → master → tag`。

### 第二优先：异常直推 `develop`

仅当 PR 流程持续因环境、依赖、规则冲突或 GitHub 基础设施问题无法完成时使用。不得用于绕过失败测试、review 或安全门禁。

```text
<type>(<scope>): <变更说明>

## 问题原因
<PR 流程无法通过的真实根因>

## 技术债务
- <遗留问题>
```

必要时同步 `docs/TECH_DEBT.md`：

```text
[YYYY-MM-DD] 描述 | 遗留原因 | 状态
```

## 9. Definition of Done

- 实现符合 PRD Requirement；
- 对应 Test Case 自动化；
- happy/failure/adversarial/fault path 按风险覆盖；
- lint、type-check、tests、import、secret scan、traceability 全绿；
- 不通过 rerun 隐藏失败；
- public API、error code、schema、versioning 同步；
- README、PRD、architecture、Threat Model、Known Unknowns 按需同步；
- Traceability 写入实际 PR/Test/Evidence/Status/Blocker；
- 默认日志和 Evidence 无 key、prompt、response、reasoning、工具正文；
- PR 描述包含根因、设计、边界、风险、测试和回滚。

## 10. No-Go

workspace 外读写、密钥泄漏、artifact secret、重复高价值副作用、P0 失败/跳过、Registry/Policy/Adapter 绕过、checkpoint 状态不清、rollback handle 可伪造/跨 workspace、artifact 来源或 digest 不明、CI 只能靠 rerun、README 超过 Verified、降低断言或文档/测试/计划冲突，均必须暂停推进。

## 11. 新会话交接提示词

```text
你现在接手 GitHub 仓库 yuanchenglu/deepseek_runtime 的 Open-source Alpha Hardening 工作。

首先读取：
1. docs/roadmap/open-source-readiness-plan.md（v2.2.4）
2. docs/roadmap/m2-a-closeout.md
3. docs/product/PRD.md
4. docs/traceability/alpha-traceability.md
5. docs/testing/test-cases.md
6. docs/testing/test-plan.md
7. docs/security/threat-model.md
8. CONTRIBUTING.md

当前事实：
- develop：b012265c4f51238c97c26c22b76d1e5e043153dc（如 PR #15 已合入，直接读取最新 develop）
- M0：CLOSED
- M1：CLOSED
- M2-A：CLOSED
- M2-B：NEXT
- M2-A 实施 PR #14：merged
- M2-A merge commit：b012265c4f51238c97c26c22b76d1e5e043153dc
- Minimum CI run 106：PASS
- M1 P0 Gate run 56：PASS
- Release：NO RELEASE

先核对 PR #15 closeout 是否已完成；若未完成，完成 CI/review/merge。随后从最新 develop 创建 agent/m2-policy-approval 和 Draft PR。

M2-B 只处理 Policy 与 Approval：READ 默认 ALLOW、非 READ 默认 DENY、稳定规则优先级、ASK→ApprovalProvider、approve-once/session、deny、timeout、缺 provider fail-closed、安全摘要、decision/approval evidence、handler 仅在最终 allow 后执行。

目标用例：TC-SEC-001–004、TC-SEC-008。不得混入 ExecutionAdapter、timeout/output enforcement、Budget、Cancellation、Workspace P1、CLI 输出协议或 M3。

流程：功能分支 → Draft PR → tests/Traceability/docs/CI → Ready → develop。禁止直接开发 master。保持 NO RELEASE。
```

## 12. 当前结论

- M0、M1、M2-A 已有合并态与可访问证据；
- PR #15 正在同步 M2-A closeout 的权威文档；
- closeout 合入后，立即从最新 `develop` 启动独立 M2-B Policy/Approval Draft PR；
- M2-B–M2-G、M3–M6 完成前保持 **NO RELEASE**。
