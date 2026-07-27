# DeepSeek Runtime Open-source Alpha Threat Model

> 版本：1.0
> 适用代码审查基线：`develop@0e1e435`
> 文档修订：以本文件所在 Git commit 为准
> 目标：明确首个 Alpha 保护什么、不保护什么，以及所有安全声明的证据要求。

## 1. 安全结论

DeepSeek Runtime 首个 Alpha 是 **local-first Runtime Kernel**，不是多租户安全执行平台，也不是内核级 sandbox。

它必须做到：

- Runtime 自身不存在绕过 ToolRegistry、Policy、Approval 和 Execution Adapter 的生产路径；
- 不可信模型输出和 Provider response 不能直接成为未校验工具执行；
- workspace 工具不能通过 Runtime 自身的路径解析逻辑越出工作区；
- rollback handle 不可由调用方伪造或跨 workspace 使用；
- 不确定外部副作用不会在恢复时自动重试；
- 默认日志、Evidence 和发布构件不泄露敏感正文和密钥；
- 所有安全承诺有自动化测试和发布证据。

它不承诺：

- 抵抗同一主机、相同用户权限下的恶意并发进程；
- 提供容器、虚拟机、Seatbelt、seccomp、Job Object 等内核隔离；
- 对不支持幂等键、receipt 或查询的外部系统提供通用 exactly-once；
- 在宿主机、内核、Python 解释器或依赖被攻破后维持安全边界。

## 2. 保护资产

| 资产 | 风险 | Alpha 要求 |
| --- | --- | --- |
| DeepSeek API Key | 日志、子进程、异常、构件泄漏 | 默认不存储；不传入子进程；所有输出脱敏 |
| Prompt/response/reasoning | Evidence、日志、checkpoint、异常泄漏 | 公开 Evidence 无正文；checkpoint 可选加密 |
| Tool arguments/results | 日志、审批、checkpoint 泄漏 | 默认只输出安全摘要；恢复正文仅进入 checkpoint |
| Workspace 文件 | 越界读写、symlink、冲突覆盖 | canonical containment、链接防护、冲突检测 |
| 外部副作用 | 崩溃后重复执行 | RecoveryPolicy、receipt、uncertain/manual |
| Checkpoint | 明文、篡改、损坏、版本漂移 | 原子写、损坏检测、schema version、可选加密 |
| ChangeJournal | 伪造 rollback、敏感正文、跨 workspace | opaque handle、受保护记录、scope/expiry/schema |
| Release artifact | `.env`、checkpoint、未跟踪文件、篡改 | Git tracked allowlist、secret scan、digest/tamper gate |
| 测试和发布证据 | 虚假通过、rerun 掩盖、文档漂移 | Traceability、无 flaky、明确 Release/No Release |

## 3. 不可信输入

以下输入默认不可信：

- 用户 prompt；
- 模型输出、tool name、tool arguments；
- Provider HTTP body、SSE event、usage、request id；
- 工作区路径、文件名、文件内容、symlink/reparse point；
- Tool handler 返回值和异常；
- checkpoint 文件、schema version、migration input；
- rollback handle；
- 环境变量；
- 构建工作树和未跟踪文件；
- 依赖包和第三方代码来源。

## 4. 信任边界

```mermaid
flowchart LR
    User[User/App]
    Runtime[Runtime]
    Provider[DeepSeek Provider]
    Registry[ToolRegistry]
    Policy[Policy + Approval]
    Adapter[Execution Adapter]
    Workspace[Workspace]
    Store[Checkpoint + ChangeJournal]
    Evidence[Publishable Evidence]
    Artifact[Release Artifact]

    User --> Runtime
    Runtime <--> Provider
    Runtime --> Registry
    Registry --> Policy
    Policy --> Adapter
    Adapter --> Workspace
    Runtime --> Store
    Runtime --> Evidence
    Store -. must not enter .-> Artifact
    Evidence --> Artifact
```

### 4.1 模型与 Provider 边界

- Provider response 必须先 normalize，再进入 Runtime 和 Evidence；
- 任意 JSON-compatible 根必须返回规范化对象或结构化错误；
- tool name 和 arguments 不因来自模型而获得信任；
- retry 只应用于明确 eligible 的 Provider 请求，不代表 Tool 副作用可重试。

### 4.2 Runtime 与 Tool 边界

- Runtime 只能通过 ToolRegistry 执行工具；
- Registry 在 handler 前完成 tool lookup、schema validation、risk/recovery/limit 检查；
- 每次执行必须有 policy decision；
- ASK 必须通过 ApprovalProvider；
- handler 异常和非法返回值必须规范化。

### 4.3 Execution Adapter 边界

`NoIsolationLocalAdapter`：

- 仅可信本地开发；
- 不提供 OS 隔离；
- 文档和类型必须明确风险。

`RestrictedSubprocessAdapter`：

- 最小环境；
- cwd；
- timeout；
- process-tree cleanup；
- cancellation；
- output limit；
- 仍不阻止进程读取同一用户可访问的工作区外资源，因此不能称为 sandbox。

### 4.4 Workspace 边界

Runtime 承诺：

- 所有 read/search/change/rollback 使用同一 canonical resolver；
- 默认拒绝或跳过 symlink 和 reparse point；
- 每个候选在使用前执行 containment；
- 读取和写入有资源预算、冲突检测和结构化错误。

Runtime 不承诺：

- 阻止同一主机恶意进程在检查后、打开前替换 symlink 或路径；
- 防御拥有相同用户权限的进程直接绕过 Runtime 访问文件系统。

因此文档不得使用“对本地主机攻击者安全隔离”等表述。

### 4.5 Checkpoint 与 Evidence 边界

`RecoverableCheckpoint`：

- 包含恢复所需正文；
- 默认仅本地使用；
- 可选加密；
- 不可作为公开诊断报告。

`PublishableEvidence`：

- 只包含结构、长度、安全 identity、usage、cost、状态和脱敏错误；
- 不包含恢复正文；
- 低熵敏感值不得输出可字典猜测的裸 SHA-256。

### 4.6 Rollback 与 ChangeJournal 边界

- 调用方只持有 opaque handle；
- handle 不能携带路径、原始正文或可篡改恢复载荷；
- Manager/Store 维护 ChangeJournal；
- Journal 绑定 workspace、changeset、pre/post hash、expiry、schema；
- rollback 时重新执行 containment、policy 和 stale-hash 检查；
- forged、expired、missing、cross-workspace handle 结构化拒绝；
- Journal 可选加密，默认不进入发布构件；
- 重启后是否可 rollback 由 Journal 是否持久化决定，必须可测试，不允许依赖隐式内存状态。

### 4.7 外部副作用边界

崩溃窗口：

1. effect 前；
2. effect 成功后、succeeded checkpoint 前；
3. succeeded checkpoint 后。

规则：

- PURE/IDEMPOTENT/RETRYABLE_WITH_KEY 按 RecoveryPolicy 处理；
- NON_IDEMPOTENT 或无法确认的 running 状态进入 `TOOL_SIDE_EFFECT_UNCERTAIN`；
- uncertain 不自动重试；
- 用户显式 reconcile、mark-succeeded、mark-not-executed、abandon 或 explicit-retry；
- 所有人工决策进入 checkpoint 和 evidence。

## 5. 主要威胁与控制

| ID | 威胁 | 控制 | 验证 |
| --- | --- | --- | --- |
| TM-001 | Path traversal 越界读 | canonical resolver + containment | TC-WS-001 |
| TM-002 | symlink/reparse-point 越界搜索 | lstat/skip/resolve/containment | TC-WS-002/003 |
| TM-003 | Forged rollback 写删外部文件 | opaque handle + ChangeJournal + policy | TC-CHG-001/002 |
| TM-004 | stale rollback 覆盖后续修改 | post-change hash conflict | TC-CHG-005 |
| TM-005 | rollback handle 重启/跨 workspace 混淆 | scope/expiry/schema/journal lookup | TC-CHG-011 |
| TM-006 | Tool 绕过 policy | Registry 唯一入口 | TC-RUN-004、TC-SEC-004 |
| TM-007 | 子进程继承 API Key | minimal environment | TC-SEC-005 |
| TM-008 | timeout 后子进程残留 | process-tree cleanup | TC-SEC-006 |
| TM-009 | 命令 Gate 被误认为隔离 | 命名、帮助文本、保证表 | TC-SEC-007/009 |
| TM-010 | 崩溃后重复副作用 | uncertain/manual、receipt、idempotency | TC-SES-006/007/009 |
| TM-011 | malformed Provider 绕过结构化错误 | normalization-before-evidence | TC-PROV-002–004、TC-RUN-010 |
| TM-012 | Evidence 泄漏正文或 Key | content-free evidence + redaction | TC-EVD-001/005/007 |
| TM-013 | 低熵 hash 可猜 | HMAC 或不输出 identity | TC-EVD-004 |
| TM-014 | Checkpoint 明文或损坏 | optional encryption + atomic/corrupt checks | TC-SES-003/004/011 |
| TM-015 | 构件包含未跟踪 secret | Git tracked allowlist + secret scan | TC-OSS-003/005 |
| TM-016 | 篡改构件仍通过 | digest recomputation + tamper test | TC-OSS-004 |
| TM-017 | 文档/测试优先级漂移 | PRD source of truth + traceability gate | TC-OSS-007/008 |
| TM-018 | flaky/rerun 掩盖安全失败 | no-rerun gate + P0 repetition | Release Gate |

## 6. 安全测试要求

- P0 测试不得 quarantine；
- P0 测试在适用平台连续运行 20 次无失败；
- P0 manifest 中目标分支 coverage = 100%；
- RecoveryPolicy × crash window × prior state 的 P0/P1 组合有确定预期；
- 必需 Provider error fixture 100% 返回预期 code；
- Release Gate 必须 100% 通过；
- 不允许用 rerun 后成功作为 Release 证据。

## 7. 漏洞响应

公开 Alpha 前必须在 `SECURITY.md` 明确：

- 私密报告渠道；
- 支持版本；
- 响应和确认目标；
- 严重度分类；
- 修复、公告和版本发布流程；
- 不应公开提交真实 API Key、prompt、response、checkpoint 或 exploit data。

发现以下任一问题立即 No-Go：

- 越界写删；
- API Key 或默认正文泄漏；
- Runtime policy 绕过；
- 重复高价值副作用；
- 发布构件包含 secret；
- rollback handle 可伪造或跨 workspace；
- CI 只能通过 rerun。

## 8. 审查与变更规则

以下变化必须更新本 Threat Model 和相关 ADR：

- 新 Tool 类型或 RecoveryPolicy；
- 新 Execution Adapter；
- checkpoint、evidence 或 ChangeJournal schema；
- workspace/path 处理；
- Provider streaming/retry；
- release artifact pipeline；
- 从 local-first 向 hosted/multi-tenant 扩展。

Threat Model 未同步更新的安全边界变化不得合入 `develop`。