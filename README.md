# DeepSeek Runtime

> 面向 DeepSeek API 的本地 Agent Runtime Kernel。
>
> **当前阶段：Open-source Alpha Hardening；M1、M2-A、M2-B 已关闭；M2-C ExecutionAdapter 在 Draft PR #18 实施中；当前发布结论：NO RELEASE。**

[English](README_en.md) | [简体中文](README.md)

## 项目定位

直接调用模型 API 并不等于获得一个可靠 Agent。Runtime 需要处理 Provider 协议、工具合同、权限审批、受限执行、资源预算、状态恢复、证据隐私和发布验证。

本仓库已完成 M1 的核心合同、Workspace containment、受约束回滚和不确定副作用恢复；M2-A 建立 ToolRegistry 唯一生产工具集合；M2-B 将 PermissionPolicy 与 ApprovalProvider 强制接入 Runtime。M2-C 正在 PR #18 建立统一 ExecutionAdapter 边界、受限子进程控制和三平台专项证据。完整 Runtime lifecycle、预算、Provider cancellation、durable checkpoint、Workspace P1、CLI 协议和发布工程仍未完成。首个公开 Alpha 的范围、优先级和验收标准以 [`docs/product/PRD.md`](docs/product/PRD.md) 为唯一事实源。

## 当前真实状态

| 能力 | 当前判断 |
| --- | --- |
| DeepSeek Provider 请求与基础响应处理 | Partial |
| Text-only 与基础 Tool Loop | Partial |
| ToolRegistry 与参数/结果边界 | Verified for M2-A；PR #14、Minimum CI run 106、M1 P0 Gate run 56 |
| Policy 与 Approval 强制闭环 | Verified for M2-B 内存生产路径；PR #16、runs 129/77 |
| ExecutionAdapter 强制闭环 | Implemented on Draft PR #18；代码完成态 runs 159/105，M2 Gate run 9 三平台各 36/36；尚未合入 |
| Restricted subprocess controls | Implemented on PR #18：minimal env、contained cwd、timeout、combined byte output、cancellation handoff、process-tree cleanup |
| Kernel / OS isolation | 不提供；所有当前 Adapter 均声明 `kernel_isolation=false` |
| Approval durable checkpoint / resume | Partial；持久化时机、恢复和 migration 属 M2-D/M3 |
| Complete cancellation | Partial；tool execution handoff 已实现，Provider 前/请求中 cancellation 属 M2-D/M4 |
| Workspace containment 与 symlink/reparse-point 防护 | Verified for M1 P0；Linux/macOS/Windows 各 20/20 |
| Workspace read/search budgets | Planned；M2-E |
| Checkpoint 与 Evidence | Partial；合同已冻结，生产存储仍需拆分 |
| 副作用恢复 | Verified for M1 P0；不确定非幂等副作用进入人工协调 |
| 文件变更与回滚 | Verified for M1 P0；opaque handle、durable ChangeJournal、expiry/scope/conflict 已覆盖 |
| 多平台 CI | M1 P0 与 M2-C Adapter 专项均覆盖 Linux/macOS/Windows + Python 3.11；完整 release matrix 仍 Planned |
| wheel/sdist、构件来源与完整性验证 | Planned/Blocked |

详细证据：

- [PRD](docs/product/PRD.md)
- [Threat Model](docs/security/threat-model.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [M1 P0 三平台报告](docs/testing/m1-p0-report.md)
- [M2-A ToolRegistry Closeout](docs/roadmap/m2-a-closeout.md)
- [M2-B Policy/Approval Closeout](docs/roadmap/m2-b-closeout.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [M2-C ExecutionAdapter Test Report](docs/testing/m2-execution-adapter-report.md)
- [开源就绪执行计划](docs/roadmap/open-source-readiness-plan.md)

## 当前生产工具调用链

PR #18 的目标路径为：

```text
Provider tool call
→ ToolRegistry resolve
→ JSON Schema validation
→ PermissionPolicy
→ ApprovalProvider（仅 ASK）
→ ExecutionAdapter
→ result normalization
→ content-minimized evidence
```

当前保证：

- Registry/schema/Policy/Approval 失败时 Adapter 和 handler 调用次数为 0；
- 默认 `NoIsolationLocalAdapter` 保持可信本地 Python handler 兼容，但明确不提供 timeout、运行中 cancellation、output limit、environment minimization、process cleanup 或隔离；
- `RestrictedSubprocessAdapter` 强制参数数组、`shell=False`、contained cwd、最小环境、secret/loader key 剥离、ToolSpec timeout、combined stdout/stderr byte limit、cancellation handoff 和 process-tree cleanup；
- execution event 不含 arguments、command、cwd、env、stdin、stdout、stderr、result 或异常正文；
- `WorkspaceSandbox.run()` 不再直接调用 `subprocess.run`，统一委托配置的 Adapter。

## 安全边界

当前实现**不是操作系统级安全沙箱**。

- `NoIsolationLocalAdapter` 仅适用于可信本地工具；
- `RestrictedSubprocessAdapter` 是 process-resource boundary，不提供 filesystem、network、syscall、user 或 kernel isolation；
- command classifier 不是隔离：包装命令可能被分类为 `SHELL_SAFE`；
- Restricted 子进程仍可能访问同一宿主用户有权访问的资源；
- process-tree cleanup 对 hostile process 仅为 best-effort，尽管三平台 fixture 已通过；
- Python command builder 是半可信代码，M2-C 不能阻止恶意 builder 在返回 request 前产生副作用；
- Workspace containment 不承诺抵抗同一用户权限下的恶意并发进程；
- Runtime 不承诺任意外部系统的 exactly-once。

完整边界见 [Threat Model](docs/security/threat-model.md) 和 [Security Policy](SECURITY.md)。

## 开发者快速开始

以下命令用于当前开发基线，不代表 Release Gate 已通过：

```bash
git clone https://github.com/yuanchenglu/deepseek_runtime.git
cd deepseek_runtime

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

deepseek-runtime doctor --json
python -m unittest discover -s tests -v
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

使用真实 API 前，仅使用无敏感业务内容的测试输入：

```bash
export DEEPSEEK_API_KEY=sk-your-key-here
deepseek-runtime run --workspace . "请描述这个项目的结构"
```

## 质量门禁

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
```

专项 Gate：

```bash
python scripts/m1_p0_gate.py --repetitions 20 --output m1-p0-local.json
python scripts/m2_execution_gate.py --output m2-execution-local.json
```

CI 结果才是可分享的执行证据；本地口头通过不构成发布证据。

## 文档

统一入口：[`docs/INDEX.md`](docs/INDEX.md)

- [产品架构](docs/architecture/product-architecture.md)
- [技术架构](docs/architecture/technical-architecture.md)
- [Runtime Core Contracts](docs/contracts/runtime-contracts.md)
- [Policy/Approval Contract](docs/contracts/policy-approval.md)
- [ExecutionAdapter Contract](docs/contracts/execution-adapter.md)
- [测试计划](docs/testing/test-plan.md)
- [测试用例](docs/testing/test-cases.md)
- [Known Unknowns](docs/known-unknowns.md)

## 贡献与支持

- [贡献指南](CONTRIBUTING.md)
- [支持策略](SUPPORT.md)
- [行为规范](CODE_OF_CONDUCT.md)
- [安全报告](SECURITY.md)

默认开发流程：功能分支 → Draft PR → tests/Traceability/docs/CI → strict review → Ready → `develop`。`master` 只用于通过最终 Release Gate 的发布。

## 许可与归属

Apache-2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
