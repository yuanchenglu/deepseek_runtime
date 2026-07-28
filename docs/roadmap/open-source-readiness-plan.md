# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.1  
> 状态日期：2026-07-28  
> 计划状态：**Execution in progress — M0/M1 closed, M2 active**  
> 当前开发基线：`develop@64b938fbd861a0157c800191653bbc70b128901e`  
> 当前工作分支：`agent/m2-tool-registry`  
> 当前工作 PR：Draft PR #14  
> 当前远程 head：`517d0f72d97ba815656b8b883382d73c70741c36`  
> 发布分支：`master`  
> 发布结论：**NO RELEASE**

## 1. 唯一目标

以最少新增功能，将现有 DeepSeek Runtime 做到：

- 产品边界真实；
- 工具执行不可绕过治理入口；
- 恢复和副作用语义正确；
- Evidence、测试和构件证据可信；
- Linux、macOS、Windows 上可复现；
- 首个 Open-source Alpha 可以持续维护，而不是一次性演示。

本计划不是功能扩张路线图。M0–M6 期间禁止通过新增 MCP、Skills、Multi-Agent、RAG、IDE、Desktop、Hosted API、多 Provider 或 Workflow DSL 掩盖 Runtime、安全、恢复和发布工程缺陷。

## 2. 当前总体进展

| Milestone | 状态 | 当前结论 | 主要证据 |
| --- | --- | --- | --- |
| M0 基线、治理、Traceability、最小 CI | **CLOSED** | 单一事实源、治理和最小 CI 已建立 | PR #1–#4、M0 closeout、PR #13 |
| M1 核心合同冻结与全部 P0 关闭 | **CLOSED** | Workspace、rollback authorization、uncertain side effect 的 M1 P0 范围已验证 | PR #6–#10、PR #13、M1 P0 Gate runs 33/40 |
| M2 Runtime 与 Security 闭环 | **IN PROGRESS / CI RED** | ToolRegistry 首个切片已远程保存；当前有 1 个真实 Pyright blocker | Draft PR #14、Minimum CI run 92 |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | 只存在 M1 合同和部分原语，不满足 M3 Gate | Traceability |
| M4 Provider、配置与 CLI 协议收口 | **NOT STARTED** | Provider normalization、streaming、配置和 CLI 稳定合同未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打新 tag | Release Gate |

当前可客观表述为：

- 7 个里程碑中，2 个已正式关闭；
- 1 个正在执行；
- 4 个尚未开始；
- 这不等价于“发布完成度 28.6%”，因为各里程碑规模和风险权重不同；
- M1 的 P0 范围已关闭，但大量 M2–M5 P1 Requirement 仍未 `Verified`；
- 当前仍为 **NO RELEASE**。

## 3. 已完成的关键结果

### 3.1 M0

- PRD、测试、Traceability、Threat Model 和路线图的权威顺序已确定；
- Apache-2.0 LICENSE、NOTICE、CONTRIBUTING、SECURITY、SUPPORT 和治理文档已建立；
- Minimum CI 已覆盖 Ruff 关键规则、Pyright、unit tests、import、secret scan 和文档追踪检查；
- 开发流程已明确为“PR 优先，直推 `develop` 仅作为异常兜底”；
- PR #13 按当前真实分支策略完成 M0 状态同步。

### 3.2 M1

- Error、Runtime State、Checkpoint/Evidence、ToolSpec、RecoveryPolicy、RollbackHandle 和 ChangeJournal 最小合同已冻结；
- Workspace read/search 已统一经过 `WorkspaceResolver`；
- symlink 和 Windows reparse-point/junction P0 场景已纳入固定 Gate；
- caller-controlled rollback payload 已替换为 opaque handle + durable ChangeJournal；
- forged、expired、cross-workspace、external-path 和 stale rollback 有结构化拒绝路径；
- side-effect crash window 已进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不再自动盲目重试；
- PR #6 → #7 → #8 → #9 → #10 已按顺序合入 `develop`；
- PR #13 完成集成态 closeout 并合入 `develop@64b938f`。

M1 首次集成态证据：

- Minimum CI run 82：PASS；
- M1 P0 Gate run 33：PASS；
- Linux/macOS/Windows：各 140/140；
- 总计：420/420；
- failed/skipped/N/A：0/0/0；
- Windows `TC-WS-003` 实际执行 junction/reparse-point 测试；
- artifacts：Linux `8676238220`、macOS `8676237125`、Windows `8676241048`。

最终精确内容校验：

- Minimum CI run 89：PASS；
- M1 P0 Gate run 40：三平台全部 PASS。

## 4. 当前 M2 工作现场

### 4.1 远程保存状态

当前不存在仅保存在临时容器中的未上传代码。

- 远程分支：`agent/m2-tool-registry`；
- 基线：`develop@64b938fbd861a0157c800191653bbc70b128901e`；
- 当前远程 head：`517d0f72d97ba815656b8b883382d73c70741c36`；
- Draft PR：#14 `feat: start M2 ToolRegistry production path`；
- PR 当前为 open + draft，不允许自动合并；
- 当前共 5 commits、5 changed files；
- 其中代码净变更为 4 个文件，另 1 个文件是本路线图。

代码文件：

1. `src/deepseek_runtime/contracts/tools.py`
2. `src/deepseek_runtime/contracts/__init__.py`
3. `src/deepseek_runtime/__init__.py`
4. `src/deepseek_runtime/runtime.py`

### 4.2 已实现但尚未验收

Draft PR #14 当前已实现：

- `ToolRegistry` 作为 `ToolSpec` 的唯一生产集合；
- duplicate name 拒绝；
- handler callable 校验；
- risk category 校验；
- side-effect、risk 与 `RecoveryPolicy` 一致性校验；
- timeout 和 output-size 注册期校验；
- JSON Schema Draft 2020-12 参数校验；
- Provider tool definitions 由 `ToolSpec` 生成；
- unknown tool 返回 `TOOL_NOT_FOUND`；
- handler 返回 `str`、UTF-8 bytes 或 JSON-compatible 值的确定性规范化；
- 非 UTF-8 bytes 和非 JSON-compatible result 返回 `TOOL_RESULT_INVALID`；
- handler exception 转为 `TOOL_EXECUTION_FAILED`；
- `DeepSeekRuntime.run()` 不再接受裸 `dict[str, handler]`；
- 内建 `read_file` 和 `search` 通过完整 `ToolSpec` 注册。

### 4.3 当前 CI 真实结果

PR #14 当前 head `517d0f72...`：

- M1 P0 Gate run 42：**PASS**；
- Minimum CI run 92：**FAIL**；
- auto-merge workflow：失败属于 Draft PR 下无法启用自动合并，不是产品 Gate；
- Minimum CI 在 `Enforce basic type check` 失败后，unit tests、import、secret scan 和 docs traceability 被跳过。

唯一 Pyright error：

```text
src/deepseek_runtime/cli.py:93
Argument of type "ToolRegistry | dict[Unknown, Unknown]"
cannot be assigned to parameter "tools" of type "ToolRegistry | None"
in function "run".
Rule: reportArgumentType
```

根因：

- Runtime API 已收紧为 `ToolRegistry | None`；
- `cli.py` 仍使用会产生 `{}` fallback 的旧调用方式；
- 类型系统正确识别出 CLI 仍可能传入裸 dict；
- 这是代码迁移未完成，不是 CI 环境问题；
- 不允许通过忽略 Pyright、降低规则或直推 `develop` 绕过。

下一步应先修正 CLI，使无 workspace tools 时使用空 `ToolRegistry()` 或 `None`，再运行完整 CI，并检查旧 CLI 行为测试是否需要更新。

### 4.4 PR #14 未完成项

PR #14 **不得合并**，直到以下事项全部完成：

- 修复 `cli.py` 的 `ToolRegistry | dict` 类型错误；
- 自动化 `TC-TOOL-001`：完整 ToolSpec 注册；
- 自动化 `TC-TOOL-002`：duplicate name；
- 自动化 `TC-TOOL-003`：required、additionalProperties、错误类型，且 handler 不执行；
- 自动化 `TC-TOOL-004`：side-effect 缺 risk/recovery/limits 拒绝；
- 自动化 `TC-RUN-004`：裸 handler production path 不存在；
- 自动化 `TC-RUN-009`：dict/list/bytes/object result 规范化或拒绝；
- 自动化 `TC-RUN-011`：unknown tool 不执行 handler；
- malformed tool-call JSON、function shape、call ID 和 exception boundary 用例；
- 旧 API 和 CLI 兼容性影响审查；
- Traceability 中实际 PR、Test、Evidence、Status、Blocker 更新；
- README/architecture/contract 文档按需同步；
- Minimum CI 对最终精确内容全绿；
- PR 从 Draft 转 Ready 前完成严格 Code Review。

### 4.5 明确不属于 PR #14 的范围

以下内容不得塞入 PR #14：

- Policy 决策；
- ApprovalProvider；
- ExecutionAdapter；
- 实际 timeout/output-size enforcement；
- process-tree cleanup；
- cancellation；
- token/cost/context/time budgets；
- checkpoint timing；
- CLI 输出协议重构；
- M3 checkpoint store 或 Evidence 重构。

## 5. M2 执行顺序

### M2-A：ToolRegistry 唯一入口

当前分支：`agent/m2-tool-registry`  
当前 PR：Draft PR #14

完成条件：

- Runtime 公共生产 API 只接受 `ToolRegistry`；
- 内建工具全部通过 `ToolSpec` 注册；
- Provider schema 由 Registry 生成；
- unknown tool、invalid argument、invalid result 和 handler exception 全部结构化；
- `TC-TOOL-001`–`004`、`TC-RUN-004/009/011` 全部自动化；
- 不存在第二套裸 handler production path；
- Traceability 和 CI 证据完整。

### M2-B：Policy 与 Approval

依赖：M2-A 合入。

交付：每次工具执行都有 policy decision；READ 默认 ALLOW、非 READ 默认 DENY；规则优先级稳定；ASK 进入 ApprovalProvider；approve-once、approve-session、deny、timeout；安全摘要；decision/approval 进入 checkpoint/evidence。

目标用例：`TC-SEC-001`–`004`、`TC-SEC-008`。

### M2-C：ExecutionAdapter

依赖：M2-A、M2-B。

交付：`FakeExecutionAdapter`、`NoIsolationLocalAdapter`、`RestrictedSubprocessAdapter`；minimal env、cwd、timeout、process-tree cleanup、cancellation、output limits、structured failure；不承诺 kernel isolation。

目标用例：`TC-SEC-005`–`007`、`TC-SEC-009`、`TC-TOOL-005/006`、`TC-RUN-013`。

### M2-D：Runtime Lifecycle、Budget 与 Cancellation

交付：状态转换、lifecycle event、关键 checkpoint、统一 `RuntimeResult`、max steps/token/cost/context/time、provider-before-cancel、tool-during-cancel、tool-error policy、malformed Provider 结构化失败。

目标用例：`TC-RUN-001`–`013`，不含 P2 `TC-RUN-014`。

### M2-E：Workspace P1

交付：UTF-8 byte-safe truncation、read limit、search file/byte/time budgets、binary/permission/file-disappeared 结构化结果。

目标用例：`TC-WS-004`–`006`。

### M2-F：CLI 核心

交付：stdout 最终回答、stderr 进度、`--report`、`--json`、unsafe debug、稳定 exit code、workspace 错误 UX。

目标用例：`TC-CLI-001`–`006`。

### M2-G：Integrated Closeout

必须满足：

- `TC-RUN-001`–`013`；
- `TC-TOOL-001`–`007`；
- `TC-WS-004`–`006`；
- `TC-SEC-001`–`009`；
- `TC-CLI-001`–`006`；
- 无裸 handler production path；
- 每次工具执行有 policy event；
- side-effect tool 有 recovery policy；
- transition manifest 合法/非法类别覆盖 100%；
- Runtime 状态模块 branch coverage ≥95%；
- Active P1 Runtime/Tool/Security defect = 0；
- 所有实现 PR 合入后在 integrated `develop` 复跑 closeout。

## 6. 后续里程碑摘要

### M3

checkpoint/evidence 分离；atomic save、directory fsync、locking、corruption detection、migration、optional encryption；three crash windows；ChangeManager lock/conflict/fsync/metadata；Evidence totality/canonical/redaction；Observability 正确性。

Exit Gate：`TC-CHG-003`–`011`、`TC-SES-001`–`011`、`TC-EVD-001`–`007`、`TC-OBS-001`–`007`。

### M4

Python 3.11–3.13 配置和版本单一真源；Provider arbitrary-root normalization、malformed schema、error mapping、retry/budget/size；request identity；真正 incremental SSE；CLI/doctor 协议稳定。

### M5

Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；完整 lint/type/test/coverage；tracked allowlist 构建 wheel/sdist；secret scan；digest/tamper；clean install；live smoke；治理和 release process。

### M6

RC 期间只允许 P0/P1 fix、测试稳定性、文档事实和 release pipeline 修复。

最终 Gate：所有 P0/P1 Requirement `Verified`；Active P0/P1/S0/S1 = 0；P0/P1 tests 100%；多平台 CI；clean artifacts；secret/digest/tamper；version/tag/artifact/manifest 一致；README claim traceability 100%；final report 明确 `Release`。

任一 Gate 不满足，结论必须是 `No Release`。

## 7. 开发流程规范

### 第一优先：PR 流程

1. 从最新 `develop` 创建 `agent/<scope>`；
2. 提交聚焦变更；
3. 创建 Draft PR；
4. 补齐测试、Traceability、文档和 CI；
5. 转 Ready；
6. CI 全绿后合入 `develop`；
7. Release Gate 全通过后才执行 `develop → master → tag`。

### 第二优先：异常直推 `develop`

仅当 PR 流程持续因环境、依赖、规则冲突或 GitHub 基础设施问题无法完成时使用。不得用于绕过失败测试、review 或安全门禁。

直推 commit 必须使用：

```text
<type>(<scope>): <变更说明>

## 问题原因
<说明 PR 流程无法通过的真实根因>

## 技术债务
- <遗留问题 1>
- <遗留问题 2>
```

技术债务也可写入 `docs/TECH_DEBT.md`：

```text
[YYYY-MM-DD] 描述 | 遗留原因 | 状态
```

## 8. Definition of Done

任何 PR 只有同时满足以下条件才能合入：

- 实现符合 PRD Requirement；
- 对应 Test Case 已自动化；
- happy、failure、adversarial/fault path 按风险覆盖；
- lint、type-check、tests、import、secret scan、traceability 全绿；
- 不通过 rerun 隐藏失败；
- public API 有 type hints；
- error code/schema/versioning 同步；
- README、PRD、architecture、Threat Model、Known Unknowns 按需同步；
- Traceability 写入实际 PR、Test、Evidence、Status、Blocker；
- 默认日志和 Evidence 不包含 key、prompt、response、reasoning 或工具正文；
- PR 描述包含问题、根因、设计、边界、风险、测试证据和回滚方式。

## 9. No-Go 条件

出现任一情况必须暂停推进：

- workspace 外读写、密钥泄漏、artifact secret 或重复高价值副作用；
- P0 测试失败、被跳过或 quarantine；
- Runtime 存在绕过 Registry/Policy/Adapter 的 production path；
- checkpoint 无法区分 failed、running、uncertain；
- rollback handle 可伪造、跨 workspace 或 restart 语义不明；
- artifact 不能证明来源或 digest；
- License/第三方来源不明确；
- CI 只能通过 rerun；
- README 宣称超过 Verified 能力；
- 为完成里程碑降低断言或删除安全用例；
- PRD、测试、Traceability 和路线图冲突。

## 10. 新会话交接提示词

以下内容可直接复制到新的 ChatGPT/Codex 会话：

```text
你现在接手 GitHub 仓库 yuanchenglu/deepseek_runtime 的 Open-source Alpha Hardening 工作。

请先读取并严格遵守：
1. develop 或 PR #14 分支中的 docs/roadmap/open-source-readiness-plan.md（v2.2.1，当前真实进度）
2. docs/product/PRD.md
3. docs/traceability/alpha-traceability.md
4. docs/testing/test-cases.md
5. docs/testing/test-plan.md
6. docs/security/threat-model.md
7. CONTRIBUTING.md

当前远程状态：
- develop：64b938fbd861a0157c800191653bbc70b128901e
- M0：CLOSED
- M1：CLOSED
- M2：IN PROGRESS / CI RED
- 功能分支：agent/m2-tool-registry
- Draft PR：#14，feat: start M2 ToolRegistry production path
- 当前远程 head：517d0f72d97ba815656b8b883382d73c70741c36
- 当前发布结论：NO RELEASE

PR #14 已实现但未验收：
- ToolRegistry/ToolSpec 注册合同
- duplicate、handler、risk、side-effect、limits、RecoveryPolicy 校验
- JSON Schema 参数校验
- Provider definitions 从 ToolSpec 生成
- result normalization
- DeepSeekRuntime.run() 只接受 ToolRegistry
- Workspace 内建工具通过 ToolSpec 注册

当前 CI：
- M1 P0 Gate run 42：PASS
- Minimum CI run 92：FAIL
- 唯一 Pyright error 位于 src/deepseek_runtime/cli.py:93：CLI 仍可能把 ToolRegistry | dict 传给只接受 ToolRegistry | None 的 Runtime.run。
- type-check 失败后 unit tests/import/secret scan/docs gate 被跳过。
- 这是实现迁移未完成，不是环境问题；禁止降低 Pyright 或直推 develop 绕过。

立即执行：
1. 拉取并严格审查 PR #14 完整 diff，不要仅相信本提示词。
2. 修复 cli.py：无 workspace tools 时使用空 ToolRegistry() 或 None，确保不产生 dict fallback，并审查 CLI 行为兼容性。
3. 运行 Pyright，确认 errorCount=0。
4. 补 TC-TOOL-001–004、TC-RUN-004/009/011，以及 malformed tool-call/exception boundary 测试。
5. 测试暴露实现问题时修实现，不得降低断言。
6. 保持 PR #14 范围，不混入 Policy、Approval、ExecutionAdapter、Budget、Cancellation、CLI 输出协议或 M3。
7. 更新 Traceability 和必要文档。
8. 运行最终精确内容 Minimum CI；保留失败证据，不通过 rerun 掩盖问题。
9. 严格 Code Review 后再将 PR 从 Draft 转 Ready；CI 全绿才合入 develop。
10. 合入后更新路线图，再开始 M2-B Policy 与 Approval。

开发流程：
- 功能分支 → Draft PR → tests/CI → Ready → develop。
- 只有 PR 流程持续因环境或基础设施问题无法完成，才允许直推 develop。
- 直推 commit 必须包含“## 问题原因”和“## 技术债务”，必要时更新 docs/TECH_DEBT.md。
- 禁止直接开发 master；master 只用于通过 Release Gate 的发布。

请独立持续执行，不要停在分析或计划阶段。每个 PR 保持聚焦、可审查、可测试，并始终保持 NO RELEASE，直到 M6 最终 Gate 明确允许发布。
```

## 11. 当前结论

- M0/M1 已有合并态、三平台和 closeout 证据；
- M2 已开始，Draft PR #14 已完全保存在远程；
- PR #14 当前因 1 个真实 Pyright 错误处于 CI RED；
- 下一会话应从修复 CLI 类型迁移、补测试和收口 CI 继续；
- 在 M2–M6 完成前，仓库继续保持 **NO RELEASE**。
