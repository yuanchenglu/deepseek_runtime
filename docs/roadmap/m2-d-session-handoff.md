# DeepSeek Runtime M2-D 新会话交接提示词

> 状态日期：2026-07-29  
> 远程仓库：`https://github.com/yuanchenglu/deepseek_runtime.git`  
> 当前远程分支：`agent/m2-runtime-lifecycle`  
> 当前 PR：Draft PR #20 `feat(runtime): establish M2-D lifecycle and budget path`  
> 本文创建前的计划提交：`fa42bab14cf1643b6e1d22d3c3a8e0084bb05d24`  
> 发布结论：**NO RELEASE**

下面内容可直接复制到新会话：

---

你正在继续 `yuanchenglu/deepseek_runtime` 的 Open-source Alpha Hardening 工作。不要从记忆、旧容器或旧摘要推断仓库状态；GitHub 远程仓库是唯一事实源。

## 一、第一步：重新建立远程事实

仓库：

```text
https://github.com/yuanchenglu/deepseek_runtime.git
```

目标分支策略：

```text
develop = 开发分支
master = 发布分支
```

当前工作入口：

```text
branch: agent/m2-runtime-lifecycle
PR: #20 feat(runtime): establish M2-D lifecycle and budget path
base: develop
```

开始工作前必须动态获取并核对：

1. PR #20 当前是否仍 open/draft；
2. 当前真实 head SHA；
3. changed files；
4. 最新 Minimum CI、M1 P0 Gate、M2 ExecutionAdapter Gate、M2 Runtime Lifecycle Gate；
5. `docs/roadmap/open-source-readiness-plan.md`；
6. `docs/roadmap/m2-d-worklog.md`；
7. `docs/roadmap/m2-d-session-handoff.md`；
8. `docs/testing/m2-runtime-lifecycle-report.md`；
9. `docs/contracts/runtime-lifecycle.md`；
10. `docs/traceability/alpha-traceability.md`、PRD、Threat Model 和 README 的真实远程内容。

不要假设本文中的 SHA 在你开始时仍是最新值。

## 二、整体进展

已关闭：

- M0：治理、PRD、Traceability、Minimum CI；
- M1：核心合同和 P0；
- M2-A：ToolRegistry 唯一生产入口；
- M2-B：PermissionPolicy / ApprovalProvider；
- M2-C：ExecutionAdapter、受限子进程和三平台 Gate。

当前：

- M2-D Runtime Lifecycle、Budget、Cancellation 正在 Draft PR #20 实施；
- M2-E Workspace P1、M2-F CLI、M2-G Integrated Closeout 未开始；
- M3–M6 未开始或只有前置合同；
- 当前整体 Alpha 发布就绪度约 35%–40%，不得解释为接近发布；
- 发布结论始终为 `NO RELEASE`。

## 三、PR #20 已完成的主要工作

- 在现有 `DeepSeekRuntime` 内接入唯一 lifecycle，不创建第二套 Agent Loop；
- `LifecycleEvent`、`LifecycleTrace`、transition manifest 一致性 Gate；
- `TOOL_RUNNING → CANCELLED` 合法转换；
- Provider round / tool batch 生命周期；
- private `RecoverableCheckpoint` handoff；
- Provider message 在 `PROVIDER_COMPLETED` checkpoint 前写入；
- ASK 在 ApprovalProvider I/O 前保存 pending；
- Provider-before-call cancellation；
- pure tool cancellation 与 side-effect uncertain；
- step/token/USD cost/context/time budgets；
- unknown usage/cost 保持 unknown；
- `ToolErrorPolicy.CONTINUE/TERMINATE`；
- malformed Provider structured `RuntimeResult` subset；
- public usage evidence 数值白名单；
- side-effect success private structural receipt；
- UTF-8 bytes checkpoint compatibility；
- 三平台 M2 Runtime Lifecycle focused Gate；
- lifecycle contract、worklog、测试报告和严格 review tests。

## 四、当前必须先处理的 blocker

交接时已确认：当前 PR head 只有新的严格回归测试，尚未包含对应生产修复。

失败测试：

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

失败语义：

- 同一个 Provider response 有多个需要 ASK 的 tool call；
- 第二个 call 的 pending checkpoint 已生成；
- ApprovalProvider 返回最终 `approve-once` 后；
- Runtime 在进入 `ExecutionAdapter.execute()` 前没有再次 handoff 已解析 approval outcome 和该 call 的 `TOOL_RUNNING` 状态。

当前失败证据：

```text
Minimum CI run 205: failure
M2 Runtime Lifecycle Gate run 20: failure
M1 P0 Gate run 149: success
M2 ExecutionAdapter Gate run 55: success
```

较早的绿色 head `2d71808b3ae8963998416fc5eedbf8ece2d8fc52` 通过 runs 202/146/52/17，但不包含该严格回归测试，不能作为最终证据。

### 建议最小修复

保留并通过当前测试，不允许删除或降低断言。

重点检查：

```text
src/deepseek_runtime/runtime.py
```

`on_authorized()` 当前应当：

1. 设置当前 `checkpoint_call.state = RuntimeState.TOOL_RUNNING`；
2. 设置 `attempt_count = 1`；
3. 如果全局 lifecycle 已经是 `RuntimeState.TOOL_RUNNING`，调用 `handoff_current_state(step)`；
4. 该 handoff 必须发生在 `ExecutionAdapter.execute()` 之前；
5. `AuthorizationSession.authorize()` 返回时，pending event 已原位更新为最终 approval outcome，因此 handoff 应包含 `approve-once`。

同时严格审查：deny、timeout、unavailable 最终 outcome 是否也需要 resolved private checkpoint。若需要，增加回归测试和最小 callback，不得只修 approve happy path 后宣称 approval timing 完成。

## 五、修复后的完成顺序

1. 修复 approval resolved checkpoint 时序；
2. 运行相关 focused tests；
3. 以最终精确 head 等待并核对：
   - Minimum CI；
   - M1 P0 Gate；
   - M2 ExecutionAdapter Gate；
   - M2 Runtime Lifecycle Gate；
4. 所有 Gate 必须针对同一最终 head；
5. 保留所有失败 run，不 rerun-mask；
6. 获取 M2-D 三平台 artifact ID、digest、tests_run、failures/errors/skipped；
7. 严格审查 changed files，不混入 M2-E/M2-F/M3/M4/M5；
8. 同步 PRD、Traceability、Threat Model、双语 README、INDEX、test plan 和测试报告；
9. PR #20 未合入前只标 `Implemented/Partial`，不得标 `Verified`；
10. 更新 PR #20 body，写入最终 head、retained failures、最终 runs/artifacts、明确排除项；
11. 核验 review threads 和 unresolved P0/S0/S1；
12. Draft → Ready；
13. squash merge PR #20 到 `develop`；
14. 新建 docs-only M2-D closeout PR；
15. closeout 合入后将 M2-D 合入态 Requirement 提升为 Verified，并把 M2-E 标记为 NEXT。

## 六、M2-D 明确排除

不得混入：

- Workspace read/search P1 budgets（M2-E）；
- CLI stdout/report/json/exit-code（M2-F）；
- Provider streaming、retry、body-size、完整 arbitrary JSON normalization、in-flight cancellation（M4）；
- durable encrypted/locked checkpoint store、migration（M3）；
- ChangeManager/Evidence redesign（M3）；
- container/VM/kernel sandbox；
- packaging、release matrix、`master`、tag、release。

## 七、开发流程规范

以下规范适用于 5 个项目：

```text
deepseekagent
deepcode
deepseek_runtime
llm-harness-agent
oh-my-deepseek-harness
```

Remote：

```text
https://github.com/yuanchenglu/<项目名>.git
```

### 分支策略

- 开发分支为 `develop`；
- 发布分支为 `master`；
- `develop` 分支已取消 PR 强制保护，可以直接推送，但直推只作为兜底。

### 第一优先：走 PR 流程

1. 创建功能分支；
2. 提 Pull Request；
3. 等待 CI 通过；
4. 合入 `develop`；
5. 按项目 `docs/` 目录下的计划文档执行任务；
6. 确保 PR 标题和描述清晰说明变更内容。

### 第二优先：异常处理与直推

如果 PR 流程持续出问题，例如 CI 环境不可用、测试依赖无法安装或规则冲突：

1. 先分析原因：定位问题根因，确认是代码问题还是环境问题；
2. 尝试修复：如果是代码问题，例如缺少文件或配置错误，直接修复；
3. 解决不了再直推 `develop`：只有问题无法在当前环境解决时，才允许直推，不阻塞流程。

### 直推 `develop` 的纪律

Commit 信息必须包含“问题原因”和“技术债务”段落：

```text
<type>(<scope>): <变更说明>

## 问题原因
[写明为什么 PR 流程无法通过，根因是什么]

## 技术债务
- [列出本次遗留的未解决问题、待办事项]
```

示例：

```text
feat(auth): add login ticket validation

## 问题原因
CI 环境的 Playwright 依赖版本与本地不一致，E2E 测试在 CI 上无法运行。已手动验证本地通过。

## 技术债务
- Playwright 版本锁定需要统一管理
- E2E 测试在 CI 上需要单独排查
```

技术债务记录二选一：

方式 A：记录在 commit 信息中，推荐；

方式 B：记录在项目文档中：

```text
deepseekagent              → docs/TECH_DEBT.md 或 docs/BUG_LIST.md
deepcode                   → docs/BUG_LIST.md
deepseek_runtime           → docs/TECH_DEBT.md
oh-my-deepseek-harness     → docs/TECH_DEBT.md
llm-harness-agent          → TECH_DEBT.md（根目录）
```

每条格式：

```text
[日期] 描述 | 遗留原因 | 状态
```

核心原则：

- 能走 PR 就走 PR，直推是兜底方案，不是默认方案；
- 直推必须有交代，commit 要说清楚为什么以及留下了什么；
- 技术债务不怕有，怕没人知道；记录下来是解决的第一步。

## 八、工作方式要求

- 中文沟通，结论基于远程事实；
- 独立执行，不反复要求用户发送“继续”；
- 不承诺后台工作；
- 不删除或隐藏失败证据；
- 不降低测试、Ruff、Pyright 或安全合同；
- 不在 `master` 开发；
- 不在 M6 Gate 前发布；
- 远程 write 成功后必须再次 fetch PR/head/file 验证，不能只相信工具返回；
- 当前结论保持：`M2-D IN PROGRESS / PR #20 NOT MERGED / NO RELEASE`。

---
