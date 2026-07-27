# DeepSeek Runtime

> 面向 DeepSeek API 的本地 Agent Runtime Kernel。
>
> **当前阶段：Open-source Alpha Hardening；当前发布结论：NO RELEASE。**

[English](README_en.md) | [简体中文](README.md)

## 项目定位

直接调用模型 API 并不等于获得一个可靠 Agent。Runtime 需要处理 Provider 协议、工具合同、权限审批、资源预算、状态恢复、证据隐私和发布验证。

本仓库当前包含这些基础原语，但尚未完成不可绕过的端到端执行闭环。首个公开 Alpha 的范围、优先级和验收标准以 [`docs/product/PRD.md`](docs/product/PRD.md) 为唯一事实源。

## 当前真实状态

| 能力 | 当前判断 |
| --- | --- |
| DeepSeek Provider 请求与基础响应处理 | Partial |
| Text-only 与基础 Tool Loop | Partial |
| ToolRegistry、参数校验、Policy、Approval 强制闭环 | Blocked |
| Workspace containment 与 symlink/reparse-point 防护 | Blocked，存在 P0 修复项 |
| Checkpoint 与 Evidence | Partial，当前模型需要拆分 |
| 副作用恢复 | Blocked，不确定副作用不得自动重试 |
| 文件变更与回滚 | Blocked，handle 与冲突语义需要加固 |
| Evidence、Diagnostics、Usage/Cost | Partial |
| 多平台 CI、wheel/sdist、构件来源与完整性验证 | Planned/Blocked |

详细证据见：

- [完整 Code Review](docs/reviews/2026-07-27-code-review.md)
- [当前测试报告](docs/testing/test-report-2026-07-27.md)
- [Alpha Traceability](docs/traceability/alpha-traceability.md)
- [开源就绪执行计划](docs/roadmap/open-source-readiness-plan.md)

## 安全边界

当前实现**不是操作系统级安全沙箱**。

- `NoIsolationLocalAdapter` 只适用于可信本地开发环境；
- `RestrictedSubprocessAdapter` 的目标是最小环境、cwd、timeout、进程树清理、取消和输出限制，但仍不提供内核级隔离；
- 当前版本不适合不可信多租户、任意命令执行或高价值不可逆副作用；
- Runtime 不承诺任意外部系统的 exactly-once；无法确认的副作用必须进入人工协调状态。

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

## M0 最小质量门禁

```bash
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
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

首个 Alpha 原则上只接受关闭 P0/P1 阻断项、提高验证质量或修正文档事实的变更。

## 许可与归属

Apache-2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
