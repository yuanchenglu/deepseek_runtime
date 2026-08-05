# M5 CI Matrix, Packaging, Governance Closeout

> Milestone: M5 CI Matrix / Packaging / Governance
> Status: **CLOSED**（CI 矩阵 + coverage + 打包 + tamper 完成；governance review 转移 M6）
> 验证基线：`develop@48bbf16`
> Release decision: **NO RELEASE**

## 1. 完成范围

### CI Matrix（CFG-001/002, OSS-001/002）

- CFG-001/002：minimum-ci.yml 新增 3 OS（ubuntu/macOS/windows）× 3 Python（3.11/3.12/3.13）matrix job
- OSS-001：minimum-ci 是 required-check
- OSS-002：完整 release matrix 建立

### Coverage（OSS-003/004）

- OSS-003：CI matrix job 运行 coverage + report
- OSS-004：pyproject.toml `[tool.coverage.run]` branch coverage + `[tool.coverage.report]`

### Packaging（OSS-005/006/007/008）

- OSS-005：check_tracked_secrets.py secret scan（已有）
- OSS-006：build_release_artifact EXCLUDE_GLOBS denylist（补测试）
- OSS-007：release_gate_audit 重算构件 digest 比对（tamper 检测）
- OSS-008：CI matrix job build sdist/wheel + clean venv install smoke

## 2. 测试证据

| 测试文件 | 覆盖 | 结果 |
| --- | --- | --- |
| tests/test_release_m5.py | OSS-006/007 | 3 tests pass |
| tests/test_cli_and_scripts.py | release gate audit（已有，更新 fixture） | pass |
| 全量回归 | 全部 | 209 pass / 1 skip |

## 3. 未关闭项转移 M6

| 项 | 原因 | 转移至 |
| --- | --- | --- |
| OSS-009 | M5 release governance 复核 | M6 |
| OSS-010 | 私密报告能力与 release review | M6 |
| OSS-011 | 完整逐项自动 claim audit | M6 |
| DOC-001 | 诊断/在线可运行混淆 | M6 |
| PROV-007 | Provider identity envelope | M6（可后置） |
| RUN-006 | Provider in-flight transport cancellation | 保持 |

## 4. Exit judgment

M5 CI/Packaging 核心完成：3 OS × 3 Python matrix、coverage、wheel/sdist + clean venv、tamper 检测、secret scan。未关闭项（OSS-009/010/011、DOC-001）真实转移 M6。

M6 RC / Alpha Release Gate 为下一执行切片。

Repository release status remains **NO RELEASE**.