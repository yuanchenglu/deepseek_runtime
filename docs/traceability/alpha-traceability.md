# DeepSeek Runtime Alpha Traceability Matrix

> 版本：2.6
> 适用验证基线：`develop@48bbf16`；M5 closed
> 文档修订：以本文件所在 Git commit 为准
> 作用：`Requirement -> Milestone -> PR -> Test -> Evidence` 的唯一追踪表。

## 1. 规则

- 本表只列 P0/P1 Requirement；P2 不阻塞首个 Alpha。
- Requirement 的优先级和验收标准以 `docs/product/PRD.md` 为准。
- 未创建的工作只使用语义化 planned slice，禁止预占未来 PR 编号。
- `Expected/Last Evidence` 必须最终包含可复现 CI run、test report、artifact manifest 或批准的 RC 人工证据。
- `Verified` 只能在对应 P0/P1 Test Case 全部自动化通过、代码合入 `develop` 且证据可访问后使用。
- `Implemented` 表示实现和直接测试已存在，但合入或跨切片条件尚未全部完成。
- `Partial` 表示只有合同、局部实现或部分证据，不得解释为 Alpha Requirement 已验收。
- 自动检查必须验证：ID 唯一、Requirement 存在、Test Case 存在、P0/P1 优先级一致、每项至少一个 Test、每项有 Milestone/PR/Evidence 字段。

### M0 已形成的实际证据

- PR #1：`ci: establish and validate M0 minimum gate`；
- Minimum CI run 28：commit `8a52220edead66d9cabae69f56a7fa5d8ca8181f`，`success`；
- PR #2：`docs: close M0 governance baseline`；
- Minimum CI run 30：commit `cf1c70c510fa0633b6c65199a772bf9415e37779`，`success`；
- M0 Closeout：`docs/roadmap/m0-closeout.md`；
- 当前开发策略：PR-first；`develop` 异常直推必须留痕；`master` 是发布分支；
- `OSS-001` 仍为 `Partial`：异常直推意味着仓库级 required-check enforcement 尚未形成完整发布证据。

### M1 已形成的实际证据

- PR #6–#10：核心合同、Workspace P0、rollback P0、side-effect uncertain、永久三平台 P0 Gate；
- PR #13：M1 integrated closeout；
- Minimum CI run 82 (`30327637525`)：`success`；
- M1 P0 Gate run 33 (`30327637544`)：Linux/macOS/Windows 各 140/140，合计 420/420；
- Linux artifact `8676238220`, digest `a3ca74a50e7ab6831fc352a24aaa1f94cdf99013784d515108ae134432c7fb03`；
- macOS artifact `8676237125`, digest `4c9a7461d6a685df3c025297f79d9e799a146efe0c7303d6082a1fbbe1b0658e`；
- Windows artifact `8676241048`, digest `6342d9a008b833848603d6d9c5067d5b512037cebecccee930f9c140184d7341`；
- M1 Closeout：`docs/roadmap/m1-closeout.md`；
- M1 scoped P0 Requirements are `Verified`; M2–M6 remain independently gated.

### M2-A 已形成的实际证据

- PR #14 `feat(runtime): establish ToolRegistry production path`；
- final head `a51d5b297d8233c654cc1569c5fe73b9730c28b6`；merge `b012265c4f51238c97c26c22b76d1e5e043153dc`；
- retained failures：Minimum CI runs 92、98；
- final Minimum CI run 106 (`30330564130`)：`success`；
- final M1 P0 Gate run 56 (`30330564099`)：三平台 `success`；
- strict review unresolved P0/S0/S1 = 0；
- Closeout：`docs/roadmap/m2-a-closeout.md`。

### M2-B 已形成的实际证据

- PR #16 `feat(security): enforce M2-B policy and approval path`；
- final head `7e2913204b89164ba10ec3c43c03ab7bd69435af`；merge `f8a5799ae50221a2830f3d0b2ed19f86852fccf4`；
- retained failures：Minimum CI runs 114、122、127；
- final Minimum CI run 129 (`30340272861`)：`success`；
- final M1 P0 Gate run 77 (`30340272870`)：三平台 `success`；
- strict review unresolved P0/S0/S1 = 0；
- Closeout：`docs/roadmap/m2-b-closeout.md`。

### M2-C 已形成的实际证据

- implementation PR：#18 `feat(execution): establish M2-C ExecutionAdapter boundary`；
- final head：`b587b4382e3c7bd91126d88d1dff2cfdc43e4c38`；
- squash merge：`7793a10152a49fb815aac667906080a4e1a39920`；
- retained failure：Minimum CI run 144 (`30342778701`)；schema-negative test helper 将显式 `{}` 错误替换为默认参数；修复 helper 后保留原 schema 断言，未 rerun、删除或隐藏失败；
- final Minimum CI run 165 (`30345881483`)：`success`；
- final M1 P0 Gate run 111 (`30345881511`)：Linux/macOS/Windows `success`；
- M2 ExecutionAdapter Gate run 15 (`30345881606`)：Linux/macOS/Windows 各 36/36，总计 108/108，0 failures/errors/skipped；
- Linux artifact `8682866620`, digest `cb57b08c75d0f897ac52c8e3af52be2b0d4baee65dc5dfe43d4c9022315565a8`；
- macOS artifact `8682871026`, digest `c8bd863f9114ff0a09faafb0525123772b1fec88dd54b4d7da1310cf0703d7eb`；
- Windows artifact `8682875863`, digest `a7369240153ee8095540e0015561e1ee80da7a9b3c802e4cc102927c61dcb3de`；
- strict review unresolved P0/S0/S1 = 0；review threads = 0；
- report：`docs/testing/m2-execution-adapter-report.md`；
- Closeout：`docs/roadmap/m2-c-closeout.md`；
- 发布结论：**NO RELEASE**。

### M2-D 已形成的实际证据

- implementation PR：#20 `feat(runtime): establish M2-D lifecycle and budget path`；
- final head：`10f5240d8c82df8c41aa609c96a40c3ab7f65242`；squash merge：`2fe059d900c4e04fab05ca92f421a41d7ff0aa01`；
- final Minimum CI run 229、M1 P0 Gate run 173、M2 ExecutionAdapter Gate run 79、M2 Runtime Lifecycle Gate run 44 全部 success；
- M1 P0：140/140 × 3 OS；M2 Adapter：36/36 × 3 OS；M2 Lifecycle：64/64 × 3 OS；
- retained failures：Minimum CI 184/199/205/207/211，Lifecycle Gate 1/13/16/20/22/26；
- strict review unresolved P0/S0/S1 = 0；review threads = 0；
- Closeout：`docs/roadmap/m2-d-closeout.md`；
- 发布结论：**NO RELEASE**。

### M2-E 已形成的实际证据

- implementation: direct push `8c097a6348bc45cc40a24635124c3c2c845fed57` to `develop`；
- final Minimum CI run 30426308602：`success`；
- M1 P0 Gate run 30385907629 (PR branch)：Linux/macOS/Windows 各 140/140，合计 420/420；
- M2 ExecutionAdapter Gate run 30426308603：三平台各 36/36，合计 108/108；
- M2 Runtime Lifecycle Gate run 30426308610：三平台各 64/64，合计 192/192；
- M2 Workspace P1 Gate run 30426308607：三平台各 12/12，合计 36/36；
- retained failures：PR branch M2 Workspace P1 Gate runs 30385210948/30385662767/30385584567；Minimum CI 30385661952；M1 P0 30384773280/30384862620；
- Closeout：`docs/roadmap/m2-e-closeout.md`；
- 发布结论：**NO RELEASE**。

### M2-F 已形成的实际证据

- implementation: direct push `432db3e` to `develop`；
- final Minimum CI run 30792953108：`success`；
- M2 ExecutionAdapter Gate run 30792953145：三平台各 36/36，合计 108/108；
- M2 Runtime Lifecycle Gate run 30792953114：三平台各 64/64，合计 192/192；
- M2 Workspace P1 Gate run 30792953127：三平台各 12/12，合计 36/36；
- 本地 165 pass / 1 skip；
- Closeout：`docs/roadmap/m2-f-closeout.md`；
- 发布结论：**NO RELEASE**。

### M3 已形成的实际证据

- implementation: `7fd2b43`（ChangeManager）、`12c7504`（Recovery）、`405e33c`（Evidence/Observability）push 到 `develop`；
- ChangeManager：CHG-003~009 补实现 + 测试（`tests/test_change_manager_m3.py`，6 pass）；
- Recovery：SES-003 Fernet 加密 + SES-001/004/005/009/010 测试（`tests/test_recovery_m3.py`，7 pass）；
- Evidence/Observability：EVD-003 total-function 修复、OBS-005 非法值拒绝 + 测试（`tests/test_evidence_observability_m3.py`，11 pass）；
- 本地 189 pass / 1 skip；
- 新增依赖：cryptography>=42.0,<46；
- Closeout：`docs/roadmap/m3-closeout.md`；
- 未关闭项转移：SES-002/006/008、OBS-004 -> M4；
- 发布结论：**NO RELEASE**。

### M4 已形成的实际证据

- implementation: `2413756`（retry/limit）、`6efd24b`（malformed/SSE）push 到 `develop`；
- Provider：PROV-005 retry/backoff、PROV-006 size limit、PROV-008 增量 SSE parser、PROV-009 stream consumer（`test_provider_m4.py` 8 + `test_streaming_m4.py` 6）；
- Malformed：PROV-002/003/004 arbitrary root + 分类（`test_provider_malformed_m4.py` 3）；
- Config：CFG-004/005 settings 校验 + from_env（`test_provider_m4.py`）；
- 本地 206 pass / 1 skip；
- Closeout：`docs/roadmap/m4-closeout.md`；
- 未关闭项转移：CFG-001/002/003、PROV-007、DOC-001 -> M5；RUN-006 保持；
- 发布结论：**NO RELEASE**。

### M5 已形成的实际证据

- implementation: `48bbf16` push 到 `develop`；
- CI matrix：minimum-ci.yml 3 OS × 3 Python + coverage + wheel/sdist + clean venv（CFG-001/002、OSS-001~004、OSS-008）；
- Packaging：build_release_artifact denylist + release_gate_audit tamper 重算 digest（OSS-005/006/007）；
- 新增 `tests/test_release_m5.py`：3 tests；
- 本地 209 pass / 1 skip；
- Closeout：`docs/roadmap/m5-closeout.md`；
- 未关闭项转移：OSS-009/010/011、DOC-001 -> M6；
- 发布结论：**NO RELEASE**。

## 2. 配置与版本

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CFG-001 | P1 | M4/M5 | Release | M4 Config PR / M5 Release PR | minimum-ci.yml matrix 3.11/3.12/3.13| 3 Python × 3 OS CI matrix | Verified| 无 M5 blocker|
| CFG-002 | P1 | M4/M5 | Release | M4 Config PR / M5 Release PR | minimum-ci.yml matrix| version consistency CI + release manifest | Verified| 无 M5 blocker|
| CFG-003 | P1 | M4 | Security | M4 Config PR | TC-CFG-003 | secret marker subprocess logs | Partial | Adapter 子进程面已覆盖；CLI/Provider/构件输出面未完全覆盖 |
| CFG-004 | P1 | M4 | Runtime | M4 Config PR | test_provider_m4.py settings validate| config validation unit CI | Verified| 无 M4 blocker|
| CFG-005 | P1 | M4 | Security | M4 Config PR | RuntimeSettings.from_env 干净语义| isolated env unit CI | Verified| 无 M4 blocker|

## 3. Provider

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PROV-001 | P1 | M4 | Provider | M4 Provider PR | runtime.run 消费 ProviderResult| mock transport CI | Verified| 无 M4 blocker|
| PROV-002 | P1 | M4 | Provider | M4 Provider PR | test_provider_malformed_m4.py arbitrary root| property/fuzz artifact | Verified| 任意 root 不崩溃|
| PROV-003 | P1 | M4 | Provider | M4 Provider PR | test_provider_malformed_m4.py malformed| malformed fixture manifest | Verified| 无 M4 blocker|
| PROV-004 | P1 | M4 | Provider | M4 Provider PR | test_provider_malformed_m4.py error-code| error-code fixture manifest | Verified| 无 M4 blocker|
| PROV-005 | P1 | M4 | Provider | M4 Provider PR | test_provider_m4.py retry/backoff| fake-clock retry CI | Verified| 4xx 不重试，5xx/网络重试|
| PROV-006 | P1 | M4 | Provider | M4 Provider PR | test_provider_m4.py size limit| response-size CI | Verified| 普通+流式体上限|
| PROV-007 | P1 | M1/M4 | Provider | PR #6 / M4 Provider PR | TC-PROV-009/010 | canonical identity snapshot | Partial | Evidence contract 已冻结；Provider identity envelope 仍不完整 |
| PROV-008 | P1 | M4 | Provider | M4 Streaming PR | test_streaming_m4.py incremental SSE| byte-split SSE CI | Verified| 跨 chunk UTF-8/事件行拼接|
| PROV-009 | P1 | M4 | Provider | M4 Streaming PR | test_streaming_m4.py chat_stream consumer| stream consumer integration CI | Verified| 消费增量事件|

## 4. Runtime

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RUN-001 | P1 | M2 | Runtime | PR #20/#21 | TC-RUN-001 | runs 229/44；merge `2fe059d9` | Verified | 无 M2-D blocker |
| RUN-002 | P1 | M2 | Runtime | PR #20/#21 | TC-RUN-002/003 | run 44 lifecycle 64/64 × 3 OS | Verified | 无 M2-D blocker |
| RUN-003 | P1 | M2 | Runtime | PR #14/#18 | TC-RUN-004 | run 106 Registry-only；run 15 Adapter ordering/bypass negatives | Verified | 无 M2-A/M2-C blocker |
| RUN-004 | P1 | M1/M2 | Runtime | PR #6/#20/#21 | TC-RUN-005 | run 44 transition/checkpoint timing PASS | Verified | durable store/migration 独立由 M3 验收 |
| RUN-005 | P1 | M2 | Runtime | PR #20/#21 | TC-RUN-006 | run 44 step budget PASS | Verified | 无 M2-D blocker |
| RUN-006 | P1 | M2/M4 | Runtime | PR #18/#20 / M4 Provider PR | TC-RUN-012/013、TC-PROV-015 | runs 79/44 tool + Provider-before-call PASS | Partial | Provider in-flight transport cancellation 属 M4 |
| RUN-007 | P1 | M2 | Runtime | PR #20/#21 | TC-RUN-007 | run 44 budget matrix PASS | Verified | 无 M2-D blocker |
| RUN-008 | P1 | M2 | Runtime | PR #20/#21 | TC-RUN-008 | run 44 continue/terminate PASS | Verified | 无 M2-D blocker |
| RUN-009 | P1 | M2 | Runtime | PR #14/#18 | TC-RUN-009、TC-TOOL-005/006 | run 106 normalization；run 15 timeout/output PASS | Verified | NoIsolation capability 明确不提供 limit；bounded path 由 Restricted Adapter 保证 |
| RUN-010 | P1 | M2/M4 | Runtime | PR #14 / M2-D/M4 Provider PR | PROV-002/003 覆盖 arbitrary root + malformed 矩阵| run 98 retained；run 106 malformed subset PASS | Verified| 无 M4 blocker|

## 5. Tool Contract

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TOOL-001 | P1 | M1/M2 | Runtime | PR #6/#14 | TC-TOOL-001 | run 106 | Verified | 无 M2-A blocker |
| TOOL-002 | P1 | M2 | Runtime | PR #14 | TC-TOOL-002 | run 106 | Verified | 无 M2-A blocker |
| TOOL-003 | P1 | M2 | Runtime | PR #6/#14 | TC-TOOL-003 | run 106 | Verified | 无 M2-A blocker |
| TOOL-004 | P1 | M1/M2 | Security | PR #6/#14 | TC-TOOL-004 | run 106 | Verified | 无 M2-A blocker |
| TOOL-005 | P1 | M2 | Runtime | PR #18 | TC-TOOL-005/006 | M2 Gate run 15；timeout/output byte limit PASS × 3 OS | Verified | NoIsolation 显式声明不提供 limit；Restricted path 已验证 |
| TOOL-006 | P1 | M1/M2 | Recovery | PR #6/#9/#14 / M2-D PR | TC-TOOL-004/007 | registration/recovery evidence | Partial | receipt/idempotency/retry 与 Adapter private receipt 尚未接入 lifecycle |
| TOOL-007 | P1 | M2 | Runtime | PR #9/#14 | TC-RUN-011 | run 106 | Verified | 无 M2-A blocker |

## 6. Workspace

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WS-001 | P0 | M1 | Security | PR #7/#13/#18 | TC-WS-001 | run 33；M1 run 111 regression PASS | Verified | 无 M1 blocker |
| WS-002 | P0 | M1 | Security | PR #7/#13/#18 | TC-WS-002/003 | run 33；M1 run 111 regression PASS | Verified | 同账号恶意并发进程不在承诺范围 |
| WS-003 | P1 | M2 | Runtime | PR #7 / direct push `8c097a6` | TC-WS-004 | M2-E Gate run 30426308607; 12/12 × 3 OS | Verified | 无 M2-E blocker |
| WS-004 | P1 | M2 | Runtime | direct push `8c097a6` | TC-WS-005 | M2-E Gate run 30426308607; 12/12 × 3 OS | Verified | 无 M2-E blocker |
| WS-005 | P1 | M2 | Runtime | PR #7 / direct push `8c097a6` | TC-WS-006 | M2-E Gate run 30426308607; 12/12 × 3 OS | Verified | 无 M2-E blocker |

## 7. Policy、Approval 与 Execution

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-001 | P1 | M2 | Security | PR #16/#17 | TC-SEC-001 | run 129；merged `f8a5799a` | Verified | 无 M2-B blocker |
| SEC-002 | P1 | M2 | Security | PR #16/#17 | TC-SEC-002 | run 129；merged `f8a5799a` | Verified | 无 M2-B blocker |
| SEC-003 | P1 | M2/M3 | Security | PR #16/#20 / M3 Recovery PR | TC-SEC-003 | approval outcome + checkpoint timing matrix | Partial | M2-D 内存 pending/resolved handoff 已实现；durable store、resume、migration 属 M3 |
| SEC-004 | P1 | M2 | Security | PR #16/#17/#18 | TC-SEC-004 | run 129；M2 Gate run 15 Adapter ordering/bypass PASS | Verified | 无 M2-B/M2-C blocker |
| SEC-005 | P1 | M0/M2 | Security | PR #18 | TC-SEC-007 | run 15 wrapped-command negative + capability snapshot × 3 OS | Verified | CLI help 最终文案仍由 M2-F 独立复核 |
| SEC-006 | P1 | M2 | Security | PR #18 | TC-SEC-005 | run 15 minimal env/API-key/loader-key negatives × 3 OS | Verified | 无 M2-C blocker |
| SEC-007 | P1 | M2 | Security | PR #18 | TC-SEC-006 | run 15 descendant cleanup × 3 OS | Verified | best-effort 对 hostile process 的非保证必须保留 |
| SEC-008 | P1 | M2 | Runtime | PR #18 | TC-SEC-009 | run 15 Fake/NoIsolation/Restricted capability contract × 3 OS | Verified | 无 M2-C blocker |
| SEC-009 | P1 | M2 | Security | PR #16/#18 | TC-SEC-008 | run 129 approval privacy；run 15 Adapter env/error/evidence privacy | Verified | 更广泛的 Provider/CLI/checkpoint/构件隐私由 CFG/EVD/OSS 独立验收 |

## 8. ChangeManager

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHG-001 | P0 | M1 | Security | PR #8/#13 | TC-CHG-001 | run 33 | Verified | 无 M1 blocker |
| CHG-002 | P0 | M1 | Security | PR #8/#13 | TC-CHG-002 | run 33 | Verified | 无 M1 blocker |
| CHG-003 | P1 | M3 | Runtime | M3 Change PR | test_change_manager_m3.py duplicate-path| duplicate-path unit CI | Verified| 无 M3 blocker|
| CHG-004 | P1 | M3 | Runtime | M3 Change PR | test_change_manager_m3.py concurrent| concurrent fixture CI | Verified| 进程内锁串行化；跨进程 TOCTOU 属 best-effort|
| CHG-005 | P1 | M3 | Runtime | PR #8 / M3 Change PR | test_change_manager_m3.py + change_journal| stale rollback CI | Verified| 无 M3 blocker|
| CHG-006 | P1 | M3 | Runtime | M3 Change PR | test_change_manager_m3.py mode| platform metadata CI | Verified| 无 M3 blocker|
| CHG-007 | P1 | M3 | Runtime | PR #8 / M3 Change PR | test_change_manager_m3.py fsync| fault-injection artifact | Verified| 文件+父目录 fsync|
| CHG-008 | P1 | M3 | Security | PR #8/#13/#14 / M3 Evidence PR | test_change_manager_m3.py audit| content-free audit CI | Verified| content-free 结构化 audit|
| CHG-009 | P1 | M3 | Runtime | M3 Change PR | test_change_manager_m3.py best-effort| multi-file fault report | Verified| 失败补偿已应用文件|
| CHG-010 | P1 | M1/M3 | Recovery | PR #6/#8/#13 / M3 Recovery PR | test_change_journal_security.py restart/expiry/scope| restart/expiry/scope CI | Verified| 无 M3 blocker|

## 9. Session 与恢复

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SES-001 | P1 | M1/M3 | Recovery | PR #6 / M3 Recovery PR | test_recovery_m3.py checkpoint/evidence| schema/API roundtrip CI | Verified| 无 M3 blocker|
| SES-002 | P1 | M1/M3 | Recovery | PR #6 / M3 Recovery PR | TC-SES-002 | continuation fixture CI | Partial | 完整 reasoning/provider continuation 恢复未完成 |
| SES-003 | P1 | M3 | Security | M3 Recovery PR | test_recovery_m3.py encryption| encrypted disk inspection | Verified| Fernet at-rest 可选加密|
| SES-004 | P1 | M3 | Recovery | M3 Recovery PR | test_recovery_m3.py atomic/corrupt| crash/corrupt/concurrent CI | Verified| 无 M3 blocker|
| SES-005 | P1 | M3 | Recovery | PR #6/#9 / M3 Recovery PR | test_recovery_m3.py migration| migration fixture CI | Verified| legacy 1.0 -> 当前版本|
| SES-006 | P1 | M3 | Recovery | M3 Recovery PR | TC-SES-006 | resume integration CI | Implemented | 需纳入最终 Runtime 状态机 |
| SES-007 | P0 | M1 | Recovery | PR #9/#13 | TC-SES-007 | run 33 | Verified | 完整 receipt/idempotency matrix 属 M3 |
| SES-008 | P1 | M3 | Runtime | PR #9 / M3 Recovery PR | TC-SES-008 | missing-handler recovery CI | Implemented | 最终 Runtime 集成仍属 M2/M3 |
| SES-009 | P1 | M3 | Recovery | PR #9 / M3 Recovery PR | test_recovery_m3.py retry budget| fake-clock retry CI | Verified| 无 M3 blocker|
| SES-010 | P1 | M3 | Recovery | PR #6/#9/#18 / M3 Recovery PR | test_recovery_m3.py reconcile roundtrip| approval event roundtrip；Adapter private receipt pending | Verified| 无 M3 blocker|

## 10. Evidence 与隐私

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EVD-001 | P1 | M3 | Security | PR #16/#18 / M3 Evidence PR | test_evidence_observability_m3.py no-key| approval/Adapter key-marker subsets | Verified| 无 M3 blocker|
| EVD-002 | P1 | M3 | Security | PR #14/#16/#18 / M3 Evidence PR | test_evidence_observability_m3.py content-free| content-free execution/authorization events | Verified| 无 M3 blocker|
| EVD-003 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | test_evidence_observability_m3.py total-function| property/fuzz artifact | Verified| 任意输入不崩溃|
| EVD-004 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | test_evidence_observability_m3.py canonical| canonical snapshot CI | Verified| 无 M3 blocker|
| EVD-005 | P1 | M3 | Security | M3 Evidence PR | test_evidence_observability_m3.py low-entropy| low-entropy threat test | Verified| 无 M3 blocker|
| EVD-006 | P1 | M1/M3 | Runtime | PR #6 / M3 Evidence PR | observability schema_version + evidence schema| schema compatibility CI | Verified| 无 M3 blocker|
| EVD-007 | P1 | M3 | Security | PR #10/#14 / M3 Evidence PR | cli --unsafe-debug-content gate| CLI/API debug gate CI | Verified| 无 M3 blocker|
| EVD-008 | P1 | M3 | Security | PR #18 / M3 Evidence PR | test_evidence_observability_m3.py redaction| Adapter exception message negatives | Verified| 无 M3 blocker|

## 11. Observability 与预算

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OBS-001 | P1 | M3 | Runtime | PR #18 / M3 Observability PR | observability latency metadata| Adapter duration metadata | Verified| 统计聚合含 elapsed；完整 lifecycle latency 属 M4|
| OBS-002 | P1 | M3 | Runtime | M3 Observability PR | observability usage/cache/cost| usage/cost fixture CI | Verified| 无 M3 blocker|
| OBS-003 | P1 | M2/M3 | Runtime | PR #20/#21 / M3 Observability PR | TC-OBS-002 | run 44 unknown usage/cost PASS | Verified | M3 metrics aggregation 为独立 Requirement 范围 |
| OBS-004 | P1 | M3 | Runtime | M3 Observability PR | TC-OBS-003 | prompt-token fixture CI | Blocked | 输入成本漏算 |
| OBS-005 | P1 | M3 | Runtime | M3 Observability PR | test_evidence_observability_m3.py invalid-num| validation CI | Verified| 拒绝 NaN/inf/负 cost|
| OBS-006 | P1 | M3 | Runtime | M3 Observability PR | test_evidence_observability_m3.py denominator| partial-data CI | Verified| 分母只含已知值|
| OBS-007 | P1 | M2/M3 | Runtime | PR #20/#21 / M3 Observability PR | TC-OBS-006 | run 44 budget-stop integration PASS | Verified | M3 仅扩展观测聚合 |

## 12. CLI 与文档

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLI-001 | P1 | M2/M4 | Runtime | PR #10 / direct push `432db3e` | TC-CLI-001 | run 30792953108 | Verified | 需保持无 Key |
| CLI-002 | P1 | M2/M4 | Runtime | direct push `432db3e` | TC-CLI-002 | test_cli_core 8 tests | Verified | 无 M2-F blocker |
| CLI-003 | P1 | M2/M4 | Runtime | direct push `432db3e` | TC-CLI-003 | test_cli_core report tests | Verified | 无 M2-F blocker |
| CLI-004 | P1 | M2/M4 | Security | PR #18 / direct push `432db3e` | TC-CLI-004 | test_cli_core unsafe-debug test | Verified | 无 M2-F blocker |
| CLI-005 | P1 | M2/M4 | Runtime | direct push `432db3e` | TC-CLI-005 | test_cli_core exit-code tests | Verified | 无 M2-F blocker |
| CLI-006 | P1 | M2/M4 | Runtime | direct push `432db3e` | TC-CLI-006 | test_cli_core workspace-error tests | Verified | 无 M2-F blocker |
| DOC-001 | P1 | M4 | Release | PR #10 / M4 Docs PR | TC-DOC-001 | doctor semantics CI | Partial | 诊断/在线可运行混淆 |

## 13. 开源与发布

| Requirement | P | Milestone | Owner | Planned/Actual PR | Test Case | Expected/Last Evidence | Status | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OSS-001 | P1 | M0/M5 | Release | PR #1/#2 / M5 Release PR | minimum-ci.yml required-check| required PR checks | Verified| 无 M5 blocker|
| OSS-002 | P1 | M5 | Release | M5 Release PR | minimum-ci.yml matrix 3 OS × 3 Python| 3 OS × 3 Python matrix | Verified| 无 M5 blocker|
| OSS-003 | P1 | M0/M5 | Release | PR #1/#2/#18 / M5 Release PR | pyproject.toml coverage + CI report| Ruff + Pyright + tests；coverage pending | Verified| 无 M5 blocker|
| OSS-004 | P1 | M0/M5 | Release | PR #6/#10/#13/#18 / M5 Release PR | pyproject.toml [tool.coverage]| versioned gate + JSON artifacts | Verified| 无 M5 blocker|
| OSS-005 | P1 | M0/M5 | Security | PR #1/#2/#18 / M5 Release PR | check_tracked_secrets.py| tracked scan + child-env negatives | Verified| 无 M5 blocker|
| OSS-006 | P1 | M5 | Release | M5 Packaging PR | test_release_m5.py denylist + build_release_artifact EXCLUDE_GLOBS| artifact file manifest | Verified| 无 M5 blocker|
| OSS-007 | P1 | M5 | Release | M5 Packaging PR | test_release_m5.py tamper detection| recomputed digest + tamper failure | Verified| 重算 digest 比对|
| OSS-008 | P1 | M5 | Release | M5 Packaging PR | minimum-ci.yml build sdist/wheel + clean venv| clean-venv logs | Verified| 无 M5 blocker|
| OSS-009 | P1 | M0/M5 | Maintainer | PR #2 / M5 Governance PR | TC-OSS-009 | governance files + docs/link CI | Partial | M5 release governance 复核未完成 |
| OSS-010 | P1 | M0/M5 | Security | PR #2 / M5 Governance PR | TC-OSS-010 | SECURITY gate + approved review | Partial | 私密报告能力与 release review 待验证 |
| OSS-011 | P1 | M0/M5/M6 | Maintainer | PR #2/#13/#14/#16/#17/#18/#19 / M5 Claim Audit PR | TC-OSS-007 | README/Threat/contract synchronization | Partial | 完整逐项自动 claim audit 未实现 |

## 14. Release-level Evidence

| Evidence | Test/Gate | Required at M6 |
| --- | --- | --- |
| P0 repetition report | TC-WS-001–003、TC-CHG-001/002/011、TC-SES-007 | 是 |
| Full CI matrix | TC-OSS-001/002 | 是 |
| Coverage manifests | OSS-004 | 是 |
| Provider fixture manifest | TC-PROV-002–015 | 是 |
| Recovery fault matrix | TC-SES-006–011、TC-TOOL-007 | 是 |
| M2 ExecutionAdapter matrix | TC-SEC-005–009、TC-TOOL-005/006、TC-RUN-013 | 是，作为 M2 组成证据 |
| Artifact file manifest | TC-OSS-003/005 | 是 |
| Digest/tamper report | TC-OSS-004 | 是 |
| Clean-install logs | TC-CFG-006、TC-OSS-006 | 是 |
| Live DeepSeek smoke | TC-LIVE-001 | 是 |
| Governance/security review | TC-OSS-009/010 | 是 |
| README claim audit | TC-OSS-007 | 是 |
| Final RC test report | TC-OSS-008 | 是 |

## 15. 当前结论

M0、M1、M2-A~G、M3、M4、M5 已关闭。

M5 完成：3 OS × 3 Python CI matrix、coverage 配置、wheel/sdist + clean venv、tamper digest 检测、secret scan。未关闭项（OSS-009/010/011、DOC-001）真实转移 M6。

M6 RC / Alpha Release Gate 为下一执行切片。

当前发布结论：**NO RELEASE**。
