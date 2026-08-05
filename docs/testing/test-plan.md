# DeepSeek Runtime 测试计划

> 版本：1.2
> 适用代码审查基线：`develop@2fe059d900c4e04fab05ca92f421a41d7ff0aa01`；M2-D closeout PR #21
> 文档修订：以本文件所在 Git commit 为准
> 目标：证明 Open-source Alpha 的功能、边界、安全、恢复和发布过程，而不是只证明 Happy Path。

## 1. 测试目标

1. 验证 PRD 中全部 P0/P1 Requirement。
2. 验证模型、Provider、工作区、checkpoint 和 Tool 均可输入恶意或异常数据。
3. 验证中断恢复不会盲目重复副作用。
4. 验证默认输出、日志、checkpoint 配置和发布构件的隐私边界。
5. 建立贡献者可复现的 CI、构件和发布证据。
6. 使 coverage、normalization 和 release gate 指标具有明确分母，避免“假精确”。

## 2. 测试层级

| 层级 | 范围 | 目标占比/要求 |
| --- | --- | ---: |
| Unit | 纯函数、状态机、schema、policy、redaction | 约 55% |
| Component | Provider、Registry、Store、ChangeManager、Adapter | 约 25% |
| Integration | Runtime + Fake Provider + Fake Tools + Store | 约 15% |
| E2E | CLI、安装、live API、release artifact | 约 5% |
| Property/Fuzz | arbitrary JSON、路径、SSE chunks、schema | 持续运行 |
| Security Adversarial | traversal、symlink、handle forge、secret leak | 发布门禁 |
| Fault Injection | crash windows、fsync、replace、checkpoint corruption | 发布门禁 |

占比仅用于测试组合治理，不是发布 Gate；发布 Gate 由 Requirement 和 Test Case 决定。

## 3. 环境矩阵

### 3.1 Python 与操作系统

- Python：3.11、3.12、3.13；
- OS：Ubuntu、macOS、Windows；
- 文件系统：runner 默认文件系统；POSIX symlink；Windows junction/reparse point；
- Windows、macOS、Linux 的 process-tree、fsync、locking 差异必须有专用测试或已知限制。

### 3.2 Provider

- deterministic Fake Provider；
- malformed Provider fixtures；
- rate-limit/timeout fake transport；
- byte-split SSE fixture；
- 最少一次受保护的真实 DeepSeek smoke。

### 3.3 Execution Adapter

- FakeExecutionAdapter；
- NoIsolationLocalAdapter；
- RestrictedSubprocessAdapter；
- Docker/Podman 为 P2，不进入首个 Alpha 强制矩阵。

## 4. 测试数据原则

- 不使用真实用户 prompt、response 或业务文件。
- 不在 fixture 保存真实 API Key。
- Secret fixture 使用显眼假值，例如 `sk-test-do-not-use`。
- Provider 响应使用最小结构化 fixture。
- Side-effect 测试只操作临时目录、内存 fake 或可验证 mock endpoint。
- Live smoke 只生成固定、无业务含义的短句。
- 低熵 secret 测试必须覆盖 PIN、布尔值和短枚举，验证不会暴露可猜裸 hash。

## 5. 测试范围

### 5.1 Provider

- request merge 与 identity；
- response normalization；
- arbitrary JSON root；
- choices/message/tool_calls shape；
- error mapping；
- retry/backoff/retry budget；
- response-size limit；
- SSE framing、UTF-8、chunking、malformed event 和 cancellation；
- iterator/callback 与 final aggregation。

### 5.2 Runtime

- text-only；
- one/multiple tool calls；
- unknown tool；
- invalid arguments；
- tool timeout/error/output overflow；
- max step/token/cost/context/time；
- cancellation；
- lifecycle events；
- malformed Provider；
- Registry/Policy/Approval/Adapter 不可绕过；
- 所有终止路径返回结构化 RuntimeResult。

### 5.3 Tool、Policy 与 Execution

- ToolSpec 必填字段；
- JSON Schema validation；
- duplicate registry；
- default deny；
- rule conflict；
- approval allow/deny/timeout；
- adapter interface consistency；
- minimal child environment；
- process-tree timeout；
- NoIsolation/Restricted 的保证和限制不被混淆。

### 5.4 Workspace

- path traversal；
- absolute path；
- symlink/junction/reparse-point escape；
- read byte limit 和 UTF-8 截断；
- file/byte/time search budget；
- binary、permission、file-disappeared；
- 同一主机恶意并发进程属于未承诺边界，测试只验证可合理实现的检查与失败语义。

### 5.5 Change 与 Session

- forged/expired/cross-workspace rollback handle；
- durable ChangeJournal restart semantics；
- duplicate path；
- concurrent modification；
- stale rollback；
- metadata preservation；
- best-effort multi-file semantics；
- temp/write/replace/fsync fault injection；
- checkpoint corruption、migration、future version；
- checkpoint/evidence separation；
- encrypted checkpoint；
- uncertain side effects；
- receipts/idempotency/retry budget/manual reconciliation。

### 5.6 Evidence 与 Observability

- no secret/content；
- exception secret redaction；
- canonical identity；
- arbitrary JSON-compatible input；
- evidence schema version；
- debug-content gate；
- provider/tool/step latency；
- unknown cost；
- partial metrics；
- budget-stop evidence。

### 5.7 CLI、文档与发布

- doctor；
- “诊断成功”与“可在线运行”语义区分；
- run final output；
- report file；
- exit codes；
- clean install；
- wheel/sdist；
- Git tracked allowlist；
- secret scan；
- digest verification 与 tamper test；
- governance files；
- SECURITY 内容；
- README claim traceability。

## 6. 可测试性要求

- Clock、random、transport、approval、filesystem、checkpoint store 和 adapter 必须可注入。
- Runtime 状态机应暴露可测试的 transition table 或等价结构。
- Provider 错误规范化应使用显式 fixture manifest。
- Release Gate 应使用显式 gate manifest，不能只依赖脚本退出码集合。
- Fault injection 点至少包括：
  - before effect；
  - after effect before succeeded checkpoint；
  - after succeeded checkpoint；
  - after temp write before replace；
  - after first file replace；
  - before/after file fsync；
  - before/after directory fsync；
  - checkpoint partial/corrupt/concurrent save；
  - SSE arbitrary byte split。

## 7. 指标与分母定义

### 7.1 总体 Coverage

| 指标 | 分母 | Gate |
| --- | --- | ---: |
| Line coverage | `src/deepseek_runtime/**.py` 可执行语句；排除类型存根和明确不可达防御分支 | ≥85% |
| Branch coverage | 同一源码范围内 coverage.py 识别的分支 | ≥75% |

排除项必须写入配置并经评审；禁止为达标临时增加 pragma 排除。

### 7.2 P0 安全路径 Coverage

分母不是“安全相关文件的全部代码”，而是以下 manifest 中列出的函数和分支：

- workspace canonicalization/containment；
- symlink/reparse-point rejection；
- rollback handle lookup/validation；
- rollback containment/policy/conflict；
- side-effect running → uncertain recovery transition。

要求：manifest 中每个目标分支均被至少一个 P0 测试执行，目标 branch coverage = 100%。

### 7.3 Runtime 状态转换 Coverage

分母为已批准 transition table 的全部合法转换和全部非法转换类别：

```text
合法转换数 + 非法前驱拒绝类别数
```

要求：

- 合法转换覆盖 100%；
- 非法前驱拒绝类别覆盖 100%；
- 实现模块 branch coverage ≥95%。

### 7.4 Recovery Coverage

分母为：

```text
RecoveryPolicy × crash window × prior persisted state
```

首个 Alpha 至少覆盖：PURE、IDEMPOTENT、RETRYABLE_WITH_KEY、NON_IDEMPOTENT/MANUAL，以及 effect 前、effect 后 checkpoint 前、succeeded checkpoint 后三个窗口。

要求：所有 P0/P1 组合都有确定预期；不适用组合必须在 manifest 中说明理由。

### 7.5 Provider Error Normalization

分母为 `provider-error-fixtures.json` 中全部必需 fixture：

- 401、403、429、5xx；
- timeout、DNS、connection reset；
- invalid UTF-8、invalid JSON；
- JSON root type；
- malformed choices/message/tool_calls；
- response too large；
- malformed SSE event。

Gate：必需 fixture 100% 返回预期 machine-readable code；“≥90%”不得替代必需错误类别全部通过。

### 7.6 Release Gate Coverage

分母为 `release-gates.json` 中全部 Gate：Requirement、Defect、Test、Artifact、Documentation、Live Smoke。

Gate：发布时必须 100% 通过。测试代码对 gate evaluator 的 branch coverage ≥90%，但不能用代码 coverage 替代 Gate 通过率。

## 8. CI Pipeline

### 8.1 每个 PR 最小流水线

```text
lint
→ type-check
→ unit/component tests
→ 相关 regression tests
→ 受影响 P0/P1 adversarial tests
→ package import
→ tracked-secret scan
→ docs traceability
```

### 8.2 M2-D focused Gate

`M2 Runtime Lifecycle Gate` 在 Linux、macOS、Windows + Python 3.11 上运行 Runtime lifecycle、strict review、ExecutionAdapter、ToolRegistry、Policy/Approval 与授权审计模块，并上传包含明确测试分母和失败详情的 JSON artifact。实现 PR 文档变更后必须重新取得同一 exact head 的三平台证据。

### 8.3 合并后或 Nightly

```text
Python 3.11–3.13
× Ubuntu/macOS/Windows
→ property/fuzz
→ integration
→ recovery fault injection
→ security adversarial
→ package build/install
```

### 8.4 Release

```text
full matrix
→ clean build from Git tracked allowlist
→ wheel/sdist clean install
→ secret scan
→ digest recomputation
→ artifact tamper test
→ docs traceability
→ live DeepSeek smoke
→ RC report
```

真实付费 API 不在普通 PR 中运行；live smoke 只在受保护的手动、定时或 release workflow 中执行。

## 9. 准入标准

进入实现阶段前：

- PRD、测试用例、路线图和 traceability 一致；
- Threat Model 已评审；
- Error/State/Checkpoint/Recovery 最小合同先于 side-effect uncertain 实现冻结；
- P0 fixture 和测试骨架已存在；
- 最小 CI 可运行。

进入 RC 前：

- P0/P1 代码已合入；
- error/schema/versioning 已冻结；
- 所有 fixture manifest 已评审；
- 无已知数据泄漏和 silent retry；
- 完整 CI workflow 可运行。

## 10. 退出标准

- P0/P1 Requirement 全部 `Verified`；
- P0/P1 Test Case 100% 通过；
- Active P0/P1/S0/S1 = 0；
- 多平台矩阵全绿；
- 无已知 flaky test，不通过重跑掩盖失败；
- live smoke 通过；
- artifact 可安装、可追溯、无 secret、digest 匹配；
- Test Report 给出 `Release`。

## 11. 缺陷等级

- S0：可越界写/删、泄露密钥、发布敏感构件、重复高价值副作用；
- S1：核心流程不可用、状态损坏、错误恢复、权限绕过；
- S2：部分功能错误、指标不准、严重 UX 偏差；
- S3：文档、可维护性、低影响兼容性。

S0/S1 均阻断发布；P0/P1 defect 均阻断发布。

## 12. Traceability

每个 P0/P1 Requirement 必须维护：

- Requirement ID；
- Milestone；
- Owner Role；
- Implementation PR；
- Test Case ID；
- Test Level；
- Automation Status；
- Expected Evidence；
- Last Evidence；
- Status；
- Blocker。

唯一追踪表：`docs/traceability/alpha-traceability.md`。