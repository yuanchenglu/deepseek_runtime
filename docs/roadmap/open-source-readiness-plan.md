# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.5  
> 状态日期：2026-07-28  
> 计划状态：**Execution in progress — M0/M1/M2-A/M2-B closed, M2-C next**  
> 当前开发基线：`develop@f8a5799ae50221a2830f3d0b2ed19f86852fccf4`  
> 当前工作分支：`agent/m2-b-closeout`  
> 当前工作入口：Draft PR #17 `docs(roadmap): close M2-B and hand off M2-C`  
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
| M2-A ToolRegistry 唯一入口 | **CLOSED** | Registry-only Runtime path 已合入 `develop` | PR #14、runs 106/56、PR #15 |
| M2-B Policy 与 Approval | **CLOSED** | 每个受支持 Runtime tool call 强制经过 Policy/Approval | PR #16、runs 129/77、merge `f8a5799a` |
| M2-C ExecutionAdapter | **NEXT** | Adapter 合同、子进程资源控制和清理尚未实现 | `SEC-006`–`008`、`TOOL-005`、`RUN-006` |
| M2-D–M2-G | **NOT STARTED** | lifecycle/budget/cancellation、Workspace P1、CLI、integrated closeout 未完成 | Traceability |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | P1 Requirement 仍有 Blocked/Partial | Traceability |
| M4 Provider、配置与 CLI 协议收口 | **NOT STARTED** | Provider、streaming、配置和稳定协议未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

客观结论：

- M0、M1、M2-A、M2-B 已关闭；M2 总里程碑仍未关闭；
- M2-B 只关闭内存中的生产授权链，不代表 ExecutionAdapter、durable checkpoint、budget 或 cancellation 已完成；
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
- 最终精确内容：Minimum CI run 89 PASS，M1 P0 Gate run 40 三平台 PASS。

### M2-A：ToolRegistry

PR #14 已 squash 合入 `develop`，PR #15 完成 docs-only closeout。

合并态：

- PR head：`a51d5b297d8233c654cc1569c5fe73b9730c28b6`；
- merge commit：`b012265c4f51238c97c26c22b76d1e5e043153dc`；
- Minimum CI run 106：PASS；
- M1 P0 Gate run 56：三平台 PASS；
- 严格 Code Review：未解决 P0/S0/S1 = 0；
- closeout：`docs/roadmap/m2-a-closeout.md`。

已关闭能力：

- `ToolRegistry` 是 Runtime 的生产工具集合；
- `DeepSeekRuntime.run()` 只接受 `ToolRegistry | None`；
- 不保留裸 `{}` 或 `dict[str, handler]` Runtime fallback；
- ToolSpec 注册、JSON Schema 参数校验、Provider definition、结果规范化和 malformed tool-call 边界已建立。

已 `Verified`：

- `RUN-003`、`RUN-009`；
- `TOOL-001`–`004`、`TOOL-007`。

保留失败证据：Minimum CI runs 92、98。

### M2-B：Policy 与 Approval

PR #16 `feat(security): enforce M2-B policy and approval path` 已 squash 合入 `develop`。

合并态：

- 最终 PR head：`7e2913204b89164ba10ec3c43c03ab7bd69435af`；
- merge commit：`f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- Minimum CI run 129：PASS；
- M1 P0 Gate run 77：Linux/macOS/Windows 全部 PASS；
- 严格 Code Review：未解决 P0/S0/S1 = 0；
- closeout：`docs/roadmap/m2-b-closeout.md`。

生产调用链：

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider（仅 ASK）
→ handler
→ result normalization
```

已关闭能力：

- READ 默认 `ALLOW`，非 READ 默认 `DENY`；
- 规则按声明顺序确定性执行，保留既有 last-match precedence；
- 缺失 path 不匹配具体 path glob；
- approve-once、exact-request approve-session、deny、timeout；
- ASK 缺失 Provider、Provider exception、invalid outcome 均 fail-closed；
- denial/approval failure 不执行 handler；
- authorization event 进入 Runtime evidence，并可无转换写入 `RecoverableCheckpoint.approvals`；
- approval summary、public error、evidence 和 policy audit 不保留参数值、正文、原始路径或命令正文；
- 直接 Policy DENY 与 ASK 后人工 DENY 的 audit 语义分离。

Requirement 状态：

- `SEC-001`：Verified；
- `SEC-002`：Verified；
- `SEC-004`：Verified；
- `SEC-003`：Partial，durable checkpoint timing/resume/migration 仍属 M2-D/M3；
- `SEC-009`：Partial，Adapter 子进程环境和错误输出面仍属 M2-C。

保留失败证据：

1. run 114：ErrorCode/schema mismatch 导致 Pyright 失败；
2. run 122：错误改变 Policy precedence 导致 unit regression；
3. run 127：直接 Policy DENY 被错误记录为人工审批拒绝。

三次失败均通过修复实现/合同和补回归测试解决，未 rerun 掩盖、未降低规则或断言。

## 4. 当前 closeout 工作现场

PR #17 只同步 PR #16 合并后的事实状态：

1. 新增 `docs/roadmap/m2-b-closeout.md`；
2. 更新本路线图为 v2.2.5；
3. 更新 `docs/traceability/alpha-traceability.md` 为 M2-B merged 状态；
4. 更新 Threat Model 的实施基线和剩余边界；
5. 更新 `README.md`、`README_en.md` 与 `docs/INDEX.md`；
6. 不修改生产代码；
7. 不实现 M2-C 功能。

PR #17 完成条件：

- [x] PR #16、merge commit、失败与成功 CI evidence 写入 closeout；
- [ ] Requirement 状态与 Blocker 同步；
- [ ] 双语 README 与 Threat Model 同步；
- [ ] 文档索引同步；
- [ ] Minimum CI 全绿；
- [ ] M1 P0 Gate 全绿；
- [ ] 严格文档 review；
- [ ] Ready 后合入 `develop`。

## 5. M2-C：ExecutionAdapter

### 5.1 目标

M2-C 必须建立唯一、可替换、可测试的执行边界，使 Runtime 不再直接把受授权工具实现等同于无限制宿主执行：

```text
authorized tool request
→ ExecutionAdapter
→ bounded execution
→ structured execution result/error
→ Runtime normalization
```

### 5.2 最小合同

1. 定义 `ExecutionAdapter` Protocol/ABC；
2. 提供 deterministic Fake Adapter；
3. 提供明确标注风险的 `NoIsolationLocalAdapter`；
4. 提供 `RestrictedSubprocessAdapter`，但不得称为 OS sandbox；
5. 子进程使用最小环境，不继承 DeepSeek API Key、token、authorization 或任意宿主 secret；
6. cwd 必须显式且经过 workspace containment；
7. `timeout_seconds` 必须实际 enforcement；
8. stdout/stderr 使用 byte-size limit，不能只按字符数；
9. timeout/cancel 后必须清理 process tree；
10. 返回 code、stdout、stderr、truncated、timed_out、cancelled 和结构化错误；
11. Adapter exception 不泄露 secret 或任意私有异常正文；
12. Runtime 所有需要 Adapter 的生产工具不得绕过该边界。

### 5.3 目标 Requirement/Test

- `SEC-006` / `TC-SEC-005`：minimal child environment；
- `SEC-007` / `TC-SEC-006`：timeout 后 process-tree cleanup；
- `SEC-008` / `TC-SEC-009`：Adapter 合同与非隔离声明；
- `SEC-009` / `TC-SEC-008`：Adapter 错误/输出 secret marker；
- `TOOL-005` / `TC-TOOL-005/006`：timeout 与 output-size enforcement；
- `RUN-006` / `TC-RUN-013`：cancellation handoff 的 Adapter 接口准备。

### 5.4 明确不做

M2-C 不混入：

- Runtime 全状态机重构；
- token/cost/context/time budgets；
- durable checkpoint timing/store；
- Workspace read/search P1 budgets；
- CLI stdout/report/json 协议；
- Provider streaming/retry；
- M3 Evidence 重构；
- container、VM、seccomp、Seatbelt、Job Object 等内核隔离承诺。

### 5.5 分支与 PR

PR #17 合入后，从最新 `develop` 创建：

```text
agent/m2-execution-adapter
```

先开 Draft PR，再按“合同 → Fake → NoIsolation → RestrictedSubprocess → Runtime 接入 → 测试/Traceability/docs → CI → review”顺序推进。

## 6. 后续 M2 顺序

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

必须通过 `TC-RUN-001`–`013`、`TC-TOOL-001`–`007`、`TC-WS-004`–`006`、`TC-SEC-001`–`009`、`TC-CLI-001`–`006`；无裸 handler/Adapter bypass；每次工具执行有 policy event；side-effect tool 有 recovery policy；transition 合法/非法类别覆盖 100%；Runtime 状态模块 branch coverage ≥95%；Active P1 Runtime/Tool/Security defect = 0；在 integrated `develop` 复跑 closeout。

## 7. M3–M6 摘要

### M3

checkpoint/evidence 分离；atomic save、fsync、locking、corruption、migration、optional encryption；three crash windows；ChangeManager conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider normalization、malformed schema、error mapping、retry/budget/size、request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 只允许 P0/P1 fix、测试稳定性、文档事实、release pipeline fix。最终 Gate 要求所有 P0/P1 `Verified`，Active P0/P1/S0/S1 = 0，测试/矩阵/构件/claim traceability 全部通过。任一 Gate 不满足，结论必须是 `No Release`。

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
- 用 cast 或 fallback 掩盖真实合同错误；
- 将后续里程碑工作混入当前 PR；
- 在 M6 Gate 前发布、打正式 tag 或把 `master` 当开发分支。

当前结论：**NO RELEASE**。
