# DeepSeek Runtime 技术架构

> 状态：Current + Target Architecture  
> 适用基线：`develop@7793a10152a49fb815aac667906080a4e1a39920`  
> 当前阶段：M1、M2-A、M2-B、M2-C Closed；M2-D Next  
> 发布结论：**NO RELEASE**

## 1. 架构目标

DeepSeek Runtime 是 local-first Agent Runtime Kernel。核心目标不是扩展更多 Agent 功能，而是建立一条可验证、不可静默绕过、失败可解释的生产执行链：

```text
Provider
→ DeepSeekRuntime
→ ToolRegistry / JSON Schema
→ PermissionPolicy / ApprovalProvider
→ ExecutionAdapter
→ trusted local handler or bounded subprocess
→ deterministic result normalization
→ content-minimized Runtime evidence
```

M2-C 已关闭授权后执行边界。M2-D 下一步关闭生产状态机、lifecycle event、checkpoint handoff、完整取消和任务预算；它不创建第二套 Agent loop。

## 2. 当前模块与成熟度

| 模块 | 当前职责 | 当前状态 |
| --- | --- | --- |
| `client.py` | HTTP、SSE、ProviderResult、配置 | Partial；normalization、retry、真正增量流式与请求中取消仍未完成 |
| `runtime.py` | Provider/tool loop、Registry、Policy、Approval、Adapter 编排 | M2-A/B/C 已合入；lifecycle/budget/full cancellation 属 M2-D |
| `contracts/*` | Error、State、Tool、Checkpoint、Evidence、Recovery、Journal | M1/M2-A 最小合同已冻结 |
| `approval.py` | Policy/Approval 强制链与内容最小化事件 | Verified for M2-B 内存路径；durable timing/resume Partial |
| `execution.py` | Adapter 合同、Fake/NoIsolation/RestrictedSubprocess | Verified for M2-C；三平台专项 Gate |
| `workspace.py` | canonical resolver、link/reparse-point containment | Verified for M1 P0 |
| `security.py` | PermissionPolicy、WorkspaceSandbox compatibility、ChangeManager | 命令路径统一委托 Adapter；类名不代表内核隔离 |
| `session.py` | Session/ToolCallRecord、恢复原语 | Partial；未统一接入最终 lifecycle |
| `evidence.py` | 请求/响应结构证据与脱敏 | Partial；M3 totality/canonical/privacy 未完成 |
| `observability.py` | usage、cost、成功率汇总 | Partial；unknown 与预算语义未收口 |
| `cli.py` | doctor/run | Partial；M2-F 输出和 exit-code 协议未完成 |
| `.github/workflows/*` | Minimum CI、M1 P0 Gate、M2 Adapter Gate | M2-C 三平台专项 Gate 已合入并在 develop push 继续执行 |

## 3. 当前生产调用链

```mermaid
flowchart LR
    Provider[Provider tool call]
    Runtime[DeepSeekRuntime]
    Registry[ToolRegistry]
    Schema[JSON Schema]
    Policy[PermissionPolicy]
    Approval[ApprovalProvider]
    Adapter[ExecutionAdapter]
    Local[NoIsolationLocalAdapter]
    Restricted[RestrictedSubprocessAdapter]
    Result[ExecutionOutcome]
    Evidence[Execution Evidence]

    Provider --> Runtime
    Runtime --> Registry
    Registry --> Schema
    Schema --> Policy
    Policy --> Approval
    Approval --> Adapter
    Adapter --> Local
    Adapter --> Restricted
    Local --> Result
    Restricted --> Result
    Result --> Runtime
    Runtime --> Evidence
```

强制顺序：

1. Provider tool-call shape 校验；
2. Registry lookup；
3. JSON Schema 参数校验；
4. Policy decision；
5. ASK approval；
6. Adapter execution；
7. result normalization；
8. authorization/execution evidence。

Registry/schema/Policy/Approval 失败时 Adapter 与 handler 调用次数为 0。

## 4. Tool 与授权合同

### 4.1 ToolRegistry

- `ToolRegistry` 是 `DeepSeekRuntime` 接受的生产工具集合；
- ToolSpec 声明名称、schema、risk、side effect、timeout、output limit 和 recovery policy；
- Provider definition 从 ToolSpec 生成；
- malformed call、unknown tool、invalid arguments/result 返回结构化错误；
- Runtime 不接受裸 handler mapping。

### 4.2 Policy 与 Approval

- READ 默认 ALLOW，非 READ 默认 DENY；
- rule 使用确定性 last-match precedence；
- path 缺失不匹配具体 path rule；
- ASK 必须经过 ApprovalProvider；
- approve once、exact-request session、deny、timeout、unavailable 已实现；
- 未授权时 Adapter 不执行；
- authorization event 内容最小化；
- durable approval checkpoint timing/resume/migration 属 M2-D/M3。

## 5. ExecutionAdapter 模型

### 5.1 公共合同

```python
class ExecutionAdapter(Protocol):
    name: str
    capabilities: ExecutionCapabilities

    def execute(
        self,
        spec: ToolSpec,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionOutcome: ...
```

`ExecutionCapabilities` 明确：isolation level、timeout、cancellation、byte output limit、process-tree cleanup、minimal environment 与 kernel isolation。当前所有 Adapter 均为 `kernel_isolation=false`。

### 5.2 FakeExecutionAdapter

- deterministic scripted outcome；
- 不调用 handler；
- 用于 ordering、failure、cancellation 和 evidence 测试；
- 不虚标 timeout、output、process-tree、minimal-env 或 kernel isolation。

### 5.3 NoIsolationLocalAdapter

- 当前 Python 进程内调用可信 handler；
- 保持 read/search 等 Python 工具兼容；
- handler exception 转为结构化 `TOOL_EXECUTION_FAILED`，不发布异常正文；
- 开始前可识别 cancellation；
- 不提供 timeout、运行中 cancellation、输出限制、环境最小化、进程清理或 OS 隔离。

这是显式低保证 Adapter，不得被描述为 sandbox。

### 5.4 RestrictedSubprocessAdapter

注册 handler 是纯 command builder，返回 `SubprocessRequest`。

已验证控制：

- command 是非空参数 tuple，`shell=False`；
- cwd 经过 `WorkspaceResolver` containment；
- child environment 从小型 host allowlist 构建；
- API key、token、authorization、password、credential、secret 等键被移除；
- `PYTHONPATH`、`PYTHONHOME`、`LD_*`、`DYLD_*`、`NODE_OPTIONS` 等 loader/runtime 注入键被移除；
- ToolSpec `timeout_seconds` 实际驱动终止；
- stdout/stderr 合并按 byte 限制；
- stdin 在独立线程写入，不阻塞 timeout/cancellation loop；
- timeout/cancel/output overflow 触发 process-tree cleanup；
- Windows 使用 `taskkill /T /F`，辅助进程也使用最小环境；
- Unix 使用独立 process group 和 TERM/KILL；
- builder/spawn/cwd/pipe 异常结构化，不公开异常正文；
- pipe reader failure 不会静默成为残缺成功。

该 Adapter 是 process-resource boundary，不是 kernel sandbox；同一宿主用户可访问的文件、网络和系统调用仍可能被 child 访问。

## 6. WorkspaceSandbox 兼容路径

`WorkspaceSandbox.run()` 已从直接 `subprocess.run` 迁移为：

```text
command array validation
→ risk classification
→ cwd containment
→ PermissionPolicy
→ temporary ToolSpec/SubprocessRequest
→ configured ExecutionAdapter
→ CommandResult compatibility envelope
```

默认使用 `RestrictedSubprocessAdapter`。`WorkspaceSandbox` 名称是兼容名称，不构成隔离保证。

## 7. ExecutionOutcome 与 Evidence

私有 `ExecutionOutcome` 可包含：结果、adapter/capability、duration、output bytes、truncated、return code 与 private receipt。

公开 execution event 仅包含：tool、adapter、capability、status、duration、output byte count、truncated、return code、error code/cause class。

禁止进入公开 event：

- tool arguments；
- command/cwd；
- env/stdin；
- stdout/stderr；
- result/private receipt；
- handler/builder/adapter exception message。

`ExecutionOutcome.private_receipt` 尚未接入 durable checkpoint；属于 M2-D/M3。

## 8. M2-D 生命周期目标

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

M2-D 必须补：

- production state 与 transition manifest 对齐；
- lifecycle event ordering；
- checkpoint handoff；
- Provider 调用前 cancellation；
- tool-during-cancel 最终 Runtime state；
- step/token/cost/context/time budgets；
- unknown usage/cost 保持 unknown；
- tool error continue/terminate policy；
- malformed Provider 的结构化 RuntimeResult 边界。

请求进行中的 transport cancellation 若现有 client 不支持，允许明确移交 M4，但不得虚报已完成。

## 9. Checkpoint、恢复与 Change

现有合同区分：

```text
RecoverableCheckpoint
- messages/provider continuation
- tool states/arguments/results
- approvals/receipts/budgets
- private/recoverable

PublishableEvidence
- structure/status/usage/safe metadata
- no recoverable content
```

M2-D 负责 lifecycle checkpoint handoff；M3 负责 durable/encrypted/locked store、migration 和完整 recovery matrix。

ChangeManager 继续使用 canonical resolver、PermissionPolicy、opaque RollbackHandle、durable ChangeJournal、workspace binding、expiry 与 pre/post hash。M3 仍需 lock、parent fsync、metadata policy、duplicate path 和完整 fault matrix。

## 10. 信任边界

| 边界 | 默认信任 | 必须防御 |
| --- | --- | --- |
| 模型输出 | 不可信 | tool name、JSON、路径、命令、超长输出 |
| 用户 prompt | 敏感但合法 | 日志泄漏、间接命令注入 |
| Tool handler/builder | 半可信 | exception、直接副作用、错误结果、secret 泄漏 |
| ExecutionAdapter | 可替换基础设施 | capability 虚标、timeout/cancel 失效、原生异常 |
| 子进程 | 不可信 | inherited env、cwd escape、无限输出、残留进程 |
| 工作区文件 | 不可信 | traversal、symlink/reparse、二进制、巨型文件 |
| Provider response | 不可信 | arbitrary JSON、协议漂移 |
| Checkpoint store | 本地主机可访问 | 明文、篡改、损坏 |
| Release tree | 不可信 | `.env`、未跟踪 secret、构建污染 |

## 11. 三平台验证

M2 ExecutionAdapter Gate run 15 在 Ubuntu、macOS、Windows + Python 3.11 各运行 36/36，总计 108/108，0 failures/errors/skips。

Gate 直接覆盖 Adapter capability、minimal environment、loader env stripping、cwd containment、timeout、byte output、blocking stdin、cancellation handoff、descendant cleanup、Runtime ordering、WorkspaceSandbox migration、exception/evidence privacy 与 command Gate 非隔离声明。

每个 job 上传明确分母的 JSON evidence。workflow 不自动取消旧运行，并在合入 `develop` 后继续执行。

## 12. Deferred / non-goals

M2-D 不实现：

- Docker/Podman adapter 或 OS/kernel sandbox；
- Workspace read/search P1 budgets；
- CLI stdout/report/JSON 协议；
- Provider streaming/retry/body-size/完整 normalization；
- durable encrypted checkpoint store；
- M3 Evidence totality/canonical redesign；
- hosted/multi-tenant security boundary；
- packaging/release engineering。

## 13. 架构决策

- ADR-001：Runtime 是 local-first kernel，不做 hosted control plane。
- ADR-002：Checkpoint 与 Evidence 分离。
- ADR-003：Command Gate 不等于 sandbox。
- ADR-004：ToolSpec/ToolRegistry 是 Runtime 工具合同入口。
- ADR-005：Side-effect recovery 不承诺通用 exactly-once。
- M2-C：ExecutionAdapter 是授权后唯一执行边界；capability 必须可测试且不虚标。
- M2-D：只扩展现有 DeepSeekRuntime 生命周期，不维护第二套生产 Agent loop。
