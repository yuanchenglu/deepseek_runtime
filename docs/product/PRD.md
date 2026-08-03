# DeepSeek Runtime 产品需求文档（PRD）

> 文档版本：1.6
> 产品阶段：Open-source Alpha Hardening
> 适用验证基线：`develop@8c097a6348bc45cc40a24635124c3c2c845fed57`；M2-E closed
> 文档修订：以本文件所在 Git commit 为准
> 唯一目标：以最少新增功能，把项目做到可以真实、可信、可持续地开源。

## 0. 文档规则

- 本 PRD 是产品范围、优先级和验收标准的唯一事实源。
- `P0`：不满足则禁止任何公开发布。
- `P1`：首个公开 Alpha 必须满足。
- `P2`：Alpha 后迭代，不阻塞首次开源，除非被批准为 P0/P1 的技术前置。
- 状态：`Implemented`、`Partial`、`Planned`、`Blocked`、`Verified`。
- “实现存在”不等于“验收通过”；只有实现合入开发基线、可复现测试和可访问证据齐备，才标记 `Verified`。
- 测试用例不得自行提升或降低 Requirement 优先级；优先级冲突一律以本 PRD 为准。
- `Requirement → Milestone → PR → Test → Evidence` 映射见 `docs/traceability/alpha-traceability.md`。

## 1. 背景

直接调用 DeepSeek API 不能自动解决 Agent 产品所需的工具治理、状态恢复、文件变更、证据隐私、成本控制和发布验证。

当前仓库已在 `develop` 合入 ToolRegistry、Policy/Approval、ExecutionAdapter，M2-D Runtime lifecycle、任务预算、Provider-before-call cancellation 与 tool-error policy，以及 M2-E Workspace bounded read/search。durable recovery、Provider 协议、CLI 协议和发布工程仍未闭环。

## 2. 产品目标

### G-01：可运行

开发者可在干净环境中完成安装、doctor、无网络测试和最小 Runtime 示例。

### G-02：可控

每次工具执行都经过注册、参数校验、权限决策、必要审批、ExecutionAdapter、超时和输出预算。

### G-03：可恢复

任务中断后能够恢复；已确认成功的副作用不重复执行，不确定副作用不会被自动重试。

### G-04：可审计

默认公开输出不泄露 API Key、prompt、response、reasoning 和工具正文。

### G-05：可贡献

贡献者能通过明确命令运行 lint、type check、tests、security checks 和 release checks。

### G-06：可发布

发布构件来源明确、可安装、经过 secret scan、digest 校验和自动化门禁。

## 3. 非目标

首个公开 Alpha 不新增：

- MCP、Skills、Multi-Agent；
- Memory、RAG、Vector Database；
- IDE、TUI、Desktop；
- Hosted API、云端多租户、账号、计费和组织权限；
- Plugin Marketplace、Workflow DSL；
- Browser / Computer Use；
- 多 Provider 横向扩张；
- 通用 exactly-once 外部副作用保证；
- 默认交付 Docker/Podman/平台内核级隔离实现。

首个 Alpha 不使用命令黑名单、cwd 限制或普通 subprocess 宣称“安全沙箱”。`RestrictedSubprocessAdapter` 是进程资源边界，不是 container、VM 或 kernel sandbox。

## 4. 用户与场景

### Persona A：Runtime 集成开发者

需要稳定 Python API，将 Agent loop 嵌入本地产品或服务。

### Persona B：Tool 开发者

需要声明工具 schema、风险、副作用、超时、输出上限和恢复策略。

### Persona C：本地最终用户

需要看到最终回答、审批高风险动作、理解失败状态并恢复中断任务。

### Persona D：Maintainer / 安全审查者

需要确定性 CI、对抗测试、追踪矩阵、发布证据和明确的 No Release 规则。

## 5. 核心用户故事

- US-001：集成开发者可用 Fake Provider 离线测试完整多轮 tool loop。
- US-002：Tool 开发者提交错误参数时，Runtime 在 handler 前拒绝。
- US-003：用户可批准、拒绝或让 ASK 操作超时。
- US-004：用户能区分工具失败、超时、取消和副作用不确定。
- US-005：用户恢复会话时，不重复已确认成功的副作用。
- US-006：维护者可分享诊断报告而不泄露正文和密钥。
- US-007：维护者可证明发布包没有包含 `.env`、checkpoint 或未跟踪文件。
- US-008：用户默认看到最终回答，安全报告独立输出。

## 6. 功能需求

### 6.1 安装、配置与版本

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| CFG-001 | P1 | 支持 Python 3.11–3.13 | 三版本 CI 全通过 | Partial |
| CFG-002 | P1 | 包版本只有一个真源 | package、diagnostics、artifact、tag 一致 | Blocked |
| CFG-003 | P1 | API Key 仅从显式配置或环境读取 | repr、日志、doctor、error 不出现值 | Partial |
| CFG-004 | P1 | 环境配置解析有类型和范围校验 | 非法 timeout/max_tokens 返回 `CONFIG_INVALID` | Planned |
| CFG-005 | P1 | 显式传入空 env 不回退宿主环境 | `env={}` 测试通过 | Blocked |
| CFG-006 | P2 | 支持配置对象覆盖环境变量 | 优先级文档和测试明确 | Partial |

### 6.2 Provider Client

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| PROV-001 | P1 | 请求 method/url/header/body 正确 | Mock transport 测试 | Implemented |
| PROV-002 | P1 | 任意 Provider JSON 根不会使 Client 崩溃 | property test 返回规范化结果或结构化错误 | Blocked |
| PROV-003 | P1 | 校验 choices/message/tool_calls shape | malformed fixtures 全部结构化失败 | Planned |
| PROV-004 | P1 | 区分 auth/rate-limit/timeout/transport/5xx | error-code matrix | Partial |
| PROV-005 | P1 | 429/5xx 可配置 retry/backoff | fake clock 验证次数、延迟和预算 | Planned |
| PROV-006 | P1 | 限制最大响应体 | 超限返回 `PROVIDER_RESPONSE_TOO_LARGE` | Planned |
| PROV-007 | P1 | Request identity 包含 provider/method/endpoint/body | canonical identity 测试 | Partial |
| PROV-008 | P1 | SSE 支持任意 byte chunk boundary | split-byte、UTF-8 和 multiline tests | Blocked |
| PROV-009 | P1 | Stream 提供 iterator/callback 和最终聚合 | 内容增量到达且聚合一致 | Blocked |
| PROV-010 | P2 | Provider adapter 可扩展 | 不修改 Runtime 可替换 adapter | Partial |

### 6.3 Runtime Loop

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| RUN-001 | P1 | 支持 text-only 完成 | 一步返回 final result | Verified |
| RUN-002 | P1 | 支持多轮 tool call | Fake Provider 三轮测试 | Verified |
| RUN-003 | P1 | 所有工具调用必须经 ToolRegistry | 无裸 handler 或 Adapter bypass 生产路径 | Verified |
| RUN-004 | P1 | 所有关键状态转换可 checkpoint | transition/event/checkpoint 测试 | Verified |
| RUN-005 | P1 | max_steps 是明确预算 | 超限返回 `BUDGET_STEP_EXCEEDED` | Verified |
| RUN-006 | P1 | 支持 cancellation | Provider 前不发送请求；tool 执行可取消并清理 | Partial |
| RUN-007 | P1 | 支持 token/cost/context/time budget | 达阈值停止并生成证据 | Verified |
| RUN-008 | P1 | Tool error 回传模型或终止策略可配置 | policy tests | Verified |
| RUN-009 | P1 | 非字符串工具结果被规范化或拒绝 | JSON/object/binary tests | Verified |
| RUN-010 | P1 | malformed Provider 不抛未处理异常 | fixtures 全部返回 RuntimeResult | Partial |
| RUN-011 | P2 | 支持生命周期 hook | hook 顺序和异常策略稳定 | Planned |

### 6.4 Tool Contract

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| TOOL-001 | P1 | ToolSpec 声明 name/description/schema/handler | API 测试 | Verified |
| TOOL-002 | P1 | Registry 拒绝重复 tool name | 单元测试 | Verified |
| TOOL-003 | P1 | 参数在 handler 前按 JSON Schema 校验 | invalid fixtures 不调用 handler | Verified |
| TOOL-004 | P1 | Tool 声明 risk 和 side_effect | 缺失声明不能注册 | Verified |
| TOOL-005 | P1 | Tool 声明 timeout/output limit | 超时或超限结构化失败 | Verified |
| TOOL-006 | P1 | Tool 声明 recovery policy | side-effect 工具必须配置 | Partial |
| TOOL-007 | P1 | 未知工具返回 `TOOL_NOT_FOUND` | handler 不执行 | Verified |
| TOOL-008 | P2 | Provider tool schema 从 ToolSpec 自动生成 | schema snapshot test | Implemented |

### 6.5 Workspace Tools

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| WS-001 | P0 | read_file 不能越出工作区 | traversal/symlink tests | Verified |
| WS-002 | P0 | search 不能跟随外部 symlink/reparse point | adversarial tests | Verified |
| WS-003 | P1 | read_file 有字节上限且标注截断 | UTF-8/大文件测试 | Verified |
| WS-004 | P1 | search 有文件数、字节和时间预算 | 大仓库 fixture | Verified |
| WS-005 | P1 | 二进制、权限和 IO 错误结构化返回 | fixtures | Verified |
| WS-006 | P2 | `.git`、runtime state 和用户 exclude 可配置 | config tests | Partial |

### 6.6 Policy、Approval 与 Execution Adapter

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| SEC-001 | P1 | 非 READ 默认 DENY | 单元测试 | Verified |
| SEC-002 | P1 | 规则优先级明确且文档化 | overlap rule tests | Verified |
| SEC-003 | P1 | ASK 有 ApprovalProvider | approve/deny/timeout tests | Partial |
| SEC-004 | P1 | Runtime 强制所有工具走 policy | integration test | Verified |
| SEC-005 | P1 | 命令 Gate 不宣称隔离 | 文档、类型和帮助文本一致 | Verified |
| SEC-006 | P1 | 子进程使用最小环境变量 | child 无 API Key 测试 | Verified |
| SEC-007 | P1 | 命令 timeout 清理进程树 | child-process test | Verified |
| SEC-008 | P1 | 提供可插拔 Execution/Sandbox Adapter 接口 | fake、no-isolation、restricted adapter tests | Verified |
| SEC-009 | P1 | 审计日志不泄露参数 secret | marker/结构化 secret tests | Verified |
| SEC-010 | P2 | 提供 Docker/Podman 参考 adapter | example integration test | Planned |

`SEC-003` 保持 Partial：PR #20 已覆盖 pending-before-I/O、approve-once、approve-session、deny、timeout、unavailable、invalid outcome 的内存 checkpoint handoff；durable store、resume 和 migration 属 M3。

### 6.7 文件变更与回滚

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| CHG-001 | P0 | Rollback handle 不可伪造 | forged-handle test | Verified |
| CHG-002 | P0 | rollback 路径重新执行 containment 和 policy | external-path test | Verified |
| CHG-003 | P1 | apply 拒绝重复路径 | duplicate fixture | Planned |
| CHG-004 | P1 | validate/write 受 workspace 或 file lock 保护 | concurrent test | Planned |
| CHG-005 | P1 | rollback 不覆盖后续外部修改 | stale rollback test | Implemented |
| CHG-006 | P1 | 文件 mode/metadata 按策略保留 | platform tests | Planned |
| CHG-007 | P1 | 文件和父目录持久化语义明确 | fsync fault-injection test | Partial |
| CHG-008 | P1 | 审计包含 changeset、路径、结果，不含正文 | evidence test | Partial |
| CHG-009 | P1 | 明确 best-effort 多文件事务语义，不声称跨目录严格原子性 | 文档、故障注入与实际行为一致 | Blocked |
| CHG-010 | P1 | rollback handle 引用受保护的 ChangeJournal；重启后语义明确 | restart/expired/cross-workspace tests | Partial |

### 6.8 Session 与恢复

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| SES-001 | P1 | Checkpoint 和 Evidence schema 分离 | 类型/API 测试 | Partial |
| SES-002 | P1 | Checkpoint 保留 Provider continuation 语义 | thinking tool-resume fixture | Partial |
| SES-003 | P1 | Checkpoint 可选加密 at rest | key injection/roundtrip test | Planned |
| SES-004 | P1 | 原子写入并检测损坏 | crash/corrupt/concurrent tests | Partial |
| SES-005 | P1 | schema migration/unsupported version 明确 | fixture tests | Partial |
| SES-006 | P1 | succeeded 副作用不重复 | resume test | Implemented |
| SES-007 | P0 | running 副作用不默认重试 | uncertain-state test | Verified |
| SES-008 | P1 | handler missing 不导致无上下文 KeyError | `TOOL_NOT_FOUND` | Implemented |
| SES-009 | P1 | retry budget 和 backoff | fake clock tests | Partial |
| SES-010 | P1 | 保存 approvals、budgets、receipts | roundtrip test | Partial |

### 6.9 Evidence 与隐私

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| EVD-001 | P1 | 公开 evidence 无 API Key | leak test | Partial |
| EVD-002 | P1 | 公开 evidence 无 prompt/response/reasoning 正文 | leak test | Implemented |
| EVD-003 | P1 | evidence 对任意 JSON-compatible 输入是 total function | property test | Partial |
| EVD-004 | P1 | canonical JSON 稳定 | key-order test | Partial |
| EVD-005 | P1 | 低熵敏感文本不使用可猜裸 hash | threat-model test | Planned |
| EVD-006 | P1 | evidence schema 版本化 | schema snapshot/compatibility test | Partial |
| EVD-007 | P1 | debug content 只能显式开启 | CLI/API test | Partial |
| EVD-008 | P1 | error 字段也经过 secret redaction | exception-secret test | Partial |

### 6.10 Observability 与预算

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| OBS-001 | P1 | 统计 provider/tool/step latency | fake clock test | Partial |
| OBS-002 | P1 | 统计 token/cache/cost | fixture tests | Partial |
| OBS-003 | P1 | 未知成本保持 unknown | missing-field test | Verified |
| OBS-004 | P1 | 输入 token 无拆分时不漏算 | provider fixture | Blocked |
| OBS-005 | P1 | 负数、NaN 和非法价格拒绝 | validation test | Planned |
| OBS-006 | P1 | success/first-completion 分母只使用已知值 | partial-data test | Blocked |
| OBS-007 | P1 | Runtime 可执行预算停止 | integration tests | Verified |
| OBS-008 | P2 | 输出稳定 JSON schema | snapshot | Partial |

### 6.11 CLI 与诊断

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| CLI-001 | P1 | `doctor --json` 无 Key 可运行 | subprocess test | Implemented |
| CLI-002 | P1 | `run` 默认输出最终回答 | golden test | Blocked |
| CLI-003 | P1 | safe report 可用独立 `--report` 输出 | file/stdout test | Planned |
| CLI-004 | P1 | debug 明文需要明显危险开关 | help/golden test | Partial |
| CLI-005 | P1 | 退出码与 error code 对应 | subprocess matrix | Partial |
| CLI-006 | P1 | workspace 不存在时友好失败 | test | Partial |
| CLI-007 | P2 | 支持 resume session id | end-to-end test | Planned |
| DOC-001 | P1 | doctor 区分“诊断成功”和“可在线运行” | report semantics test | Partial |

### 6.12 开源与发布

| ID | P | 需求 | 验收标准 | 当前 |
| --- | --- | --- | --- | --- |
| OSS-001 | P1 | GitHub Actions 自动运行质量门禁 | 每个 PR 有 checks | Partial |
| OSS-002 | P1 | Linux/macOS/Windows 测试 | matrix green | Planned |
| OSS-003 | P1 | Ruff + 单一 type checker | CI green | Partial |
| OSS-004 | P1 | Coverage 阈值和关键路径分母明确 | 指标定义与 gate 均通过 | Partial |
| OSS-005 | P1 | Secret scan | 故意 secret fixture 被拦截 | Partial |
| OSS-006 | P1 | 构件基于 Git tracked allowlist | `.env` 和未跟踪文件不进入包 | Blocked |
| OSS-007 | P1 | 构件 digest 实际重新计算 | tampered artifact 门禁失败 | Blocked |
| OSS-008 | P1 | wheel 和 sdist 可安装 | clean env smoke | Planned |
| OSS-009 | P1 | CONTRIBUTING/CODE_OF_CONDUCT/issue/PR templates 完整 | 文件和链接校验 | Partial |
| OSS-010 | P1 | 安全报告流程和响应范围明确 | SECURITY 内容测试和人工审查 | Partial |
| OSS-011 | P1 | README 所有公开能力有 PRD/测试证据 | traceability audit | Partial |
| OSS-012 | P2 | SBOM/依赖清单 | artifact 包含 | Planned |

## 7. 非功能需求

### NFR-SEC：安全

- 模型输出、Provider response、工作区内容和工具参数均视为不可信。
- 所有工具参数必须在 handler/Adapter 前验证。
- 默认日志不能包含正文和 secret。
- Runtime 不得把命令分类器、cwd、普通 subprocess 或 RestrictedSubprocessAdapter 描述为内核隔离。
- Alpha 防御不可信模型和不可信工作区内容，但不承诺抵抗同一主机上的恶意并发进程或恶意 Tool builder。

### NFR-REL：可靠性

- Runtime 公开入口不因 JSON-compatible Provider 响应抛未处理异常。
- checkpoint 损坏必须结构化失败。
- side-effect uncertain 状态不能自动当作 pending。
- retry 必须有上限和明确 eligibility。
- Rollback handle 的进程重启、过期和跨工作区语义必须明确。

### NFR-PERF：性能与资源

- Workspace search 默认不超过 10,000 文件、100MB 扫描、5 秒，可配置。
- Tool output 默认不超过 100KB，可配置。
- Provider response 必须有最大字节限制。
- 每次任务有 step/token/cost/context/time budget。

### NFR-COMP：兼容性

- Python 3.11–3.13。
- Linux、macOS、Windows。
- 文件系统、进程树、fsync 和 reparse-point 差异必须在测试报告标注。

### NFR-MAINT：可维护性

- 公共 API 有 type hints 和最小示例。
- 版本单一真源。
- 教学注释移到 docs。
- error code、checkpoint schema 和 evidence schema 有兼容策略。

## 8. 产品交互要求

### 默认 CLI 输出

```text
stdout: 最终回答
stderr: 进度/警告（可关闭）
--report path.json: 安全证据
--json: 机器可读结果
--unsafe-debug-content: 明文调试，需要显式确认
```

### 审批

审批信息至少包含：工具名、风险等级、规范化路径或命令、安全摘要、可能副作用，以及 allow once / allow session / deny / timeout。

## 9. 数据与隐私

| 数据 | 默认存储 | 可公开 | 恢复必需 |
| --- | --- | --- | --- |
| API Key | 不存 | 否 | 否 |
| Prompt/response | checkpoint，可选加密 | 否 | 是 |
| Reasoning continuation | checkpoint，可选加密 | 否 | 可能是 |
| Tool arguments/results | checkpoint，可选加密 | 默认否 | 是 |
| Structural evidence | JSON | 是 | 否 |
| Usage/cost | JSON | 是 | 否 |
| Approval/receipt | checkpoint | 可脱敏摘要 | 是 |
| ChangeJournal | 本地受保护存储，可选加密 | 否 | rollback 需要 |

## 10. 发布门禁

首个 Open-source Alpha 必须同时满足：

1. 所有 P0/P1 Requirement 状态为 `Verified`；
2. Active P0/P1/S0/S1 defect 均为 0；
3. CI 多平台、多 Python 版本全绿；
4. P0/P1 测试 100% 通过且无已知 flaky test；
5. README 与 PRD traceability 检查通过；
6. wheel/sdist 在干净环境安装成功；
7. release artifact 通过 secret scan；
8. manifest 重新计算 digest 后匹配，篡改构件被拒绝；
9. live DeepSeek smoke 通过且无泄漏；
10. `docs/testing/test-report-*.md` 给出明确 `Release` 结论。

任一条件不满足，结论必须为 `No Release`。

## 11. 里程碑

- M0：基线、治理、Threat Model、Traceability 和最小 CI；
- M1：核心合同冻结与全部 P0 关闭；
- M2：Runtime、Tool、Policy、Approval 和 Execution Adapter 闭环；
- M3：Recovery、Change、Evidence 和 Observability 正确性；
- M4：Provider、配置、CLI 和协议收口；
- M5：完整 CI、Packaging、治理和 Release Engineering；
- M6：Release Candidate、独立验证与 Alpha 发布。

M0、M1、M2-A、M2-B、M2-C、M2-D、M2-E 已关闭；M2-F CLI Core 为下一执行切片。具体执行顺序见 `docs/roadmap/open-source-readiness-plan.md`。
