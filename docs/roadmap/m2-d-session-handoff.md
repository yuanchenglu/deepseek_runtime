# DeepSeek Runtime M2-D 新会话交接提示词

> 状态日期：2026-07-29  
> 远程仓库：`https://github.com/yuanchenglu/deepseek_runtime.git`  
> 当前远程分支：`agent/m2-runtime-lifecycle`  
> 当前 PR：Draft PR #20 `feat(runtime): establish M2-D lifecycle and budget path`  
> 发布结论：**NO RELEASE**

## 使用说明

本文件保留 M2-D 现场信息，但新会话不应只完成 M2-D 后停止。

请优先复制并使用：

```text
docs/roadmap/full-plan-autonomous-handoff.md
```

该提示词要求新会话：

- 先动态核验 GitHub 远程事实；
- 关闭 PR #20 当前 approval checkpoint blocker；
- 完成并合入 M2-D；
- 自动连续推进 M2-E、M2-F、M2-G、M3、M4、M5、M6；
- 不等待用户反复发送“继续”；
- 每个阶段均按 PR-first、exact-head CI、docs-only closeout 和 retained-failure 纪律执行；
- 只有在全部 M6 Release Gate 通过后才允许更新 `master`、创建 tag 或发布 Alpha；
- 遇到必须由用户提供密钥、权限、签名或外部人工审核的硬阻断时，先将所有工作推送远程并留下精确交接。

## 当前 M2-D 现场

开始时必须重新读取 PR #20 的实时状态，不能假设以下信息仍最新。

当前已知 blocker：

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

失败语义：同一 tool batch 中后续 ASK 的 pending checkpoint 已生成，但 resolved approval outcome 和该 call 的执行前 checkpoint 尚未在 `ExecutionAdapter.execute()` 前可靠 handoff。

不得删除、跳过或降低该回归测试。

当前工作入口：

```text
repository: yuanchenglu/deepseek_runtime
branch: agent/m2-runtime-lifecycle
PR: #20
base: develop
```

开始执行前必须动态读取：

1. PR #20 当前 head、changed files、reviews、review threads；
2. Minimum CI、M1 P0 Gate、M2 ExecutionAdapter Gate、M2 Runtime Lifecycle Gate；
3. `docs/roadmap/open-source-readiness-plan.md`；
4. `docs/roadmap/full-plan-autonomous-handoff.md`；
5. `docs/roadmap/m2-d-worklog.md`；
6. PRD、Traceability、Threat Model、test plan、双语 README、INDEX；
7. 仓库当前开放 PR 和最新 `develop`。

## 开发流程规范

适用于：

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

- `develop` 为开发分支；
- `master` 为发布分支；
- 第一优先走功能分支 → PR → CI → 合入 `develop`；
- `develop` 直推只用于 PR 流程无法解决的异常兜底；
- 直推 commit 必须包含“问题原因”和“技术债务”；
- 技术债务必须记录到 commit 或项目规定的 TECH_DEBT/BUG_LIST 文档；
- 不能用直推绕过真实代码失败、安全门禁或发布门禁。

完整执行规则、里程碑顺序、停止条件和发布条件见：

```text
docs/roadmap/full-plan-autonomous-handoff.md
```
