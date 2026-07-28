# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.9  
> 状态日期：2026-07-29  
> 计划状态：**Execution in progress — M0/M1/M2-A/M2-B/M2-C closed; M2-D in progress**  
> 已合入开发基线：`develop@45b7c448d437df9ced5b5776f017a008376dabbb`  
> 当前远程工作分支：`agent/m2-runtime-lifecycle`  
> 当前工作入口：Draft PR #20 `feat(runtime): establish M2-D lifecycle and budget path`  
> 本次核验 head：`13bc04415f1ae1b17eb1d220cffba8c3fcd23cad`  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将 DeepSeek Runtime 做到：边界真实、执行可控、恢复正确、证据可信、构件可验证，并发布首个可持续维护的 Open-source Alpha。

M0–M6 期间不通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 当前事实快照

- 当前容器没有本地 Git 工作树，也没有未提交、未 push 的本地文件；
- M2-D 的代码、测试、workflow、合同、worklog 和测试报告均已保存到远程分支 `agent/m2-runtime-lifecycle`；
- Draft PR #20 已存在并指向 `develop`，当前包含 16 个变更文件；
- 当前 PR head `13bc0441` 是“严格回归测试提交”，尚未包含对应生产修复；
- 因此当前精确 head 的 Minimum CI run 205 和 M2 Runtime Lifecycle Gate run 20 为失败；
- 同一 head 的 M1 P0 Gate run 149、M2 ExecutionAdapter Gate run 55 为成功；
- 最近一个四套代码门禁均成功的较早 head 是 `2d71808b3ae8963998416fc5eedbf8ece2d8fc52`：Minimum CI run 202、M1 P0 Gate run 146、M2 ExecutionAdapter Gate run 52、M2 Runtime Lifecycle Gate run 17；
- `2d71808b` 不包含后来增加的严格 approval checkpoint 回归，因此不能作为 PR #20 的最终验收 head；
- 不得通过删除测试、降低断言或只引用较早绿色 head 将 M2-D 标记为完成。

## 3. 总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | Workspace、rollback authorization、uncertain side effect 已验证 | PR #6–#10、PR #13、Gate run 33 |
| M2-A ToolRegistry 唯一入口 | **CLOSED** | Registry-only Runtime path 已合入 | PR #14、runs 106/56、PR #15 |
| M2-B Policy 与 Approval | **CLOSED** | Runtime tool call 强制经过 Policy/Approval | PR #16、runs 129/77、PR #17 |
| M2-C ExecutionAdapter | **CLOSED** | 统一 Adapter、进程资源控制和三平台专项 Gate 已合入 | PR #18、runs 165/111/15、PR #19 |
| M2-D Runtime Lifecycle、Budget、Cancellation | **IN PROGRESS** | 大部分实现已在 PR #20；存在 1 个已知 approval checkpoint blocker | PR #20、head `13bc0441` |
| M2-E Workspace P1 | **NOT STARTED** | read/search byte/file/time 与结构化 I/O 未完成 | `WS-003`–`005` |
| M2-F CLI 核心 | **NOT STARTED** | stdout/report/json/exit-code 协议未完成 | `CLI-001`–`006` |
| M2-G Integrated Closeout | **NOT STARTED** | M2 全部 P1 尚未综合验收 | Traceability |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | 已有部分合同，但 durable recovery/evidence gate 未建立 | Traceability |
| M4 Provider、配置与协议收口 | **NOT STARTED** | Provider normalization/streaming/config 未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

### 3.1 进度判断

不使用单一百分比冒充发布就绪度。按能力域判断：

- 基线、治理和 P0 安全合同：已完成；
- M2 Runtime/Tool/Security 主链：A/B/C 已关闭，D 接近代码完成，E/F/G 未开始；
- M3 durable recovery/evidence、M4 Provider、M5 packaging/release matrix、M6 RC：仍是主要未完成工作；
- 以首个 Alpha 的全部 M0–M6 Gate 估算，当前整体发布就绪度约为 **35%–40%**；该估算只用于资源规划，不替代 Requirement/Test/Evidence Gate；
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

### 4.3 M2-A：ToolRegistry

- 实施 PR #14，closeout PR #15；
- merge `b012265c4f51238c97c26c22b76d1e5e043153dc`；
- final Minimum CI run 106、M1 P0 Gate run 56 PASS；
- retained failures：runs 92、98；
- `RUN-003`、`RUN-009`、`TOOL-001`–`004`、`TOOL-007` Verified。

### 4.4 M2-B：Policy 与 Approval

- 实施 PR #16，closeout PR #17；
- merge `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- final Minimum CI run 129、M1 P0 Gate run 77 PASS；
- retained failures：runs 114、122、127；
- READ 默认 ALLOW，非 READ 默认 DENY；
- last-match policy precedence、missing-path、approve-once/session、deny、timeout、unavailable fail-closed 已验证；
- `SEC-001`、`SEC-002`、`SEC-004` Verified；`SEC-003` 因 durable checkpoint/resume 保持 Partial。

### 4.5 M2-C：ExecutionAdapter

- 实施 PR #18，closeout PR #19；
- merge `7793a10152a49fb815aac667906080a4e1a39920`；closeout merge `45b7c448d437df9ced5b5776f017a008376dabbb`；
- retained failure：Minimum CI run 144；
- final Minimum CI run 165：PASS；
- final M1 P0 Gate run 111：Linux/macOS/Windows PASS；
- M2 ExecutionAdapter Gate run 15：三平台各 36/36，总计 108/108；
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

## 5. M2-D 当前实施状态

### 5.1 已在远程分支实现

- `LifecycleEvent`、`LifecycleTrace` 与 transition manifest 一致性检查；
- `TOOL_RUNNING → CANCELLED` 合法转换；
- Provider round / tool batch 粒度的单一生产 lifecycle；
- private `RecoverableCheckpoint` handoff；
- `PROVIDER_COMPLETED` checkpoint 包含刚收到的 assistant message；
- ASK 在 ApprovalProvider I/O 前保存 `approval_outcome="pending"`；
- Provider 调用前 cancellation 不发送请求；
- pure tool cancellation → `CANCELLED`；
- side-effect cancellation/未知结果 → `TOOL_SIDE_EFFECT_UNCERTAIN`；
- step/token/USD cost/context/time budgets；
- unknown usage/cost 保持 unknown；
- `ToolErrorPolicy.CONTINUE/TERMINATE`；
- malformed Provider 支持范围内返回结构化 `RuntimeResult`；
- public usage evidence 数值白名单；
- side-effect success private structural receipt；
- UTF-8 bytes checkpoint 兼容；
- 三平台 M2 Runtime Lifecycle focused Gate；
- Runtime lifecycle 合同、worklog 与测试报告。

### 5.2 已保留失败证据

- Minimum CI run 184：首轮 lifecycle integration unit failures；
- M2 Runtime Lifecycle Gate run 1：manifest、receipt、UTF-8 checkpoint、旧 cancellation 语义等失败；
- Minimum CI run 199 / M2 Gate run 13：全量兼容诊断阶段失败；
- M2 Gate run 16：严格 review 暴露同一 batch 后续 ASK 的最终 approval checkpoint 时序缺口；
- 当前 head 的 Minimum CI run 205 / M2 Gate run 20：新增回归测试已提交，但对应生产修复尚未提交。

失败记录不得删除、重跑覆盖或从 PR 描述中隐去。

### 5.3 当前唯一已知 blocker

测试：

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

问题：同一 Provider response 含多个需 ASK 的 tool call 时，第二个 call 的 `pending` checkpoint 已 handoff；ApprovalProvider 返回 `approve-once` 后，Runtime 在进入 Adapter 前没有再次 handoff 已解析的 approval outcome 与该 call 的 `TOOL_RUNNING` 状态。

建议最小修复：

1. 保留当前测试，不降低断言；
2. 在 `src/deepseek_runtime/runtime.py` 的 `on_authorized()` 中：
   - 先将当前 `checkpoint_call.state` 设为 `TOOL_RUNNING`，`attempt_count=1`；
   - 当全局 lifecycle 已是 `TOOL_RUNNING` 时，调用 `handoff_current_state(step)`；
   - 此时 `AuthorizationSession.authorize()` 已把 pending event 原位替换为最终 approval outcome；
   - handoff 完成后才允许进入 `ExecutionAdapter.execute()`；
3. 补充 deny/timeout/unavailable 最终 outcome 是否同样需要 resolved checkpoint 的严格测试；不得用“只处理 approve happy path”掩盖恢复窗口。

### 5.4 M2-D 完成条件

- [ ] 当前严格 approval checkpoint 回归通过；
- [ ] Minimum CI 在最终精确 head 成功；
- [ ] M1 P0 Gate 在最终精确 head 三平台成功；
- [ ] M2 ExecutionAdapter Gate 在最终精确 head 三平台成功；
- [ ] M2 Runtime Lifecycle Gate 在最终精确 head 三平台成功；
- [ ] 获取 M2-D artifact ID、digest、tests_run、failures/errors/skipped 分母；
- [ ] 更新 PR #20 描述，写入 retained failures、最终 head、run IDs 与明确排除项；
- [ ] 核验 changed files 无 M2-E/M2-F/M3/M4/M5 范围漂移；
- [ ] 核验 review threads、unresolved P0/S0/S1；
- [ ] Draft → Ready；
- [ ] squash merge PR #20 到 `develop`；
- [ ] 新建 docs-only M2-D closeout PR，将合入态 Requirement 提升为 Verified，并将 M2-E 标记为 NEXT。

## 6. M2-D 明确不做

- Workspace read/search P1 budgets（M2-E）；
- CLI stdout/report/json/exit-code 协议（M2-F）；
- Provider streaming、retry、body-size、完整 arbitrary JSON normalization 与 in-flight cancellation（M4）；
- durable encrypted checkpoint store、migration、locking（M3）；
- ChangeManager、Evidence totality/canonical redesign（M3）；
- container/VM/kernel sandbox；
- Packaging、release matrix、`master`、tag 或 release。

## 7. 后续顺序

### M2-E：Workspace P1

UTF-8 byte-safe truncation、read limit、search file/byte/time budgets、binary/permission/file-disappeared 结构化结果。目标用例：`TC-WS-004`–`006`。

### M2-F：CLI 核心

stdout 最终回答、stderr 进度、`--report`、`--json`、unsafe debug、稳定 exit code、workspace 错误 UX。目标用例：`TC-CLI-001`–`006`。

### M2-G：Integrated Closeout

必须通过 `TC-RUN-001`–`013`、`TC-TOOL-001`–`007`、`TC-WS-004`–`006`、`TC-SEC-001`–`009`、`TC-CLI-001`–`006`；无 Registry/Policy/Approval/Adapter bypass；transition 合法/非法类别覆盖 100%；Active P1 Runtime/Tool/Security defect = 0；在 integrated `develop` 复跑 closeout。

### M3

checkpoint/evidence 分离；atomic save、fsync、locking、corruption、migration、optional encryption；three crash windows；ChangeManager conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider normalization、malformed schema、error mapping、retry/budget/size、request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 只允许 P0/P1 fix、测试稳定性、文档事实和 release pipeline fix。最终 Gate 要求所有 P0/P1 `Verified`，Active P0/P1/S0/S1 = 0，测试/矩阵/构件/claim traceability 全部通过。任一 Gate 不满足，结论必须是 `NO RELEASE`。

## 8. 开发与合入纪律

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

异常直推 `develop` 只作为 PR 流程持续不可用时的兜底。直推 commit 必须写明“问题原因”和“技术债务”，并在 `docs/TECH_DEBT.md` 或 commit body 留痕。

禁止：

- 在 `master` 直接开发；
- 用 rerun 覆盖失败证据；
- 降低 Pyright/Ruff/test assertion；
- 用 cast、fallback 或文档措辞掩盖真实合同错误；
- 将后续里程碑工作混入当前 PR；
- 在 M6 Gate 前发布、打正式 tag 或把 `master` 当开发分支。

## 9. 新会话交接

完整交接提示词保存在：

```text
docs/roadmap/m2-d-session-handoff.md
```

新会话必须先从远程读取 PR #20、当前 branch head、changed files、CI runs 和本计划，不得依赖旧会话的本地容器状态。

当前结论：**M2-D IN PROGRESS；PR #20 未合入；NO RELEASE。**
