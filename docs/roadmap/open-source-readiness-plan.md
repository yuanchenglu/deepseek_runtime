# DeepSeek Runtime 开源就绪执行计划

> 计划版本：2.2.3  
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
| M2 Runtime 与 Security 闭环 | **IN PROGRESS / PR #14 FINAL GATE** | M2-A 代码与测试已通过；正在验证文档同步后的最终精确内容 | Draft PR #14、Minimum CI run 99、M1 P0 Gate run 49 |
| M3 Recovery、Change、Evidence、Observability | **NOT STARTED** | P1 Requirement 仍有 Blocked/Partial | Traceability |
| M4 Provider、配置与 CLI 协议收口 | **NOT STARTED** | Provider、streaming、配置和 CLI 稳定合同未完成 | Traceability |
| M5 完整 CI、Packaging 与治理 | **NOT STARTED** | 完整矩阵、构件和发布验证未建立 | Traceability |
| M6 RC 与 Alpha 发布 | **NOT STARTED** | 尚未进入 RC；不得合入 `master` 或打发布 tag | Release Gate |

客观结论：

- 7 个里程碑中，2 个已关闭，1 个执行中，4 个未开始；
- 里程碑规模不等，不应把 2/7 直接解释为发布完成度；
- M2-A 仅关闭 ToolRegistry 唯一入口，不代表 Policy、Approval、Adapter 或 Runtime lifecycle 已完成；
- M2–M5 仍有大量 P1 Requirement 未 `Verified`；
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

## 4. 当前 M2-A 工作现场

### 4.1 远程保存状态

当前不存在仅保存在临时容器中的未上传代码。

- 远程分支：`agent/m2-tool-registry`；
- 基线：`develop@64b938fbd861a0157c800191653bbc70b128901e`；
- Draft PR：#14 `feat: start M2 ToolRegistry production path`；
- PR 为 open + draft；完成严格 review 前不得转 Ready；
- 动态 head 应从 PR #14 获取，不在计划中写死；
- 当前代码、测试、Traceability、中文/英文 README 与本路线图均已上传远程；
- auto-merge 在 Draft 状态失败不属于产品 Gate。

当前直接变更范围：

1. `src/deepseek_runtime/contracts/tools.py`
2. `src/deepseek_runtime/contracts/__init__.py`
3. `src/deepseek_runtime/__init__.py`
4. `src/deepseek_runtime/runtime.py`
5. `src/deepseek_runtime/cli.py`
6. `tests/test_tool_registry_runtime.py`
7. `docs/traceability/alpha-traceability.md`
8. `README.md`
9. `README_en.md`
10. `docs/roadmap/open-source-readiness-plan.md`

### 4.2 已实现范围

- `ToolRegistry` 作为 `ToolSpec` 的生产工具集合；
- duplicate name、handler callable、risk category、side-effect、limits、`RecoveryPolicy` 注册校验；
- `side_effect` 和 `RecoveryPolicy` 的运行时类型合同；
- JSON Schema Draft 2020-12 参数校验；
- Provider tool definitions 由 `ToolSpec` 生成；
- unknown tool → `TOOL_NOT_FOUND`，且不执行任何 handler；
- `str`、UTF-8 bytes、JSON-compatible result 确定性规范化；
- invalid result → `TOOL_RESULT_INVALID`；
- handler exception → `TOOL_EXECUTION_FAILED`，不暴露异常正文；
- `DeepSeekRuntime.run()` 只接受 `ToolRegistry | None`；
- CLI 默认传 `WorkspaceTools(...).catalog()`，`--no-tools` 传 `None`，不再产生裸 `{}` fallback；
- `read_file` 和 `search` 通过完整 `ToolSpec` 注册；
- malformed JSON、function 非 object、arguments 非 JSON string 均在 handler 前结构化拒绝；
- tool-call ID 非空字符串校验失败时以 `PROVIDER_RESPONSE_INVALID` fail-closed，handler 不执行；
- malformed tool-call 进入 Evidence 前使用非执行安全结构视图，避免旧 Evidence helper 在校验前崩溃；原始 Provider 消息不被修改。

### 4.3 自动化测试

新增 `tests/test_tool_registry_runtime.py`，覆盖：

- `TC-TOOL-001`：完整 ToolSpec 与 Provider definition；
- `TC-TOOL-002`：duplicate registry；
- `TC-TOOL-003`：缺字段、额外字段、错误类型，handler 调用数保持 0；
- `TC-TOOL-004`：side-effect 缺 risk/recovery、非法合同类型；
- `TC-RUN-004`：裸 handler mapping 在 Provider 调用前拒绝；
- `TC-RUN-009`：dict/list/UTF-8 bytes 确定性规范化，object/non-UTF-8 拒绝；
- `TC-RUN-011`：unknown tool 返回 `TOOL_NOT_FOUND`，handler 调用数为 0；
- malformed tool-call JSON；
- function 不是 object；
- arguments 不是 JSON string；
- handler exception 与异常正文不泄漏；
- tool-call ID 为数字、空值或空字符串；
- CLI `--no-tools` 和默认 Registry 迁移。

### 4.4 CI 失败历史与修复

失败证据全部保留，未使用 rerun 掩盖：

1. **Minimum CI run 92：FAIL**
   - Pyright 唯一错误：CLI 仍可能把 `ToolRegistry | dict` 传入只接受 `ToolRegistry | None` 的 `Runtime.run()`；
   - 根因是代码迁移不完整，不是 CI 环境问题；
   - 修复为 `--no-tools → None`，默认路径传 `WorkspaceTools(...).catalog()`。

2. **Minimum CI run 98：FAIL**
   - Pyright 已通过，证明原 blocker 清零；
   - unit tests 首次执行新增 malformed function 测试时失败；
   - 根因是 Runtime 在 tool-call 校验前调用旧 `response_evidence()`，旧 helper 假设 `function` 必为 object；
   - 修复为只对 Evidence 构造安全结构视图，不能执行 handler，也不改变原始 Provider 消息。

3. **Minimum CI run 99：PASS**
   - critical lint、Pyright、全量 unit、import、tracked secret scan、docs traceability 全部通过；
   - 对应 code/test head：`9a604fb6875aeb27fc60672020016db308e10fc2`。

4. **M1 P0 Gate run 49：PASS**
   - 三平台 M1 P0 回归未被 M2-A 破坏。

文档同步后的最终精确内容仍需新的 Minimum CI 和 M1 P0 Gate 结果，才可进入 Ready/merge 决策。

### 4.5 PR #14 完成条件

已完成：

- [x] 修复 CLI `ToolRegistry | dict` 类型错误；
- [x] 自动化 `TC-TOOL-001`–`004`；
- [x] 自动化 `TC-RUN-004`、`TC-RUN-009`、`TC-RUN-011`；
- [x] 增加 malformed tool-call JSON、function shape、arguments shape、call ID、exception boundary 测试；
- [x] 审查旧 API 和 CLI 兼容性；
- [x] 更新 Traceability 的实际 PR、Test、Evidence、Status、Blocker；
- [x] 同步中文/英文 README 和路线图真实状态；
- [x] 保留 run 92/run 98 失败证据；
- [x] code/test 精确内容 Minimum CI run 99 全绿；
- [x] M1 P0 Gate run 49 全绿。

尚待完成：

- [ ] 文档同步后的最终精确内容 Minimum CI 全绿；
- [ ] 文档同步后的 M1 P0 Gate 全绿；
- [ ] 完整 diff 严格 Code Review 无未解决 P0/S0/S1 blocker；
- [ ] 更新 PR 描述为最终事实状态；
- [ ] 从 Draft 转 Ready；
- [ ] CI 全绿后合入 `develop`；
- [ ] 合入后更新路线图为 M2-A merged，并开始独立 M2-B Draft PR。

### 4.6 PR #14 明确不做

- Permission Policy 重构；
- ApprovalProvider；
- ExecutionAdapter；
- timeout/output-size 实际 enforcement；
- process-tree cleanup；
- cancellation；
- token/cost/context/time budgets；
- checkpoint timing；
- CLI stdout/report/json 协议重构；
- M3 checkpoint store 或 Evidence 重构。

## 5. M2 执行顺序

### M2-A：ToolRegistry 唯一入口（当前 PR #14）

完成条件：Runtime 只接受 `ToolRegistry`；内建工具通过 `ToolSpec`；Provider schema 从 Registry 生成；工具错误结构化；`TC-TOOL-001`–`004` 与 `TC-RUN-004/009/011` 自动化；无第二套裸 handler production path；Traceability/CI 完整。

### M2-B：Policy 与 Approval

依赖 M2-A 合入 `develop`。每次工具执行有 policy decision；READ 默认 ALLOW、非 READ 默认 DENY；规则优先级稳定；ASK 进入 ApprovalProvider；approve-once/session、deny、timeout；安全摘要；decision/approval 进入 checkpoint/evidence。

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

首先读取 PR #14 的动态状态，以及该分支上的：
1. docs/roadmap/open-source-readiness-plan.md（v2.2.3）
2. docs/product/PRD.md
3. docs/traceability/alpha-traceability.md
4. docs/testing/test-cases.md
5. docs/testing/test-plan.md
6. docs/security/threat-model.md
7. CONTRIBUTING.md

当前事实：
- develop：64b938fbd861a0157c800191653bbc70b128901e
- M0：CLOSED
- M1：CLOSED
- M2：IN PROGRESS
- 分支：agent/m2-tool-registry
- Draft PR：#14
- 动态 head：直接读取 PR #14，不依赖静态 SHA
- Release：NO RELEASE

PR #14 已完成 CLI Registry 迁移、ToolRegistry/ToolSpec 注册合同、JSON Schema 参数校验、Provider definitions、结果规范化、unknown-tool 和 malformed tool-call 边界测试。

已保留失败证据：
- Minimum CI run 92：Pyright 发现 CLI 裸 dict fallback；
- Minimum CI run 98：Pyright 已清零，但 unit tests 暴露 Evidence 在 malformed function 校验前崩溃。

修复后证据：
- Minimum CI run 99：PASS；
- M1 P0 Gate run 49：PASS。

下一步：
1. 读取当前最新 head 的 CI，确认文档同步后的最终精确内容 Minimum CI 与 M1 P0 Gate 全绿；
2. 严格审查 PR #14 完整 diff、public API、错误边界、测试断言和范围；
3. 更新 PR 描述为最终事实状态；
4. 无 P0/S0/S1 blocker 后从 Draft 转 Ready；
5. CI 全绿后合入 develop；
6. 合入后更新路线图并新建独立 M2-B Policy/Approval 分支和 Draft PR。

禁止在 PR #14 混入 Policy、Approval、ExecutionAdapter、timeout/output enforcement、Budget、Cancellation、CLI 输出协议或 M3。禁止直接开发 master。保持 NO RELEASE。
```

## 11. 当前结论

- M0/M1 已有合并态、三平台和 closeout 证据；
- M2-A 的代码、测试与文档均已保存在 PR #14 远程分支；
- run 92 和 run 98 的真实失败已保留并完成根因修复；
- code/test 内容已由 Minimum CI run 99 和 M1 P0 Gate run 49 验证；
- 当前只剩最终精确内容 CI、严格 review、Ready 和 merge；
- M2-B–M2-G、M3–M6 完成前保持 **NO RELEASE**。
