# M3 Recovery, Change, Evidence, Observability Closeout

> Milestone: M3 Recovery / Change / Evidence / Observability
> Status: **CLOSED**（核心实现完成；SES-002/006/008/OBS-004 真实转移 M4）
> 验证基线：`develop@405e33c`
> Release decision: **NO RELEASE**

## 1. 完成范围

### Change（CHG-003~010）

- CHG-003：apply 拒绝同一 change_set 重复路径（CHANGE_CONFLICT）
- CHG-004：进程内锁串行化 apply/rollback，避免并发同路径竞争
- CHG-005：opaque handle + 受约束回滚（已有，补测试）
- CHG-006：文件 mode 在 apply/rollback 后保留
- CHG-007：写入后 fsync 文件与父目录（crash-during-restore 防护）
- CHG-008：audit 事件 content-free 结构化
- CHG-009：best-effort 多文件事务，失败时补偿已应用文件
- CHG-010：restart/expiry/scope 约束（已有，补测试）

### Recovery（SES-001~010）

- SES-001：checkpoint/evidence schema 分离
- SES-003：SessionStore 可选 Fernet 加密 at rest（新增依赖 cryptography）
- SES-004：原子写入 + 损坏检测
- SES-005：legacy schema (1.0) 迁移
- SES-009：retry budget 限制
- SES-010：operator 决策 + receipt roundtrip

### Evidence（EVD-001~008）

- EVD-001/002：公开 evidence 无 API Key/prompt/response/reasoning 正文
- EVD-003：request/response_evidence 对任意输入为 total function（修复 None/非 list 崩溃）
- EVD-004：canonical JSON 稳定
- EVD-005：低熵敏感文本不暴露可猜值
- EVD-006：evidence schema 版本化
- EVD-007：CLI --unsafe-debug-content 危险开关 gate
- EVD-008：error 字段 secret redaction

### Observability（OBS-001~006）

- OBS-001：latency 元数据
- OBS-002：usage/cache/cost 统计
- OBS-005：_float_or_none 拒绝 NaN/inf/负 cost（修复透传缺陷）
- OBS-006：success/first-completion 分母只使用已知值

## 2. 测试证据

| 测试文件 | 覆盖 | 结果 |
| --- | --- | --- |
| tests/test_change_manager_m3.py | CHG-003~009 | 6 tests pass |
| tests/test_recovery_m3.py | SES-001/003/004/005/009/010 | 7 tests pass |
| tests/test_evidence_observability_m3.py | EVD-001~008, OBS-001~006 | 11 tests pass |
| 全量回归 | 全部 | 189 pass / 1 skip |

## 3. 未关闭项真实转移 M4

| 项 | 原因 | 转移至 |
| --- | --- | --- |
| SES-002 | 完整 reasoning/provider continuation 恢复未完成 | M4 Provider |
| SES-006 | durable 恢复未接入 runtime 主循环（内存 handoff 已实现） | M4/M3 |
| SES-008 | missing-handler 恢复逻辑已实现，未接入 runtime 主循环 | M4/M3 |
| OBS-004 | 输入成本漏算（输入 token 未拆分成本） | M4 |

## 4. Exit judgment

M3 核心实现完成：ChangeManager 鲁棒性、SessionStore 加密/迁移/损坏检测、Evidence total-function/redaction、Observability 非法值拒绝。未关闭项（SES-002/006/008、OBS-004）真实转移 M4。

M4 Provider / Config / Protocol 为下一执行切片。

Repository release status remains **NO RELEASE**.