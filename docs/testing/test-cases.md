# DeepSeek Runtime 测试用例

> 用例版本：1.1
> 适用代码审查基线：`develop@0e1e435`
> 文档修订：以本文件所在 Git commit 为准
> 规则：P0/P1 用例是首次公开 Alpha 的发布门禁；P2 用例不阻塞 Alpha，除非被批准为 P0/P1 技术前置。

测试优先级必须与 `docs/product/PRD.md` 一致，不允许测试文档隐式改变 Requirement 优先级。

## A. 配置与安装

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-CFG-001 | P1 | CFG-001 | Python 3.11/3.12/3.13 安装 | 均可 import 和运行 tests |
| TC-CFG-002 | P1 | CFG-002 | 比较 package/metadata/diagnostics/artifact/tag 版本 | 全部相同 |
| TC-CFG-003 | P1 | CFG-003 | repr/doctor/error 中注入假 API Key | 输出不含 Key |
| TC-CFG-004 | P1 | CFG-004 | timeout 非数字、负数、NaN | `CONFIG_INVALID` |
| TC-CFG-005 | P1 | CFG-005 | 宿主有 Key，调用 `build_diagnostics(env={})` | 报 absent，不读取宿主 |
| TC-CFG-006 | P1 | OSS-008 | 干净 venv 安装 wheel/sdist | CLI 和 import 成功 |

## B. Provider Client

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-PROV-001 | P1 | PROV-001 | chat 请求构造 | endpoint/header/body 正确 |
| TC-PROV-002 | P1 | PROV-002 | JSON 根为 list/string/null/number | 不崩溃，结构化 malformed |
| TC-PROV-003 | P1 | PROV-003 | choices 缺失/null/非列表 | `PROVIDER_MALFORMED_RESPONSE` |
| TC-PROV-004 | P1 | PROV-003 | message/tool_calls/function 类型错误 | 结构化失败 |
| TC-PROV-005 | P1 | PROV-004 | 401/403/429/500/timeout/DNS | error code 正确 |
| TC-PROV-006 | P1 | PROV-005 | 429 两次后 200 | 按预算重试，delay 正确 |
| TC-PROV-007 | P1 | PROV-005 | retry budget 用尽 | 最终错误包含 attempts |
| TC-PROV-008 | P1 | PROV-006 | 响应体超限 | 提前中止且不保存正文 |
| TC-PROV-009 | P1 | PROV-007 | 相同 body 不同 key order | identity 相同 |
| TC-PROV-010 | P1 | PROV-007 | 相同 body 不同 endpoint | identity 不同 |
| TC-PROV-011 | P1 | PROV-008 | SSE JSON 按每个 byte 切分 | 内容完整 |
| TC-PROV-012 | P1 | PROV-008 | multiline data/event/id/comment | 按 SSE 语义解析 |
| TC-PROV-013 | P1 | PROV-008 | 非法 UTF-8/JSON event | 有错误 evidence，不静默成功 |
| TC-PROV-014 | P1 | PROV-009 | 消费 stream iterator | 内容逐步到达且最终聚合一致 |
| TC-PROV-015 | P1 | RUN-006 | stream 中途取消 | 连接关闭，状态 `CANCELLED` |

## C. Runtime Loop

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-RUN-001 | P1 | RUN-001 | 一步文本响应 | ok + final_text |
| TC-RUN-002 | P1 | RUN-002 | 一次 tool call 后文本 | 消息顺序和 tool_call_id 正确 |
| TC-RUN-003 | P1 | RUN-002 | 三轮连续 tool calls | 未超过 step，最终成功 |
| TC-RUN-004 | P1 | RUN-003 | 尝试直接传裸 handler | 不存在绕过 Registry 的生产路径 |
| TC-RUN-005 | P1 | RUN-004 | 每种 P1 状态转换 | checkpoint 和 event 顺序正确 |
| TC-RUN-006 | P1 | RUN-005 | 达 max steps | `BUDGET_STEP_EXCEEDED` |
| TC-RUN-007 | P1 | RUN-007 | token/cost/context/time 超限 | 对应预算错误且不继续调用 |
| TC-RUN-008 | P1 | RUN-008 | tool error 回传模型 | 按配置继续或终止 |
| TC-RUN-009 | P1 | RUN-009 | handler 返回 dict/list/bytes/object | 规范化或 `TOOL_RESULT_INVALID` |
| TC-RUN-010 | P1 | RUN-010 | malformed Provider fixtures | RuntimeResult，不抛未处理异常 |
| TC-RUN-011 | P1 | TOOL-007 | 模型请求未知 tool | `TOOL_NOT_FOUND`，handler 不执行 |
| TC-RUN-012 | P1 | RUN-006 | Provider 前取消 | 不发送请求 |
| TC-RUN-013 | P1 | RUN-006 | Tool 执行中取消 | adapter 收到取消并清理 |
| TC-RUN-014 | P2 | RUN-011 | lifecycle hook 抛错 | 按 hook policy 隔离或终止 |

## D. Tool Contract

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-TOOL-001 | P1 | TOOL-001 | 注册完整 ToolSpec | 注册成功，字段完整 |
| TC-TOOL-002 | P1 | TOOL-002 | 重复名称 | 注册失败 |
| TC-TOOL-003 | P1 | TOOL-003 | 缺 required、额外字段、错误类型 | handler 不执行 |
| TC-TOOL-004 | P1 | TOOL-004/6 | side-effect 工具缺 risk/recovery policy | 注册失败 |
| TC-TOOL-005 | P1 | TOOL-005 | tool timeout | `TOOL_TIMEOUT` |
| TC-TOOL-006 | P1 | TOOL-005 | output 超限 | 截断或拒绝，evidence 标注 |
| TC-TOOL-007 | P1 | TOOL-006 | 幂等 key 重试 | side effect 只发生一次 |
| TC-TOOL-008 | P2 | TOOL-008 | ToolSpec schema snapshot | 与 Provider 约定一致 |

## E. Workspace 与安全

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-WS-001 | P0 | WS-001 | `../outside`、绝对路径 | `SANDBOX_VIOLATION` |
| TC-WS-002 | P0 | WS-002 | workspace symlink 指向外部文件后 search | 外部内容不可见 |
| TC-WS-003 | P0 | WS-002 | symlink 目录或 Windows reparse point 指向外部树 | 不遍历 |
| TC-WS-004 | P1 | WS-003 | UTF-8 多字节在截断边界 | 不产生非法文本，标注截断 |
| TC-WS-005 | P1 | WS-004 | 20k 小文件或扫描超时 | 达预算后停止 |
| TC-WS-006 | P1 | WS-005 | 二进制、权限错误、文件消失 | 结构化结果 |
| TC-SEC-001 | P1 | SEC-001 | READ/WRITE/NETWORK 默认决策 | read allow，其他 deny |
| TC-SEC-002 | P1 | SEC-002 | 通配规则与具体规则重叠 | 优先级符合文档 |
| TC-SEC-003 | P1 | SEC-003 | ASK approve/deny/timeout | 三种结果正确 |
| TC-SEC-004 | P1 | SEC-004 | 自定义工具执行 | 必须产生 policy event |
| TC-SEC-005 | P1 | SEC-006 | 子进程读取环境 | 无 `DEEPSEEK_API_KEY` |
| TC-SEC-006 | P1 | SEC-007 | 子进程再启动长时子进程 | timeout 后进程树清理 |
| TC-SEC-007 | P1 | SEC-005 | `bash -c curl`/`python socket`/`env curl` | NoIsolation/Restricted 边界明确，不宣称内核隔离 |
| TC-SEC-008 | P1 | SEC-009 | secret 在 `--token`、JSON 参数、异常字符串 | audit 无原值 |
| TC-SEC-009 | P1 | SEC-008 | Fake、NoIsolation、Restricted 三种 adapter | 接口一致；保证和限制可辨识 |

## F. ChangeManager

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-CHG-001 | P0 | CHG-001 | 手工构造 forged rollback handle | 被拒绝 |
| TC-CHG-002 | P0 | CHG-002 | handle 引用 workspace 外 Path | 被拒绝且外部文件不变 |
| TC-CHG-003 | P1 | CHG-003 | changeset 同一路径两次 | validate 失败 |
| TC-CHG-004 | P1 | CHG-004 | validate 后并发修改 | `CHANGE_CONFLICT` |
| TC-CHG-005 | P1 | CHG-005 | apply 后外部修改再 rollback | `ROLLBACK_CONFLICT` |
| TC-CHG-006 | P1 | CHG-006 | 可执行文件 apply/rollback | mode 按策略保留 |
| TC-CHG-007 | P1 | CHG-007 | 第一文件 replace 后故障 | 已写文件补偿，temp 清理，状态明确 |
| TC-CHG-008 | P1 | CHG-007 | fsync/replace 故障注入 | 明确失败，无静默成功 |
| TC-CHG-009 | P1 | CHG-008 | audit 序列化 | 无文件正文和 secret |
| TC-CHG-010 | P1 | CHG-009 | 多文件中间状态和跨目录故障 | 文档明确 best-effort，实际行为一致 |
| TC-CHG-011 | P1 | CHG-010 | 重启后使用 durable handle；expired/cross-workspace handle | 合法恢复或结构化拒绝，不依赖调用方载荷 |

## G. Session 与恢复

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-SES-001 | P1 | SES-001 | checkpoint/evidence roundtrip | 两种 schema 独立 |
| TC-SES-002 | P1 | SES-002 | reasoning/tool call 保存恢复 | continuation 字段完整 |
| TC-SES-003 | P1 | SES-003 | encrypted checkpoint | 磁盘无正文，可恢复 |
| TC-SES-004 | P1 | SES-004 | 非法 JSON/截断文件 | `CHECKPOINT_CORRUPT` |
| TC-SES-005 | P1 | SES-005 | 旧/未来 schema | migrate 或 unsupported |
| TC-SES-006 | P1 | SES-006 | succeeded side effect | resume 不执行 |
| TC-SES-007 | P0 | SES-007 | side effect 成功后、保存前崩溃 | `TOOL_SIDE_EFFECT_UNCERTAIN`，不自动重试 |
| TC-SES-008 | P1 | SES-008 | handler missing | `TOOL_NOT_FOUND` |
| TC-SES-009 | P1 | SES-009 | failed call 超 retry budget | 不继续重试 |
| TC-SES-010 | P1 | SES-010 | approvals/budgets/receipts | roundtrip 一致 |
| TC-SES-011 | P1 | SES-004 | 两进程并发 save | 不产生静默覆盖或损坏 |

## H. Evidence 与 Observability

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-EVD-001 | P1 | EVD-001/2 | prompt/response/reasoning/key 注入 | public JSON 无正文和 Key |
| TC-EVD-002 | P1 | EVD-003 | arbitrary nested JSON-compatible value | evidence 不抛异常 |
| TC-EVD-003 | P1 | EVD-004 | dict key order 改变 | canonical identity 相同 |
| TC-EVD-004 | P1 | EVD-005 | 低熵 secret：yes/no/4-digit PIN | 不输出可猜裸 hash |
| TC-EVD-005 | P1 | EVD-008 | exception message 含 secret | error 被脱敏 |
| TC-EVD-006 | P1 | EVD-006 | 当前/旧/未来 evidence schema | snapshot 稳定；不支持版本结构化拒绝 |
| TC-EVD-007 | P1 | EVD-007 | 默认、显式 debug、非交互环境 | 默认无正文；危险开关才允许 debug |
| TC-OBS-001 | P1 | OBS-002 | 完整 usage fixture | 汇总正确 |
| TC-OBS-002 | P1 | OBS-003 | cost/token 字段缺失 | 返回 unknown，不是 0 |
| TC-OBS-003 | P1 | OBS-004 | 只有 prompt_tokens | 输入成本不漏算 |
| TC-OBS-004 | P1 | OBS-005 | 负 token/负价格/NaN | validation fail |
| TC-OBS-005 | P1 | OBS-006 | 部分 first_completion 未知 | 分母只含已知 |
| TC-OBS-006 | P1 | OBS-007 | cost/token/time budget 超限 | Runtime 停止且有证据 |
| TC-OBS-007 | P1 | OBS-001 | Fake clock 驱动 provider/tool/step | 三类 latency 可验证且非负 |

## I. CLI、文档与发布

| ID | P | 对应需求 | 场景 | 预期 |
| --- | --- | --- | --- | --- |
| TC-CLI-001 | P1 | CLI-001 | 无 Key doctor | exit 0，warning |
| TC-CLI-002 | P1 | CLI-002 | `run "hello"` + Fake Provider | stdout 是回答 |
| TC-CLI-003 | P1 | CLI-003 | `--report out.json` | report 安全且 stdout 不污染 |
| TC-CLI-004 | P1 | CLI-004 | 明文 debug | 必须显式危险开关 |
| TC-CLI-005 | P1 | CLI-005 | error-code matrix | exit code 稳定 |
| TC-CLI-006 | P1 | CLI-006 | workspace 不存在或为文件 | 友好错误 |
| TC-DOC-001 | P1 | DOC-001 | doctor 本地检查成功但无 Key/网络不可用 | 明确区分诊断成功与可在线运行 |
| TC-OSS-001 | P1 | OSS-001/2 | PR CI | 多平台 matrix 全绿 |
| TC-OSS-002 | P1 | OSS-003/4 | lint/type/coverage | 工具固定；定义分母后的阈值通过 |
| TC-OSS-003 | P1 | OSS-005/6 | 工作树含 `.env`、checkpoint 和 secret fixture | 构件不包含，scan 通过 |
| TC-OSS-004 | P1 | OSS-007 | 修改 artifact 一个 byte | manifest gate 失败 |
| TC-OSS-005 | P1 | OSS-006 | 存在未跟踪普通文件 | 不进入构件，allowlist 策略明确 |
| TC-OSS-006 | P1 | OSS-008 | wheel/sdist clean install | import/CLI smoke 通过 |
| TC-OSS-007 | P1 | OSS-011 | README claim traceability | 每项映射 PRD ID + Test ID + Evidence |
| TC-OSS-008 | P1 | Release Gate | 缺任一必需证据 | `No Release` |
| TC-OSS-009 | P1 | OSS-009 | 治理文件、模板和链接检查 | 必需文件存在且链接有效 |
| TC-OSS-010 | P1 | OSS-010 | SECURITY 缺范围、渠道或响应策略 | 文档 gate 失败；完整内容通过人工评审 |
| TC-LIVE-001 | P1 | Release Gate | 真实 DeepSeek 固定 smoke | HTTP/内容/usage/无泄漏 |

## J. 门禁解释

- P0/P1 用例必须自动化，只有明确标记的 RC 人工审查可以作为补充证据。
- `TC-RUN-014`、`TC-TOOL-008` 为 P2，不阻塞首个 Alpha。
- `TC-CHG-010` 为 P1，因为首个 Alpha 必须诚实描述多文件事务边界。
- 用例的层级、自动化状态、执行证据和归属 PR 在 `docs/traceability/alpha-traceability.md` 维护。