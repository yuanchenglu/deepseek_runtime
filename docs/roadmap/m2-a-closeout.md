# M2-A ToolRegistry Closeout

> 状态：**CLOSED**  
> 合入日期：2026-07-28  
> 实施 PR：#14 `feat(runtime): establish ToolRegistry production path`  
> 合并提交：`b012265c4f51238c97c26c22b76d1e5e043153dc`  
> 目标分支：`develop`  
> 发布结论：**NO RELEASE**

## 1. 关闭范围

M2-A 只关闭 ToolRegistry 唯一生产入口及其直接合同、测试和文档：

- `DeepSeekRuntime.run()` 只接受 `ToolRegistry | None`；
- CLI 默认使用 `WorkspaceTools(...).catalog()`，`--no-tools` 使用 `None`；
- 不保留裸 `dict[str, handler]` production fallback；
- `ToolSpec` 注册校验 handler、risk、side-effect、limits 和 `RecoveryPolicy`；
- JSON Schema Draft 2020-12 在 handler 前校验参数；
- Provider tool definitions 从 `ToolSpec` 生成；
- unknown tool、invalid result、handler exception 和 malformed tool-call 有结构化边界；
- safe `RuntimeResult` serialization 不因 malformed tool-call 崩溃。

## 2. Requirement 与 Test

| Requirement | Test Case | 结论 |
| --- | --- | --- |
| RUN-003 | TC-RUN-004 | Registry-only Runtime API 已验证 |
| RUN-009 | TC-RUN-009 | 确定性结果规范化与非法结果拒绝已验证 |
| TOOL-001 | TC-TOOL-001 | 完整 ToolSpec/Provider definition 已验证 |
| TOOL-002 | TC-TOOL-002 | duplicate registration 拒绝已验证 |
| TOOL-003 | TC-TOOL-003 | schema-before-handler 已验证 |
| TOOL-004 | TC-TOOL-004 | side-effect/risk/recovery 注册一致性已验证 |
| TOOL-007 | TC-RUN-011 | unknown tool 零 handler 执行已验证 |

额外回归覆盖 malformed JSON、function 非 object、arguments 非 string、tool-call ID 非法、non-UTF-8 bytes、mixed-key result、handler exception、CLI Registry 迁移和安全序列化。

## 3. 保留的失败证据

### Minimum CI run 92 — FAIL

- Pyright：`src/deepseek_runtime/cli.py:93`；
- 根因：Runtime API 已迁移到 `ToolRegistry | None`，CLI 仍有裸 `{}` fallback；
- 处理：完成 CLI Registry 迁移，未使用 cast、忽略或规则降级。

### Minimum CI run 98 — FAIL

- Pyright 已清零；
- unit tests 暴露 malformed `function` 在 Runtime 校验前触发旧 Evidence helper 崩溃；
- 处理：为 Evidence 构造非执行安全结构视图，不修改原始 Provider 消息，不降低断言。

失败 run 未 rerun、删除或覆盖。

## 4. 最终证据

最终 PR head：`a51d5b297d8233c654cc1569c5fe73b9730c28b6`。

- Minimum CI run 106 (`30330564130`)：**PASS**；
- M1 P0 Gate run 56 (`30330564099`)：**PASS**；
- Linux、macOS、Windows / Python 3.11：全部 PASS；
- 严格 Code Review：未解决 P0/S0/S1 = 0；
- PR #14：Ready 后 squash 合入 `develop`；
- merge commit：`b012265c4f51238c97c26c22b76d1e5e043153dc`。

## 5. 明确未关闭

M2-A 不代表整个 M2 完成。以下仍为独立阻断项：

1. M2-B Policy 与 Approval；
2. M2-C ExecutionAdapter、timeout/output/process-tree enforcement；
3. M2-D Runtime lifecycle、budgets、cancellation；
4. M2-E Workspace P1；
5. M2-F CLI 核心协议；
6. M2-G integrated closeout。

## 6. 下一步

从最新 `develop@b012265c4f51238c97c26c22b76d1e5e043153dc` 创建独立 `agent/m2-policy-approval` 分支和 Draft PR，先冻结 Policy/Approval 最小生产合同，再接入 ToolRegistry 执行路径。

M2–M6 完成前不得合入 `master` 或发布 tag；继续保持 **NO RELEASE**。
