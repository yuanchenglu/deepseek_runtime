# DeepSeek Runtime

> 面向 DeepSeek API 的本地 Agent Runtime Kernel。
>
> **当前阶段：Open-source Alpha Hardening；M1 已通过集成态三平台门禁并关闭；当前发布结论：NO RELEASE。**

[English](README_en.md) | [简体中文](README.md)

## 项目定位

直接调用模型 API 并不等于获得一个可靠 Agent。Runtime 需要处理 Provider 协议、工具合同、权限审批、资源预算、状态恢复、证据隐私和发布验证。

本仓库已经完成 M1 的核心合同、Workspace containment、受约束回滚和不确定副作用恢复，但尚未完成不可绕过的 ToolRegistry、Policy、Approval、ExecutionAdapter 与统一 Runtime lifecycle。首个公开 Alpha 的范围、优先级和验收标准以 [`docs/product/PRD.md`](docs/product/PRD.md) 为唯一事实源。

## 当前真实状态

| 能力 | 当前判断 |
| --- | --- |
| DeepSeek Provider 请求与基础响应处理 | Partial |
| Text-only 与基础 Tool Loop | Partial |
| ToolRegistry、参数校验、Policy、Approval 强制闭环 | Blocked，M2 首要工作 |
| Workspace containment 与 symlink/reparse-point 防护 | Verified for M1 P0；Linux/macOS/Windows 各 20/20 |
| Checkpoint 与 Evidence | Partial；合同已冻结，生产存储仍需拆分 |
| 副作用恢复 | Verified for M1 P0；`running` 非幂等副作用进入人工协调，不自动重试 |
| 文件变更与回滚 | Verified for M1 P0；opaque handle、durable ChangeJournal、expiry/scope/conflict 已覆盖 |
| Evidence、Diagnostics、Usage/Cost | Partial |
| 多平台 CI | M1 P0 已覆盖 Linux/macOS/Windows + Python 3.11；完整发布矩阵仍 Planned |
| wheel/sdist、构件来源与完整性验证 | Planned/Blocked |

详细证据见：

- [完整 Code Review](docs/reviews/2026-07-27-code-review.md)
- [M1 Code Review Closeout](docs/reviews/2026-07-28-m1-closeout-review.md)
- [M1 P0 三平台报告](docs/testing/m1-p0-report.md)
- [M1 Integrated Closeout](docs/roadmap/m1-closeout.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [开源就绪执行计划](docs/roadmap/open-source-readiness-plan.md)

## 安全边界

当前实现**不是操作系统级安全沙箱**。

- `NoIsolationLocalAdapter` 只适用于可信本地开发环境；
- `RestrictedSubprocessAdapter` 的目标是最小环境、cwd、timeout、进程树清理、取消和输出限制，但仍不提供内核级隔离；
- Workspace containment 不承诺抵抗拥有相同主机用户权限的恶意并发进程；
- durable ChangeJournal 默认是 owner-only 本地存储，不等于加密；
- 当前版本不适合不可信多租户、任意命令执行或高价值不可逆副作用；
- Runtime 不承诺任意外部系统的 exactly-once；无法确认的副作用进入人工协调状态。

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

Windows PowerShell 激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

使用真实 API 前，请阅读安全边界，并仅使用无敏感业务内容的测试输入：

```bash
export DEEPSEEK_API_KEY=sk-your-key-here
deepseek-runtime run --workspace . "请描述这个项目的结构"
```

## 最小质量门禁

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
```

M1 P0 专项门禁：

```bash
python scripts/m1_p0_gate.py --repetitions 20 --output m1-p0-local.json
```

CI 结果才是可分享的执行证据；本地口头通过不构成发布证据。

## 文档

统一入口：[`docs/INDEX.md`](docs/INDEX.md)

核心文档：

- [PRD](docs/product/PRD.md)
- [产品架构](docs/architecture/product-architecture.md)
- [技术架构](docs/architecture/technical-architecture.md)
- [ADR](docs/adr/README.md)
- [测试计划](docs/testing/test-plan.md)
- [测试用例](docs/testing/test-cases.md)
- [Known Unknowns](docs/known-unknowns.md)

## 贡献与支持

- [贡献指南](CONTRIBUTING.md)
- [支持策略](SUPPORT.md)
- [行为规范](CODE_OF_CONDUCT.md)
- [安全报告](SECURITY.md)

默认开发流程是功能分支 → PR → CI → `develop`。只有 PR 流程在当前环境持续不可用时才允许异常直推 `develop`，且 commit 必须记录问题原因和技术债务。

首个 Alpha 原则上只接受关闭 P0/P1 阻断项、提高验证质量或修正文档事实的变更。

## 许可与归属

Apache-2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。