# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.2  
> 状态日期：2026-07-28  
> 计划状态：**Execution in progress — M0/M1 closed, M2 active**  
> 当前开发基线：`develop@64b938fbd861a0157c800191653bbc70b128901e`  
> 当前工作分支：`agent/m2-tool-registry`  
> 当前工作入口：Draft PR #14（动态 head 以 PR 页面为准）  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将 DeepSeek Runtime 做到：边界真实、执行可控、恢复正确、证据可信、构件可验证，并发布首个可持续维护的 Open-source Alpha。

M0–M6 期间不通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | M1 范围内 Workspace、rollback authorization、uncertain side effect 已验证 | PR #6–#10、PR #13、Gate runs 33/40 |
| M2 Runtime 与 Security 闭环 | **IN PROGRESS / CI RED** | ToolRegistry 首个切片已远程保存；当前存在 1 个真实 Pyright blocker | Draft PR #14、Minimum CI run 92 |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | P1 Requirement 仍有 Blocked/Partial | Traceability |
| M4 Provider、配置与 CLI 协议收口 | **NOT STARTED** | Provider、streaming、配置和 CLI 稳定合同未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

客观结论：

- 7 个里程碑中，2 个已关闭，1 个执行中，4 个未开始；
- 里程碑规模不等，不应把 2/7 直接解释为发布完成度；
- M1 的 P0 范围已关闭，但 M2–M5 仍有大量 P1 Requirement 未 `Verified`；
- 当前必须保持 **NO RELEASE**。

## 3. 已完成结果

### M0

- PRD、测试、Traceability、Threat Model 和路线图的权威顺序已确定；
- LICENSE、NOTICE、CONTRIBUTING、SECURITY、SUPPORT 和治理文档已建立；
- Minimum CI 覆盖 Ruff 关键规则、Pyright、unit tests、import、secret scan 和文档追踪；
- 开发流程明确为“PR 优先，直推 `develop` 仅作为异常兜底”；
- PR #13 完成 M0 当前策略同步。

### M1

- Error、Runtime State、Checkpoint/Evidence、ToolSpec、RecoveryPolicy、RollbackHandle 和 ChangeJournal 最小合同已冻结；
- Workspace read/search 统一经过 `WorkspaceResolver`；
- symlink 和 Windows reparse-point/junction P0 场景进入固定 Gate；
- rollback 使用 opaque handle + durable ChangeJournal；
- forged、expired、cross-workspace、external-path、stale rollback 有结构化拒绝；
- side-effect crash window 进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不自动盲目重试；
- PR #6 → #7 → #8 → #9 → #10 已按顺序合入 `develop`；
- PR #13 完成 integrated closeout 并合入 `develop@64b938f`。

M1 证据：

- Run 33：Linux/macOS/Windows 各 140/140，总计 420/420，0 failed/skipped/N/A；
- Windows `TC-WS-003` 实际执行 junction/reparse-point 测试；
- artifacts：Linux `8676238220`、macOS `8676237125`、Windows `8676241048`；
- 最终精确内容：Minimum CI run 89 PASS，M1 P0 Gate run 40 三平台 PASS。

## 4. 当前 M2 工作现场

### 4.1 远程保存状态

当前不存在仅保存在临时容器中的未上传代码。

- 远程分支：`agent/m2-tool-registry`；
- 基线：`develop@64b938fbd861a0157c800191653bbc70b128901e`；
- Draft PR：#14 `feat: start M2 ToolRegistry production path`；
- PR 为 open + draft，不允许自动合并；
- 动态 head 应从 PR #14 获取，不在计划中写死；
- Run 92 的 CI evidence head：`517d0f72d97ba815656b8b883382d73c70741c36`；
- 当前代码变更涉及 4 个文件，路线图为第 5 个文件。

代码文件：

1. `src/deepseek_runtime/contracts/tools.py`
2. `src/deepseek_runtime/contracts/__init__.py`
3. `src/deepseek_runtime/__init__.py`
4. `src/deepseek_runtime/runtime.py`

### 4.2 已实现但尚未验收

- `ToolRegistry` 作为 `ToolSpec` 的生产集合；
- duplicate name、handler、risk、side-effect、limits、RecoveryPolicy 注册校验；
- JSON Schema Draft 2020-12 参数校验；
- Provider tool definitions 由 `ToolSpec` 生成；
- unknown tool → `TOOL_NOT_FOUND`；
- `str`、UTF-8 bytes、JSON-compatible result 确定性规范化；
- invalid result → `TOOL_RESULT_INVALID`；
- handler exception → `TOOL_EXECUTION_FAILED`；
- `DeepSeekRuntime.run()` 不再接受裸 `dict[str, handler]`；
- `read_file` 和 `search` 通过完整 `ToolSpec` 注册。

### 4.3 当前 CI 真实结果

PR #14 的 Run 92 evidence head：

- M1 P0 Gate run 42：**PASS**；
- Minimum CI run 92：**FAIL**；
- auto-merge 失败属于 Draft PR 无法启用自动合并，不是产品 Gate；
- Minimum CI 在 type-check 失败后跳过 unit tests、import、secret scan 和 docs traceability。

唯一 Pyright error：

```text
src/deepseek_runtime/cli.py:93
Argument of type "ToolRegistry | dict[Unknown, Unknown]"
cannot be assigned to parameter "tools" of type "ToolRegistry | None"
in function "run".
Rule: reportArgumentType
```

根因：Runtime API 已收紧为 `ToolRegistry | None`，但 `cli.py` 仍保留会产生 `{}` fallback 的旧调用方式。该问题属于实现迁移未完成，不是 CI 环境问题；禁止通过忽略 Pyright、降低规则或直推 `develop` 绕过。

### 4.4 PR #14 完成条件

PR #14 **不得合并**，直到：

- 修复 `cli.py` 的 `ToolRegistry | dict` 类型错误；
- 自动化 `TC-TOOL-001`–`004`；
- 自动化 `TC-RUN-004`、`TC-RUN-009`、`TC-RUN-011`；
- 增加 malformed tool-call JSON、function shape、call ID、exception boundary 测试；
- 审查旧 API 和 CLI 兼容性；
- 更新 Traceability 的 PR、Test、Evidence、Status、Blocker；
- 按需更新 README、architecture 和 contracts；
- 最终精确内容 Minimum CI 全绿；
- 完成严格 Code Review 后才从 Draft 转 Ready。

### 4.5 PR #14 明确不做

- Policy；
- ApprovalProvider；
- ExecutionAdapter；
- timeout/output-size 实际 enforcement；
- process-tree cleanup；
- cancellation；
- token/cost/context/time budgets；
- checkpoint timing；
- CLI 输出协议重构；
- M3 checkpoint store 或 Evidence 重构。

## 5. M2 执行顺序

### M2-A：ToolRegistry 唯一入口（当前 PR #14）

完成条件：Runtime 只接受 `ToolRegistry`；内建工具通过 `ToolSpec`；Provider schema 从 Registry 生成；工具错误结构化；`TC-TOOL-001`–`004` 与 `TC-RUN-004/009/011` 自动化；无第二套裸 handler production path；Traceability/CI 完整。

### M2-B：Policy 与 Approval

依赖 M2-A。每次工具执行有 policy decision；READ 默认 ALLOW、非 READ 默认 DENY；规则优先级稳定；ASK 进入 ApprovalProvider；approve-once/session、deny、timeout；安全摘要；decision/approval 进入 checkpoint/evidence。

目标用例：`TC-SEC-001`–`004`、`TC-SEC-008`。

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

## 6. M3–M6 摘要

### M3

checkpoint/evidence 分离；atomic save、fsync、locking、corruption、migration、optional encryption；three crash windows；ChangeManager conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

Exit Gate：`TC-CHG-003`–`011`、`TC-SES-001`–`011`、`TC-EVD-001`–`007`、`TC-OBS-001`–`007`。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider normalization、malformed schema、error mapping、retry/budget/size、request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 只允许 P0/P1 fix、测试稳定性、文档事实、release pipeline fix。最终 Gate 要求所有 P0/P1 `Verified`，Active P0/P1/S0/S1 = 0，测试/矩阵/构件/claim traceability 全部通过。任一 Gate 不满足，结论必须是 `No Release`。

## 7. 开发流程

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

## 8. Definition of Done

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

## 9. No-Go

workspace 外读写、密钥泄漏、artifact secret、重复高价值副作用、P0 失败/跳过、Registry/Policy/Adapter 绕过、checkpoint 状态不清、rollback handle 可伪造/跨 workspace、artifact 来源或 digest 不明、CI 只能靠 rerun、README 超过 Verified、降低断言或文档/测试/计划冲突，均必须暂停推进。

## 10. 新会话交接提示词

```text
你现在接手 GitHub 仓库 yuanchenglu/deepseek_runtime 的 Open-source Alpha Hardening 工作。

先读取：
1. PR #14 分支的 docs/roadmap/open-source-readiness-plan.md（v2.2.2）
2. docs/product/PRD.md
3. docs/traceability/alpha-traceability.md
4. docs/testing/test-cases.md
5. docs/testing/test-plan.md
6. docs/security/threat-model.md
7. CONTRIBUTING.md

当前状态：
- develop：64b938fbd861a0157c800191653bbc70b128901e
- M0：CLOSED
- M1：CLOSED
- M2：IN PROGRESS / CI RED
- 分支：agent/m2-tool-registry
- Draft PR：#14，feat: start M2 ToolRegistry production path
- 动态 head：请直接读取 PR #14，不要依赖静态 SHA
- Run 92 evidence head：517d0f72d97ba815656b8b883382d73c70741c36
- Release：NO RELEASE

PR #14 已实现 ToolRegistry/ToolSpec 注册合同、JSON Schema 参数校验、Provider definitions、result normalization、Runtime 仅接受 ToolRegistry、Workspace 内建 ToolSpec，但尚未验收。

当前 CI：
- M1 P0 Gate run 42：PASS
- Minimum CI run 92：FAIL
- 唯一 Pyright error：src/deepseek_runtime/cli.py:93 仍可能把 ToolRegistry | dict 传给只接受 ToolRegistry | None 的 Runtime.run。
- type-check 失败后 unit tests/import/secret scan/docs gate 被跳过。
- 这是代码迁移未完成，不是环境问题；禁止降低 Pyright 或直推 develop 绕过。

立即执行：
1. 拉取并严格审查 PR #14 完整 diff。
2. 修复 cli.py：无 workspace tools 时使用 ToolRegistry() 或 None，不能产生 dict fallback，并审查 CLI 行为兼容性。
3. 运行 Pyright，确认 errorCount=0。
4. 补 TC-TOOL-001–004、TC-RUN-004/009/011，以及 malformed tool-call/exception boundary 测试。
5. 测试暴露实现问题时修实现，不得降低断言。
6. 保持 PR #14 范围，不混入 Policy、Approval、ExecutionAdapter、Budget、Cancellation、CLI 输出协议或 M3。
7. 更新 Traceability 和必要文档。
8. 运行最终精确内容 Minimum CI；保留失败证据，不用 rerun 掩盖问题。
9. 严格 Code Review 后再转 Ready；CI 全绿才合入 develop。
10. 合入后更新路线图，再开始 M2-B Policy 与 Approval。

流程：功能分支 → Draft PR → tests/CI → Ready → develop。只有 PR 流程持续因环境或基础设施问题无法完成，才允许直推 develop；直推 commit 必须包含“## 问题原因”和“## 技术债务”。禁止直接开发 master。

请持续执行，不要停在分析或计划阶段；保持 NO RELEASE，直到 M6 最终 Gate 明确允许发布。
```

## 11. 当前结论

- M0/M1 已有合并态、三平台和 closeout 证据；
- M2 已开始，Draft PR #14 和全部当前代码/文档均已保存在远程；
- PR #14 当前因 1 个真实 Pyright 错误处于 CI RED；
- 下一会话从 CLI 类型迁移、测试和 CI 收口继续；
- M2–M6 完成前保持 **NO RELEASE**。
