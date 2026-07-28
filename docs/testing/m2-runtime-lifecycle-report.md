# M2-D Runtime Lifecycle Test Report

> 状态：Implementation complete / pre-merge evidence finalization
> PR：#20 `feat(runtime): establish M2-D lifecycle and budget path`
> 分支：`agent/m2-runtime-lifecycle`
> 发布结论：**NO RELEASE**

## 1. 目标

本报告验证 M2-D 对现有 `DeepSeekRuntime` 的增量收口，不创建第二套生产 Agent loop。范围包括：

- Runtime state transition 与 lifecycle event；
- private `RecoverableCheckpoint` handoff；
- Approval pending/resolved checkpoint timing；
- Provider-before-call cancellation 与 tool-during-cancel 最终语义；
- step/token/USD-cost/context/time budgets；
- tool-error continue/terminate policy；
- supported malformed Provider subset 的结构化 `RuntimeResult`；
- side-effect private structural receipt；
- public evidence 内容最小化。

不属于本报告的范围：durable store、locking、migration、Workspace P1、CLI 协议、Provider streaming/retry/body-size/in-flight cancellation、M3 Evidence totality、packaging 或 release。

## 2. Blocker closure

原阻断测试：

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

根因是同一 Provider tool batch 的第二个及后续 ASK call 复用全局 `TOOL_RUNNING` 状态时，resolved approval outcome 未再次 handoff；Adapter 因而可能在缺少该 call 执行前快照的情况下启动。

修复保持单一生产 Runtime 状态机：

- pending 在 `ApprovalProvider` I/O 前 handoff；
- approve-once 与 approve-session 在 Adapter 执行前 handoff；
- deny、timeout、missing/failed provider、invalid outcome 在结构化返回前 handoff；
- global lifecycle 仍按 Provider round/tool batch；
- 未创建 per-tool 第二套生产状态机；
- 原回归未删除、跳过或降低断言。

新增回归：

- cached approve-session later-batch execution-before-adapter checkpoint；
- deny resolved checkpoint；
- timeout resolved checkpoint；
- ApprovalProvider missing/exception → unavailable resolved checkpoint；
- invalid outcome resolved checkpoint。

## 3. Focused Gate 分母

永久工作流：`.github/workflows/m2-runtime-lifecycle.yml`

执行环境：

```text
Linux + Python 3.11
macOS + Python 3.11
Windows + Python 3.11
```

模块分母：

```text
test_runtime_lifecycle
test_runtime_lifecycle_review
test_execution_runtime
test_tool_registry_runtime
test_policy_approval_runtime
test_policy_approval_audit_semantics
```

新增 approval matrix 后的预期测试分母为每个平台 64；最终 exact-head run、实际分母、artifact ID 和 digest 在 PR #20 的 final evidence 记录中锁定。文档更新后不得引用较早绿色 head 作为最终证据。

## 4. 已验证的实现边界

### 4.1 Runtime lifecycle

- text-only、单/多 tool call、multi-round；
- transition manifest 的合法转换；
- terminal result/error mapping；
- checkpoint sink 是私有 handoff，不宣称 durable persistence。

### 4.2 Approval checkpoint timing

- ASK pending before provider I/O；
- approve-once before Adapter；
- approve-session cache hit before later Adapter execution；
- deny/timeout/unavailable/invalid before structured tool result；
- Adapter/handler 在未授权时调用次数为 0。

### 4.3 Budgets

- max steps；
- token threshold；
- known USD cost threshold；
- unknown usage/cost 保持 unknown，不伪造为 0；
- context/time budget；
- budget stop 生成结构化 error/evidence。

### 4.4 Cancellation 与 side effects

- Provider call 前 cancellation；
- tool execution cancellation handoff；
- 无可靠 receipt 的非幂等 side effect 进入 uncertain/manual；
- 不盲目自动重试；
- in-flight Provider transport cancellation 明确留给 M4。

### 4.5 隐私

Public evidence 不包含：

- prompt/response 正文；
- tool arguments/results；
- command/cwd/env/stdin/stdout/stderr；
- private receipt 正文；
- exception 正文；
- checkpoint 恢复正文。

## 5. Retained failure history

以下失败不 rerun-mask、不删除、不用较早绿色 head 替代：

- Minimum CI runs 184、199：初始 lifecycle/typing/docs 收口期间的真实失败；
- Minimum CI runs 205、207：strict-review 修正期间的真实失败；
- Minimum CI run 211：later-batch approval checkpoint blocker；
- M2 Runtime Lifecycle Gate runs 1、13、16、20、22：实现与严格回归迭代中的真实失败；
- M2 Runtime Lifecycle Gate run 26：Linux/macOS/Windows 均由 later-batch approval checkpoint blocker 失败。

最终 exact-head run 必须是新增 approval matrix、权威文档和永久工作流全部落定后的新 run。

## 6. 先前可访问的非最终证据

在 approval matrix 与最终文档同步前，head `1d2b1377849800816641a800370eb1c916123125` 的以下 run 已通过，但只作为中间证据，不作为 PR 最终 exact-head 证据：

- Minimum CI run 214 (`30381265145`)；
- M1 P0 Gate run 158 (`30381265158`)；
- M2 ExecutionAdapter Gate run 64 (`30381265222`)；
- M2 Runtime Lifecycle Gate run 29 (`30381265198`)；
- lifecycle 三平台各 62/62，总计 186/186。

该中间 lifecycle artifacts：

- Linux `8697062524`, digest `7a5f8e98ceefc8d27d48c9f7d795bf344c0e18bf305a4d8ce490d0520d4f9719`；
- macOS `8697070995`, digest `cfadbb9bb8401a659372ad6e3b17398156f7c5e93cd693ee53cd79fe4bd8ed8b`；
- Windows `8697086273`, digest `dbbfb026ba24cfad6bafae873f8cd569fdb4d9c7a36fe9d332e79ab3111cba79`。

这些 artifact 不替代最终文档 head 的新 evidence。

## 7. Exit judgment

Implementation scope 已完成；在以下条件满足前不得将 M2-D 标记为 `Verified`：

- 永久工作流恢复；
- 最终 head 的 Minimum CI、M1 P0、M2 Adapter、M2 Runtime Lifecycle 全绿；
- final lifecycle artifacts、digests、实际分母可访问；
- changed files、review、review threads 和 claims strict review 完成；
- PR #20 Ready 并 squash merge 到 `develop`；
- docs-only closeout 在合并态更新 Requirement 为 `Verified`。

当前判断：**IMPLEMENTED / PRE-MERGE / NO RELEASE**。
