# M2-G Integrated Closeout

> Milestone: M2-G Integrated Closeout — M2 综合验收
> Status: **CLOSED**
> 验证基线：`develop@dcd2342`
> Release decision: **NO RELEASE**

## 1. 验收范围

在最新 integrated `develop` 上复跑完整 M2 Requirement/Test matrix，确认：

- Registry/Policy/Approval/Adapter 无受支持生产 bypass；
- transition 合法/非法类别覆盖；
- Runtime/Tool/Workspace/Security/CLI P1 全部达到 M2 exit criteria；
- 未关闭项真实转移到 M3/M4，而不是用文档模糊处理。

## 2. 本地专项 Gate 证据（current develop head）

| Gate | 命令 | 结果 |
| --- | --- | --- |
| M1 P0 Gate | `scripts/m1_p0_gate.py --repetitions 5` | 35/35, 0 failures |
| M2 ExecutionAdapter Gate | `scripts/m2_execution_gate.py` | 36/36, 0 failures |
| M2 Runtime Lifecycle Gate | `scripts/m2_lifecycle_gate.py` | 64/64, 0 failures |
| M2 Workspace P1 Gate | `scripts/m2_workspace_gate.py` | 12/12, 0 failures |

全量单测：165 pass / 1 skip（Windows junction）。

## 3. M2 P1 状态

M2 范围内全部 `Verified`：

- Runtime：RUN-001~005、007~009；
- Tool：TOOL-001~005、007；
- Workspace：WS-001~005；
- Security：SEC-001、002、004~009；
- CLI：CLI-001~006。

## 4. 未关闭项真实转移

以下 M2 范围项未在本里程碑关闭，明确转移到后续里程碑：

| 项 | P | 转移至 | 原因 |
| --- | --- | --- | --- |
| RUN-006 | P1 | M4 | Provider in-flight transport cancellation 属 M4 |
| RUN-010 | P1 | M4 | arbitrary root、choices/message 全矩阵属 M4 Provider |
| TOOL-006 | P1 | M3 | receipt/idempotency/retry 与 Adapter private receipt 接入 lifecycle 属 M3 |
| SEC-003 | P1 | M3 | durable store、resume、migration 属 M3 |

这些项均非"文档模糊处理"，而是有明确 M3/M4 归属和 blocker。

## 5. Exit judgment

M2-G Exit Gate 满足：M2 全部 P1 达到 exit criteria，M2 范围完成项全部 Verified，未关闭项真实转移到 M3/M4。

M3 Recovery / Change / Evidence / Observability 为下一执行切片。

Repository release status remains **NO RELEASE**.