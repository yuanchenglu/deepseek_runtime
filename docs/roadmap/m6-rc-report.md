# M6 RC / Alpha Release Gate Report

> Milestone: M6 RC / Alpha Release Gate
> Status: **BLOCKED — NO RELEASE**
> 验证基线：`develop@8cfa5cf`
> RC 分支：`develop`（未创建 `master` PR，因 Active P1 > 0）

## 1. RC Gate 执行

### 本地专项 Gate（current develop head）

| Gate | 命令 | 结果 |
| --- | --- | --- |
| M1 P0 Gate | `scripts/m1_p0_gate.py --repetitions 3` | 21/21, 0 failures |
| M2 ExecutionAdapter Gate | `scripts/m2_execution_gate.py` | 36/36, 0 failures |
| M2 Runtime Lifecycle Gate | `scripts/m2_lifecycle_gate.py` | 64/64, 0 failures |
| M2 Workspace P1 Gate | `scripts/m2_workspace_gate.py` | 12/12, 0 failures |

全量单测：210 pass / 1 skip。

### CI Gate

minimum-ci.yml（含 matrix 3 OS × 3 Python + coverage + wheel/sdist + clean venv）已在 develop 上运行。

### 阻断项

**Active P1 = 11 > 0**，不满足 M6 发布门禁。

## 2. 剩余 11 项 P1 未 Verified

### 功能缺口（真实阻断）

| 项 | blocker | 修复方向 |
| --- | --- | --- |
| RUN-006 | Provider in-flight transport cancellation | transport 循环内检查 CancellationToken |
| TOOL-006 | receipt/idempotency/retry 接入 lifecycle | runtime 主循环接入 Adapter private receipt |
| SES-002 | reasoning/provider continuation 恢复 | runtime 接入 provider continuation |
| SES-006 | resume 接入 runtime 主循环 | runtime.run 调用 resume_tool_calls |
| SES-008 | missing-handler recovery 接入 runtime | runtime 主循环接入 missing-handler 路径 |

### 覆盖/governance 缺口（非功能阻断）

| 项 | blocker | 修复方向 |
| --- | --- | --- |
| CFG-003 | CLI/Provider/构件输出面 secret 覆盖 | 补输出面 secret 测试 |
| PROV-007 | Provider identity envelope | 补 identity envelope 测试 |
| DOC-001 | 诊断/在线可运行混淆 | 文档修订 |
| OSS-009 | release governance 复核 | M6 governance review |
| OSS-010 | 私密报告能力 | release review |
| OSS-011 | 完整逐项 claim audit | 自动 claim audit |

## 3. 发布结论

**NO RELEASE**。Active P1 = 11 > 0，不满足 M6 发布门禁。

不得合入 `master` 或打发布 tag。

## 4. 下一步

1. 修复 5 项功能缺口（RUN-006、TOOL-006、SES-002/006/008）——runtime 主循环接入恢复路径
2. 补 6 项覆盖/governance（CFG-003、PROV-007、DOC-001、OSS-009/010/011）
3. Active P1 = 0 后重新进入 RC
4. live DeepSeek smoke 需要真实 API Key（硬阻断，需用户提供）