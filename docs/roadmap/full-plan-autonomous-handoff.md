# DeepSeek Runtime 全 Plan 自主执行交接提示词

> 状态日期：2026-08-03
> 远程仓库：`https://github.com/yuanchenglu/deepseek_runtime.git`
> 当前开发分支：`develop`
> 当前 HEAD：`7d148c5`（docs(readiness): close M2-F CLI Core milestone）
> 已关闭：M0、M1、M2-A、M2-B、M2-C、M2-D、M2-E、M2-F
> 当前实施入口：M2-G Integrated Closeout
> 权威计划：`docs/roadmap/open-source-readiness-plan.md`
> 发布结论：**NO RELEASE，直到 M6 全部 Release Gate 真实通过**

下面正文可直接复制到新会话。

---

你正在接管 `yuanchenglu/deepseek_runtime` 的 Open-source Alpha Hardening 全计划执行。

你的任务不是只完成当前 PR，也不是只给出分析、建议或下一步清单。你的任务是：**从 GitHub 远程仓库的当前真实状态开始，连续、独立地执行 `docs/roadmap/open-source-readiness-plan.md` 中所有尚未完成的工作，依次关闭 M2-G、M3、M4、M5、M6，直到满足最终发布门禁，或者遇到必须由用户提供权限、凭据或外部人工结果才能解除的硬阻断。** 不得在每完成一个小步骤后停下来等待用户发送"继续"。一个阶段关闭后，立即进入下一个阶段。

不得在每完成一个小步骤后停下来等待用户发送“继续”。一个阶段关闭后，立即进入下一个阶段。

## 一、唯一事实源

GitHub 远程仓库是唯一事实源：

```text
https://github.com/yuanchenglu/deepseek_runtime.git
```

分支：

```text
develop = 开发分支
master = 发布分支
```

开始工作前必须动态读取，而不是相信本提示词中的旧 SHA：

1. Draft PR #20 当前状态、base、head、真实 head SHA；
2. PR #20 changed files、review threads、reviews；
3. 当前 head 对应的 Minimum CI、M1 P0 Gate、M2 ExecutionAdapter Gate、M2 Runtime Lifecycle Gate；
4. `docs/roadmap/open-source-readiness-plan.md`；
5. `docs/roadmap/m2-d-session-handoff.md`；
6. `docs/roadmap/m2-d-worklog.md`；
7. `docs/contracts/runtime-lifecycle.md`；
8. `docs/testing/m2-runtime-lifecycle-report.md`；
9. `docs/product/PRD.md`；
10. `docs/traceability/alpha-traceability.md`；
11. `docs/security/threat-model.md`；
12. `docs/testing/test-plan.md`；
13. `README.md`、`README_en.md`、`docs/INDEX.md`；
14. 当前开放 PR、最近 develop commits 和仓库实际分支状态。

不得从旧容器、旧摘要或记忆推断文件是否已经提交。每次远程 write 后都必须重新 fetch PR、head 或文件验证。

## 二、总任务与完成定义

你必须一次性自主推进整个 Plan：

```text
当前 M2-D
→ M2-D implementation merge
→ M2-D docs-only closeout
→ M2-E Workspace P1
→ M2-E closeout
→ M2-F CLI 核心
→ M2-F closeout
→ M2-G Integrated Closeout
→ M3 Recovery / Change / Evidence / Observability
→ M3 closeout
→ M4 Provider / Config / Protocol
→ M4 closeout
→ M5 CI Matrix / Packaging / Governance
→ M5 closeout
→ M6 RC / Alpha Release Gate
→ 只有全部 Gate 通过后才允许更新 master、创建 tag 或发布 Alpha
```

“完成整个 Plan”必须同时满足：

- PRD 中全部 P0/P1 Requirement 为 `Verified`；
- Traceability 中每个 P0/P1 Requirement 都有 Milestone、PR、Test、Evidence；
- Active P0/P1 defect = 0；
- unresolved S0/S1 = 0；
- 所有规定 CI、OS/Python matrix、artifact、digest、tamper、clean-install、live smoke、governance 和 claim audit 通过；
- 最终 RC 报告和 Release Decision 有可访问证据；
- 仅在 Release Gate 通过后将发布结果合入 `master` 并执行计划允许的 tag/release；
- 任一 Gate 不满足时，结论必须继续保持 `NO RELEASE`，并继续修复，而不是降低标准。

## 三、自主执行规则

### 3.1 不等待“继续”

- 不要在每个文件、commit、PR 或 milestone 后询问是否继续；
- 不要只汇报计划而不执行；
- 不要因为任务规模大而停止在分析阶段；
- 完成当前最小切片后立即进入下一切片；
- 只有遇到本文“允许停止的硬阻断”时才能停下。

### 3.2 每个切片的固定循环

对每个 M2-D 至 M6 的实施切片，执行：

```text
读取最新 develop 和权威文档
→ 锁定 Requirement/Test/Evidence 范围
→ 创建 agent/<scope> 功能分支
→ 创建 Draft PR
→ 实现代码与测试
→ 运行 focused gate 和全量回归
→ 保留失败证据并做根因修复
→ 同步 PRD / Traceability / Threat Model / README / INDEX / test report
→ strict code/security/claim review
→ 获取最终 exact-head CI 与 artifacts
→ Ready for Review
→ squash merge 到 develop
→ 创建 docs-only closeout PR
→ 在合并态提升 Verified
→ closeout merge
→ 从最新 develop 自动进入下一切片
```

不得把多个高风险 milestone 混入一个无法审查的巨型 PR。可以连续创建多个 PR，但不等待用户确认。

### 3.3 精确 head 纪律

- 所有最终 Gate 必须对应同一个最终 head；
- 不能用较早绿色 commit 代替包含新回归测试的当前 head；
- 文档提交会改变 head，因此文档同步后必须重新跑最终 Gate；
- 不得通过 rerun、删除测试、降低断言、跳过平台或只引用成功 job 掩盖失败；
- retained failure 必须写入 PR body、test report 或 closeout。

## 四、当前 M2-D 首要 blocker

首先动态验证以下测试是否仍失败：

```text
tests/test_runtime_lifecycle_review.py::
RuntimeLifecycleReviewTests::
test_later_batch_approval_is_checkpointed_before_execution
```

已知语义：同一 tool batch 中后续 ASK 的 pending checkpoint 已存在，但 resolved approval outcome 和当前 call 的执行前 checkpoint 尚未在 `ExecutionAdapter.execute()` 前可靠 handoff。

不得删除或降低该回归测试。

优先检查：

```text
src/deepseek_runtime/runtime.py
src/deepseek_runtime/approval.py
```

必须验证 approve-once、approve-session、deny、timeout、unavailable、invalid outcome 的 resolved private checkpoint 时序。修复必须保持：

- global lifecycle 仍按 Provider round / tool batch；
- 不创建第二套 per-tool 状态机；
- pending 在 host approval I/O 前 handoff；
- resolved outcome 在 Adapter 执行或结构化返回前 handoff；
- public Evidence 不包含 tool arguments、prompt、response、receipt 或异常正文；
- durable store、locking、migration 仍属于 M3，不得在 M2-D 过度声明。

关闭该 blocker 后完成 PR #20 的 exact-head 四套 Gate、artifact、strict review、Ready、merge 和 docs-only closeout，然后自动进入 M2-E。

## 五、后续里程碑必须连续执行

### 5.1 M2-E Workspace P1

按 PRD/Traceability 实现并验证：

- UTF-8 byte-safe truncation；
- read byte limit；
- search file/byte/time budgets；
- binary、permission、file-disappeared 等结构化结果；
- 不绕过 `WorkspaceResolver`；
- Linux/macOS/Windows 差异进入测试证据。

关闭并 closeout 后自动进入 M2-F。

### 5.2 M2-F CLI 核心

实现并验证：

- stdout 只承载最终回答；
- stderr 承载进度和诊断；
- `--report`；
- `--json`；
- unsafe/debug 明示；
- 稳定 exit-code matrix；
- workspace/provider/runtime 错误 UX；
- 默认输出不泄露 API Key、prompt、tool arguments 或 checkpoint 正文。

关闭并 closeout 后自动进入 M2-G。

### 5.3 M2-G Integrated Closeout

在最新 integrated `develop` 上复跑完整 M2 Requirement/Test matrix。确认：

- Registry/Policy/Approval/Adapter 无受支持生产 bypass；
- transition 合法/非法类别覆盖；
- Runtime/Tool/Workspace/Security/CLI P1 全部达到 M2 exit criteria；
- 未关闭项真实转移到 M3/M4，而不是用文档模糊处理。

### 5.4 M3

按计划完成：

- checkpoint 与 Evidence 分离；
- atomic save、fsync、locking、corruption handling、migration；
- optional encryption 的真实边界；
- crash-window recovery；
- ChangeManager conflict/fsync/metadata；
- Evidence totality、canonical identity、redaction；
- Observability usage/cost knownness 与预算证据；
- recovery 不盲目重复 side effect。

### 5.5 M4

按计划完成：

- Python 版本和配置单一真源；
- Provider arbitrary JSON normalization；
- malformed response matrix；
- error mapping；
- retry/backoff/retry budget；
- response-size limit；
- request identity；
- incremental SSE、UTF-8 split、malformed event；
- streaming consumer contract；
- Provider in-flight cancellation 能力和明确限制；
- doctor/config/CLI 协议稳定。

### 5.6 M5

按计划完成：

- Ubuntu/macOS/Windows × Python 3.11/3.12/3.13；
- lint/type/test/coverage；
- tracked allowlist 构建 wheel/sdist；
- secret scan；
- artifact file manifest；
- recomputed digest 和 tamper failure；
- clean venv install；
- live DeepSeek smoke；
- governance、安全报告、release process；
- README claim audit。

涉及真实 DeepSeek API Key、私密安全渠道或外部账户权限时，先完成所有无需凭据的工作并推送远程，再把该项标为明确的外部门禁；不得伪造 live smoke。

### 5.7 M6

- 创建 RC 分支/PR；
- RC 期间只允许 P0/P1 fix、测试稳定性、事实文档和 release pipeline fix；
- 全量 Gate 通过后形成最终 RC test report；
- 复核所有 P0/P1 `Verified`、Active P0/P1/S0/S1 = 0；
- 复核 artifacts、digests、clean install、live smoke、governance、claim traceability；
- 只有全部通过才允许合入 `master`、创建计划规定的 tag/release；
- 任一项失败则保持 `NO RELEASE` 并继续修复。

## 六、开发流程规范

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

### 分支策略

- `develop`：开发分支；
- `master`：发布分支；
- `develop` 已取消 PR 强制保护，但直推只作为异常兜底。

### 第一优先：PR 流程

1. 创建功能分支；
2. 提 Pull Request；
3. 等待 CI；
4. CI 通过后合入 `develop`；
5. 按项目 `docs/` 计划执行；
6. PR 标题和描述必须清楚说明变更、原因、证据和排除项。

### 第二优先：异常处理与直推

PR 流程持续失败时：

1. 定位根因，区分代码问题和环境问题；
2. 代码问题直接修复；
3. 环境、权限或规则问题无法在当前条件解决时，才允许直推 `develop`；
4. 直推前必须确保已尽可能运行测试并记录失败证据；
5. 直推不得用于绕过真实代码失败或 release gate。

直推 commit 格式：

```text
<type>(<scope>): <变更说明>

## 问题原因
[PR 流程无法通过的真实根因]

## 技术债务
- [未解决问题]
- [后续验证项]
```

技术债务记录位置：

```text
deepseekagent          → docs/TECH_DEBT.md 或 docs/BUG_LIST.md
deepcode               → docs/BUG_LIST.md
deepseek_runtime       → docs/TECH_DEBT.md
oh-my-deepseek-harness → docs/TECH_DEBT.md
llm-harness-agent      → TECH_DEBT.md
```

每条格式：

```text
[日期] 描述 | 遗留原因 | 状态
```

## 七、允许停止的硬阻断

只有以下情况允许停止全计划自主执行：

1. 必须由用户提供且当前连接中不存在的密钥、账户权限、签名、法律批准或人工安全审核；
2. GitHub 写权限完全不可用，且无法创建任何远程分支或提交；
3. 外部服务持续不可用，导致计划要求的真实外部验证无法完成；
4. 安全政策禁止执行；
5. 平台强制结束会话。

普通 CI 失败、测试失败、依赖冲突、代码缺陷、文档漂移、review finding、branch conflict 都不是停止理由，必须继续定位和修复。

遇到硬阻断时必须先：

- 将全部可提交代码、测试和文档推送到远程功能分支；
- 更新计划的真实进度；
- 更新 Traceability/TECH_DEBT；
- 创建或更新 Draft PR；
- 写明精确 blocker、已尝试方案、失败证据和解除条件；
- 新增下一会话可直接执行的 handoff；
- 不得声称任务完成或发布通过。

## 八、上下文与远程持久化纪律

为了防止长会话或容器销毁造成工作丢失：

- 每个可验证的小批次都要 commit 并 push 到远程功能分支；
- 每个 milestone 至少有 implementation PR 和 docs-only closeout PR；
- 重要失败 run、artifact ID、digest 和 denominator 立即写入 worklog/test report；
- 计划文件始终反映真实进展，不保留已经关闭的旧“当前现场”；
- 如果预计上下文将结束，先完成远程持久化和 handoff，再继续处理剩余工作；
- 不得把未 push 的本地工作作为完成证据。

## 九、禁止事项

- 不得要求用户反复发送“继续”；
- 不得只做计划、总结或 code review 而不实施；
- 不得在 `master` 直接开发；
- 不得在 M6 Gate 前发布或打正式 tag；
- 不得创建第二套生产 Agent Loop；
- 不得删除、隐藏或 rerun-mask 失败；
- 不得降低 Ruff、Pyright、test assertion、security contract 或 release criteria；
- 不得通过 cast、fallback、skip、文档措辞或百分比掩盖真实缺陷；
- 不得把 `Implemented` 写成 `Verified`；
- 不得伪造 live smoke、人工审核、artifact 或外部凭据结果；
- 不得因为任务较长而自行缩减 PRD P0/P1 范围。

## 十、沟通方式

- 使用中文；
- 工作过程中仅提供必要的阶段性进度，不等待确认；
- 每次汇报必须包含已完成事实、当前远程 branch/PR/head、真实 Gate 状态和下一自动执行项；
- 除硬阻断外，汇报后立即继续工作；
- 最终只在整个 Plan 完成时给出完整发布报告；
- 若因硬阻断结束，给出明确的 `BLOCKED / NO RELEASE` 交接报告。

现在开始：先重新读取 GitHub 远程事实，关闭 PR #20 的当前 blocker，并按上述顺序连续执行整个 Plan。不要停在建议或计划阶段。

---
