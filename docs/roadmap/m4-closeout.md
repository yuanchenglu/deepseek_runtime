# M4 Provider, Config, Protocol Closeout

> Milestone: M4 Provider / Config / Protocol
> Status: **CLOSED**（Provider 核心完成；CFG-001/002/003、PROV-007、RUN-006、DOC-001 转移 M5 or 保持）
> 验证基线：`develop@6efd24b`
> Release decision: **NO RELEASE**

## 1. 完成范围

### Provider（PROV-001~009）

- PROV-001：ProviderResult 接入 runtime lifecycle/RuntimeResult
- PROV-002：arbitrary JSON root 不崩溃（normalization）
- PROV-003：malformed response 分类（body/choices/choice/message/tool_calls/call id）
- PROV-004：error-code 分类（PROVIDER_RESPONSE_INVALID）
- PROV-005：retry/backoff（5xx/网络错误重试，4xx 不重试，指数退避）
- PROV-006：response-size limit（普通 + 流式）
- PROV-008：增量 SSE parser（iter_sse_events，跨 chunk UTF-8 split 和事件行拼接）
- PROV-009：chat_stream 消费增量事件

### Config（CFG-004/005）

- CFG-004：RuntimeSettings 配置校验（max_retries/字节/超时/token 非法拒绝）
- CFG-005：from_env 干净语义，解析 retry/limit 配置

## 2. 测试证据

| 测试文件 | 覆盖 | 结果 |
| --- | --- | --- |
| tests/test_provider_m4.py | PROV-005/006, CFG-004/005 | 8 tests pass |
| tests/test_provider_malformed_m4.py | PROV-002/003/004 | 3 tests pass |
| tests/test_streaming_m4.py | PROV-008/009 | 6 tests pass |
| 全量回归 | 全部 | 206 pass / 1 skip |

## 3. 未关闭项转移

| 项 | 原因 | 转移至 |
| --- | --- | --- |
| CFG-001 | 完整 Python 版本矩阵未建立 | M5 |
| CFG-002 | 多版本 source 未建立 | M5 |
| CFG-003 | CLI/Provider/构件输出面 secret 覆盖未完全 | M5 |
| PROV-007 | Provider identity envelope 仍不完整 | M5（可后置） |
| RUN-006 | Provider in-flight transport cancellation 未实现（before-call 已实现） | M4 增强，保持 |
| DOC-001 | 诊断/在线可运行混淆 | M5 文档 |

## 4. Exit judgment

M4 Provider 核心完成：retry/backoff、response-size limit、malformed 分类、增量 SSE parser、config 校验。未关闭项（CFG-001/002/003、PROV-007、RUN-006、DOC-001）真实转移 M5 或保持。

M5 CI Matrix / Packaging / Governance 为下一执行切片。

Repository release status remains **NO RELEASE**.