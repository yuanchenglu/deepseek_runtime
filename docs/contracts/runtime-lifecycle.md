# Runtime Lifecycle、Budget 与 Cancellation 合同

> 状态：M2-D implementation contract
> 当前实现分支：`agent/m2-runtime-lifecycle`
> 当前实施 PR：#20
> 发布结论：**NO RELEASE**

## 1. 唯一生产循环

M2-D 只扩展现有 `DeepSeekRuntime`，不创建或维护第二套生产 Agent Loop。

```text
CREATED
→ PROVIDER_PENDING
→ PROVIDER_COMPLETED
→ TOOL_REQUESTED
→ APPROVAL_PENDING?
→ TOOL_RUNNING
→ TOOL_SUCCEEDED | TOOL_FAILED | TOOL_SIDE_EFFECT_UNCERTAIN
→ PROVIDER_PENDING
→ COMPLETED | FAILED | CANCELLED | BUDGET_EXCEEDED
```

状态转换必须经过 `validate_transition()`，并与 `docs/contracts/runtime-state-transitions.json` 一致。

## 2. 生命周期粒度

生命周期按 Provider round / tool batch 记录，而不是为同一 Provider response 中每个 tool call 建立第二套状态机。

- 单个 tool call 的 approval、execution、result 与 receipt 继续由 authorization/execution event 和 `ToolCallCheckpoint` 表达；
- 多 tool-call batch 只产生一次 `TOOL_RUNNING` 和一次 batch completion state；
- 第一个真实 ASK 可进入 `APPROVAL_PENDING`；同一 batch 后续 ASK 在 `TOOL_RUNNING` 状态下执行同状态 checkpoint handoff，不虚构未定义转换。

## 3. LifecycleEvent

公开事件只包含：

- sequence；
- event；
- source/target state；
- step；
- checkpoint_required。

禁止包含 prompt、response、reasoning、tool arguments/results、command、env、stdout/stderr、receipt 正文或异常正文。

## 4. Checkpoint handoff

`checkpoint_sink` 是同步、可注入的私有 checkpoint handoff：

- 每个 contract 标记为 checkpoint 的转换都生成 `RecoverableCheckpoint`；
- checkpoint 包含 messages、Provider continuation、tool-call states、approvals、receipts、budgets 和 recovery metadata；
- `PROVIDER_COMPLETED` checkpoint 必须已包含刚收到的 assistant message；
- 真实 ASK 在调用 ApprovalProvider 前写入 `approval_outcome="pending"` 并 handoff；
- approval 返回后 pending event 原位替换为最终 outcome；
- sink exception 结构化为 `INTERNAL_ERROR`，异常正文不公开；
- 该合同不等于 durable、encrypted、locked、migratable M3 store。

## 5. Cancellation

### 5.1 Provider 前

当 cancellation token 在 Provider call 前已取消：

- 不发送 Provider 请求；
- 状态进入 `CANCELLED`；
- 返回 `RuntimeResult`，error code 为 `CANCELLED`。

### 5.2 Tool 执行中

- cancellation token 传入 ExecutionAdapter；
- pure/non-side-effect tool 取消后进入 `CANCELLED`；
- side-effect tool 在无法确认结果时进入 `TOOL_SIDE_EFFECT_UNCERTAIN`，不得伪装为普通取消或自动重试；
- Restricted Adapter 继续负责 process-tree cleanup。

### 5.3 当前不保证

现有 Provider transport 不提供请求进行中的可靠 cancellation。M2-D 关闭 Provider-before-call；in-flight Provider cancellation 属 M4。

## 6. RuntimeBudgets

支持可选限制：

- `max_steps`；
- `max_tokens`；
- `max_cost_usd`；
- `max_context_tokens`；
- `max_elapsed_seconds`。

规则：

- limit 必须为有限正值；bool 不视为数字；
- step limit 在下一次 Provider call 前检查；
- token/cost/context/time 在达到或超过阈值时停止；
- Runtime 构造器 `max_steps` 与请求预算取较小值；
- 停止状态为 `BUDGET_EXCEEDED`，使用对应 machine-readable error code。

## 7. Unknown usage/cost

未知值必须保持 unknown：

- 缺少 token/cost 字段时不转换为 0；
- 不因 unknown 值虚构剩余预算；
- 只有认可的非负数值 usage 字段进入公开 evidence；
- 任意 Provider usage 字符串或未知键不进入公开 evidence；
- USD cost 只接受 `estimated_cost_usd` 或 `cost_usd`，通用 `cost` 不解释为美元。

## 8. Tool error policy

`ToolErrorPolicy`：

- `CONTINUE`：把结构化 tool error 作为 tool message 返回 Provider；
- `TERMINATE`：停止 Runtime，并保留原始 machine-readable error code；
- side-effect uncertain 不受 continue policy 自动继续或重试。

默认值为 `CONTINUE`，保持既有 Runtime 行为兼容。

## 9. Structured Provider boundary

M2-D 支持范围内：

- Provider client exception → `PROVIDER_ERROR`；
- 非对象 root、缺失/空 choices、非法 choice/message → `PROVIDER_RESPONSE_INVALID`；
- 非数组 tool_calls、非法 call id → `PROVIDER_RESPONSE_INVALID`；
- 所有路径返回 `RuntimeResult`，不公开异常正文。

完整 Provider arbitrary JSON、transport mapping、body limit、retry、streaming 与 in-flight cancellation 属 M4。

## 10. Side-effect receipt

- 成功完成的 side-effect Adapter 必须提供 private structural receipt；
- Fake/NoIsolation Adapter 在 handler 成功返回后生成仅含 adapter/tool/status 的 receipt；
- Restricted Adapter receipt 可包含 returncode、output byte count 和 truncation；
- receipt 不进入公开 execution event；
- 缺 receipt 的 side-effect success 不能进入 `TOOL_SUCCEEDED`，必须转为 uncertain；
- durable receipt storage/resume 属 M3。

## 11. RuntimeResult

新增安全字段：

- `runtime_state`；
- `lifecycle_events`；
- `budget`；
- private `checkpoint`。

`to_safe_dict()` 只输出 checkpoint 摘要：state、step、tool/approval/receipt counts，不输出 checkpoint 正文。

## 12. 验证映射

- `RUN-001` / `TC-RUN-001`；
- `RUN-002` / `TC-RUN-002/003`；
- `RUN-004` / `TC-RUN-005`；
- `RUN-005` / `TC-RUN-006`；
- `RUN-006` / `TC-RUN-012/013`；
- `RUN-007` / `TC-RUN-007`；
- `RUN-008` / `TC-RUN-008`；
- `RUN-010` / `TC-RUN-010`；
- `OBS-007` / `TC-OBS-006`；
- `SEC-003` approval-pending checkpoint timing subset。

当前结论：**NO RELEASE**。
