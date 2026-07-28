# M2-C ExecutionAdapter Closeout

> 状态：CLOSED
> 合并基线：`develop@7793a10152a49fb815aac667906080a4e1a39920`
> 实施 PR：#18 `feat(execution): establish M2-C ExecutionAdapter boundary`
> 发布结论：**NO RELEASE**

## 1. 关闭结论

M2-C 已建立 Runtime 的唯一 ExecutionAdapter 生产边界，并完成 Linux、macOS、Windows 三平台专项验证。该切片关闭的是进程执行合同、最小环境、cwd、timeout、byte output limit、cancellation handoff、process-tree cleanup、结构化错误与内容最小化证据；它不关闭完整 Runtime lifecycle、Provider-before-cancel、durable checkpoint/receipt、任务预算或内核隔离。

当前生产链为：

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

## 2. 合并事实

- 最终 PR head：`b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`；
- squash merge commit：`7793a10152a49fb815aac667906080a4e1a39920`；
- PR #18 changed files：20；
- strict review unresolved P0/S0/S1：0；
- review threads：0。

## 3. 已关闭能力

### 3.1 Adapter 合同

- 公共 `ExecutionAdapter` Protocol；
- `ExecutionContext`、`ExecutionOutcome`、`ExecutionCapabilities`；
- `CancellationToken`；
- `SubprocessRequest` 纯命令描述；
- capability 可机读，所有当前实现均声明 `kernel_isolation=false`。

### 3.2 实现

- `FakeExecutionAdapter`：确定性测试，不虚标 timeout/output/process cleanup/minimal env；
- `NoIsolationLocalAdapter`：可信本地进程内执行，明确无隔离；
- `RestrictedSubprocessAdapter`：
  - contained cwd；
  - minimal child environment；
  - secret、loader/runtime injection key 剥离；
  - registered timeout；
  - combined stdout/stderr byte limit；
  - cancellation polling；
  - timeout/cancel 后 process-tree cleanup；
  - handler/builder/Popen/cwd/pipe failure 结构化；
  - 不公开异常正文。

### 3.3 不可绕过性

- Runtime 在 Registry/schema/Policy/Approval 之后统一调用 Adapter；
- `WorkspaceSandbox.run()` 不再保留第二套直接 `subprocess.run` 生产路径；
- execution evidence 只记录 adapter、capability、duration、output bytes、truncation、return code、error code 等结构信息；
- command、env、stdin、stdout、stderr、arguments、result 和异常正文不进入公开 execution evidence。

## 4. 保留失败证据

### Minimum CI run 144 (`30342778701`)

新增 schema-negative 测试 helper 使用 `arguments or default`，错误地把显式空对象 `{}` 替换为合法默认参数，导致 unit failure。修复为区分 `None` 与显式 `{}`；未降低 JSON Schema、生产实现或测试断言。

该失败 run 保留，未 rerun、删除或隐藏。

## 5. 最终精确内容证据

最终 head：`b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`

- Minimum CI run 165 (`30345881483`)：PASS；
- M1 P0 Gate run 111 (`30345881511`)：Linux/macOS/Windows 全部 PASS；
- M2 ExecutionAdapter Gate run 15 (`30345881606`)：
  - Linux：36/36；
  - macOS：36/36；
  - Windows：36/36；
  - 总计：108/108；
  - failures/errors/skipped：0/0/0。

Artifacts：

| Platform | Artifact | Digest |
| --- | ---: | --- |
| Linux | `8682866620` | `cb57b08c75d0f897ac52c8e3af52be2b0d4baee65dc5dfe43d4c9022315565a8` |
| macOS | `8682871026` | `c8bd863f9114ff0a09faafb0525123772b1fec88dd54b4d7da1310cf0703d7eb` |
| Windows | `8682875863` | `a7369240153ee8095540e0015561e1ee80da7a9b3c802e4cc102927c61dcb3de` |

## 6. Requirement 关闭判断

- `TOOL-005`：Verified；ToolSpec timeout/output limit 已在 Adapter 执行期强制；
- `SEC-005`：Verified；类型、文档、capability 与负向测试明确命令 Gate/普通 subprocess 不等于隔离；
- `SEC-006`：Verified；子进程最小环境和 secret/loader-key 剥离有三平台证据；
- `SEC-007`：Verified；timeout/cancel process-tree cleanup 有三平台证据；
- `SEC-008`：Verified；Fake/NoIsolation/Restricted 三种实现与可辨识保证已合入；
- `SEC-009`：Verified for M2-C Adapter surfaces；完整仓库级隐私仍由 M3 Evidence/M5 release gate 独立验收；
- `RUN-006`：Partial；Adapter cancellation handoff 已实现，但 Provider-before-cancel、完整 lifecycle cancellation、checkpoint 与 final Runtime state 属 M2-D/M4。

## 7. 明确非保证

`RestrictedSubprocessAdapter` 不是 container、VM、seccomp、Seatbelt、Job Object 或其他内核 sandbox。它不能阻止已授权进程访问同一宿主用户可访问的资源，也不防御恶意 Tool builder 在构造 `SubprocessRequest` 前直接产生副作用。

M2-C 不关闭：

- Runtime 完整状态机与 lifecycle event；
- Provider 调用前取消；
- token/cost/context/time budgets；
- durable checkpoint timing/store；
- durable execution receipt 与恢复；
- Workspace read/search P1 budgets；
- CLI 协议；
- Provider streaming/retry；
- M3 Evidence totality/canonical/redaction；
- 内核隔离。

## 8. M2-D Handoff

下一切片为 **M2-D Runtime Lifecycle、Budget、Cancellation**。实施顺序：

1. 冻结生产 Runtime lifecycle 状态与事件映射；
2. 把关键转换接入 checkpoint handoff；
3. 实现 Provider-before-cancel 与 Adapter-during-cancel 的统一语义；
4. 实现 step/token/cost/context/time budgets；
5. 统一 tool error continue/terminate policy；
6. 补 malformed Provider total-function 边界；
7. 建立 M2-D 专项 Gate；
8. 更新 Traceability、Threat Model、PRD、README 与测试报告。

M2-D 不得重写第二套 Agent Loop，不得混入 Workspace P1、CLI、Provider streaming、M3 Recovery/Evidence 或发布工程。

当前结论：**NO RELEASE**。
