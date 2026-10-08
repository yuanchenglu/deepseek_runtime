# M6 RC / Alpha Release Gate Closeout

> Milestone: M6 RC / Alpha Release Gate
> Status: **CLOSED**
> 验证基线：`develop@9fb67ba`
> Release decision: **RELEASED v0.1.1a1**（master `3693786`、tag `v0.1.1a1`、GitHub Release 已发布）

## 1. Release Gate 执行结果

| Gate | 结果 |
| --- | --- |
| Active P0/P1 | **0**（98/98 Verified） |
| 本地全量单测 | 218 pass / 1 skip |
| M1 P0 Gate | 21/21 |
| M2 ExecutionAdapter Gate | 36/36 |
| M2 Runtime Lifecycle Gate | 64/64 |
| M2 Workspace P1 Gate | 12/12 |
| Minimum CI（3 OS × 3 Python + coverage + wheel/sdist + clean venv） | ✅ success |
| M2 三套 CI Gate | ✅ success |
| Live DeepSeek smoke | ✅ success=True, provider_status=200, leak_checks 全绿 |
| Release gate audit | ✅ 6/6（drill + live smoke + docs + manifest digest + tamper） |
| Secret scan | ✅ 161 tracked files inspected |
| Docs traceability | ✅ 98 blocking requirements, 110 blocking tests |

## 2. M6 完成范围

- **SES-002/006/008**：durable session resume 接入 `runtime.run()`（session_store 参数、checkpoint 持久化、同 session_id 恢复 messages/step/usage/evidence）
- **TOOL-006**：receipt lifecycle 验证（捕获、side-effect-uncertain、all_side_effect_receipts）
- **RUN-006**：before-call + tool cancellation 满足 TC-RUN-012/013（in-flight 属同步协议限制，文档声明）
- **CFG-003/PROV-007/DOC-001**：CLI secret-free、identity envelope、doctor 诊断语义测试
- **OSS-009/010/011**：release gate audit + docs traceability 验证
- **跨平台修复**：ChangeManager/workspace/drill 行尾（write_bytes）、diagnostics 可写探测、Windows UTF-8 输出（PYTHONIOENCODING + reconfigure）、CI clean venv 路径

## 3. 新增测试

- `tests/test_runtime_resume_m6.py`（3 tests）：durable resume
- `tests/test_governance_m6.py`（5 tests）：CFG-003/PROV-007/DOC-001

## 4. 发布结论

**RELEASED**。Active P1 = 0，所有 Gate 通过，live smoke pass。

RC 已合入 master（`3693786`）、tag `v0.1.1a1` 已推送、GitHub Release 已发布。