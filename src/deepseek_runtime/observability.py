"""
可观测性层（Observability Layer）—— Agent 跑了多少任务？花了多少钱？

❓ 问：CEO/产品经理最关心什么问题？
💡 答：Agent 好用吗？花了多少钱？有没有优化空间？
   observability.py 就是回答这些问题的——它把 Agent 每次运行的"体检报告"
   汇总成结构化数据：成功了多少次、缓存命中了多少 token、大概花了多少钱。

参考 llm-harness-agent 论文 A1（Agent Harness Survey）中关于可观测性组件
的讨论：「缓存可见性和任务成功率、成本应该在同一证据流里，而不是孤立指标。」
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

# 敏感标记：如果字符串包含这些关键词，说明它可能是敏感信息，需要脱敏
SENSITIVE_MARKERS = ("authorization", "bearer", "password", "api_key", "token", "secret")


@dataclass
class Observation:
    """一条"观察记录"——代表一次 Agent 任务执行的结构化摘要。

    ❓ 问：类比一下，Observation 像什么？
    💡 答：像快递的物流单——记录了每个包裹（任务）的发货时间、谁送的、
       有没有送到、花了多少运费。把散乱的物流数据汇总就成了"运营报表"。

    参考 llm-harness-agent 论文 D1: Memory Mechanism Survey 中关于
    Agent 记忆结构化的讨论：原始日志需要被结构化为标准格式才能做分析。
    """
    task_id: str | None
    model: str | None
    route_reason: str | None
    success: bool | None
    first_completion: bool | None
    prompt_cache_hit_tokens: int | None
    prompt_cache_miss_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None

    def to_dict(self) -> dict[str, Any]:
        """把 Observation 转成普通字典，方便序列化成 JSON"""
        return self.__dict__.copy()


def _safe_string(value: Any) -> str | None:
    """安全字符串：如果包含敏感关键词则替换为 [redacted]"""
    if not isinstance(value, str):
        return None
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return "[redacted]"
    return value


def _int_or_none(value: Any) -> int | None:
    """把值安全转成整数（布尔值不转，字符串不转）"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _float_or_none(value: Any) -> float | None:
    """把值安全转成浮点数（OBS-005：拒绝 NaN/inf/负数）"""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            parsed = float(value)
        except (ValueError, OverflowError):
            return None
        if not math.isfinite(parsed) or parsed < 0:
            return None
        return parsed
    return None


def _first_int(*values: Any) -> int | None:
    """从多个值中取第一个有效整数"""
    for value in values:
        parsed = _int_or_none(value)
        if parsed is not None:
            return parsed
    return None


def _iter_rows(data: Any) -> Iterable[tuple[dict[str, Any], str | None]]:
    """统一遍历按模型分组、rows、列表或单字典输入。"""
    if isinstance(data, dict) and isinstance(data.get("models"), dict):
        for model, result in data["models"].items():
            if isinstance(result, dict):
                for row in result.get("rows", []):
                    if isinstance(row, dict):
                        yield row, model
        return
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        for row in data["rows"]:
            if isinstance(row, dict):
                yield row, None
        return
    if isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                yield row, None
        return
    if isinstance(data, dict):
        yield data, None


def _usage_from(row: dict[str, Any]) -> dict[str, Any]:
    tokens = row.get("tokens")
    if isinstance(tokens, dict):
        return tokens
    usage = row.get("usage")
    if isinstance(usage, dict):
        return usage
    return {}


def _cache_from(row: dict[str, Any], usage: dict[str, Any]) -> dict[str, Any]:
    cache = row.get("cache")
    if isinstance(cache, dict):
        return cache
    details = usage.get("prompt_tokens_details")
    return details if isinstance(details, dict) else {}


def _model_from(row: dict[str, Any], group_model: str | None) -> str | None:
    metadata_value = row.get("metadata")
    metadata = metadata_value if isinstance(metadata_value, dict) else {}
    request_value = row.get("request_evidence")
    request = request_value if isinstance(request_value, dict) else {}
    return _safe_string(row.get("model") or metadata.get("model") or request.get("model") or group_model)


def _route_reason_from(row: dict[str, Any]) -> str | None:
    metadata_value = row.get("metadata")
    metadata = metadata_value if isinstance(metadata_value, dict) else {}
    return _safe_string(row.get("route_reason") or metadata.get("route_reason"))


def _success_from(row: dict[str, Any]) -> bool | None:
    if isinstance(row.get("success"), bool):
        return row["success"]
    status = _int_or_none(row.get("status"))
    if status is not None:
        return 200 <= status < 300 and not row.get("error")
    return None


def _estimated_cost(
    usage: dict[str, Any],
    cache: dict[str, Any],
    model: str | None,
    pricing: dict[str, Any],
    explicit_cost: Any,
) -> float | None:
    provided = _float_or_none(explicit_cost)
    if provided is not None:
        return provided
    if not model:
        return None
    models = pricing.get("models")
    model_prices = models.get(model) if isinstance(models, dict) else None
    if not isinstance(model_prices, dict):
        return None
    unit = _int_or_none(pricing.get("unit_tokens")) or 1_000_000
    hit = _first_int(
        usage.get("prompt_cache_hit_tokens"),
        usage.get("cache_hit_tokens"),
        cache.get("cached_tokens"),
        cache.get("hit_tokens"),
        0,
    ) or 0
    miss = _first_int(
        usage.get("prompt_cache_miss_tokens"),
        usage.get("cache_miss_tokens"),
        cache.get("miss_tokens"),
        0,
    ) or 0
    output = _first_int(usage.get("completion_tokens"), usage.get("output_tokens"), 0) or 0
    # OBS-004：当无 cache 拆分但有 prompt_tokens 时，输入成本不漏算
    if hit == 0 and miss == 0:
        prompt = _first_int(usage.get("prompt_tokens"), usage.get("input_tokens"), 0) or 0
        if prompt > 0:
            miss = prompt
    total = (
        hit * float(model_prices["cache_hit_input"])
        + miss * float(model_prices["cache_miss_input"])
        + output * float(model_prices["output"])
    ) / unit
    return round(total, 12)


def _observation_from(
    row: dict[str, Any], group_model: str | None, pricing: dict[str, Any]
) -> Observation:
    usage = _usage_from(row)
    cache = _cache_from(row, usage)
    model = _model_from(row, group_model)
    cost = _estimated_cost(usage, cache, model, pricing, row.get("estimated_cost", row.get("cost")))
    return Observation(
        task_id=_safe_string(row.get("task_id") or row.get("experiment")),
        model=model,
        route_reason=_route_reason_from(row),
        success=_success_from(row),
        first_completion=row.get("first_completion") if isinstance(row.get("first_completion"), bool) else None,
        prompt_cache_hit_tokens=_first_int(
            usage.get("prompt_cache_hit_tokens"),
            usage.get("cache_hit_tokens"),
            cache.get("cached_tokens"),
            cache.get("hit_tokens"),
        ),
        prompt_cache_miss_tokens=_first_int(
            usage.get("prompt_cache_miss_tokens"), usage.get("cache_miss_tokens"), cache.get("miss_tokens")
        ),
        completion_tokens=_first_int(usage.get("completion_tokens"), usage.get("output_tokens")),
        total_tokens=_first_int(usage.get("total_tokens")),
        estimated_cost_usd=cost,
    )


def _check(name: str, ok: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "ok": ok, "evidence": evidence}


def summarize_observability(data: Any, pricing: dict[str, Any], source: str) -> dict[str, Any]:
    observations = [_observation_from(row, group_model, pricing) for row, group_model in _iter_rows(data)]
    successes = sum(1 for item in observations if item.success is True)
    known_success = sum(1 for item in observations if item.success is not None)
    cost_total = round(sum(item.estimated_cost_usd or 0.0 for item in observations), 12)

    summary = {
        "source": source,
        "task_count": len(observations),
        "successes": successes,
        "failures": sum(1 for item in observations if item.success is False),
        "success_rate": round(successes / known_success, 6) if known_success else None,
        "first_completion_rate": round(
            sum(1 for item in observations if item.first_completion is True) / len(observations), 6
        ) if observations else None,
        "models": sorted({item.model for item in observations if item.model}),
        "route_reasons": sorted({item.route_reason for item in observations if item.route_reason}),
        "prompt_cache_hit_tokens": sum(item.prompt_cache_hit_tokens or 0 for item in observations),
        "prompt_cache_miss_tokens": sum(item.prompt_cache_miss_tokens or 0 for item in observations),
        "completion_tokens": sum(item.completion_tokens or 0 for item in observations),
        "total_tokens": sum(item.total_tokens or 0 for item in observations),
        "estimated_cost_usd": cost_total,
        "tokens_per_success": round(
            sum(item.total_tokens or 0 for item in observations) / successes, 6
        ) if successes else None,
        "cost_per_success_usd": round(cost_total / successes, 12) if successes else None,
        "pricing_snapshot_date": pricing.get("snapshot_date"),
        "pricing_source": pricing.get("source"),
    }

    checks = [
        _check(
            "route_visible",
            bool(observations) and all(item.model and item.route_reason for item in observations),
            {"models": len(summary["models"]), "route_reasons": len(summary["route_reasons"])},
        ),
        _check(
            "usage_visible",
            bool(observations) and all(item.total_tokens is not None for item in observations),
            {"total_tokens": summary["total_tokens"]},
        ),
        _check(
            "cache_usage_visible",
            bool(observations) and all(
                item.prompt_cache_hit_tokens is not None and item.prompt_cache_miss_tokens is not None
                for item in observations
            ),
            {
                "hit_tokens": summary["prompt_cache_hit_tokens"],
                "miss_tokens": summary["prompt_cache_miss_tokens"],
            },
        ),
        _check(
            "cost_estimated",
            bool(observations) and all(item.estimated_cost_usd is not None for item in observations),
            {"estimated_cost_usd": summary["estimated_cost_usd"]},
        ),
        _check("success_rate_visible", summary["success_rate"] is not None, {"success_rate": summary["success_rate"]}),
        _check(
            "tokens_per_success_visible",
            summary["tokens_per_success"] is not None,
            {"tokens_per_success": summary["tokens_per_success"]},
        ),
        _check(
            "cost_per_success_visible",
            summary["cost_per_success_usd"] is not None,
            {"cost_per_success_usd": summary["cost_per_success_usd"]},
        ),
    ]

    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "success": all(check["ok"] for check in checks),
        "summary": summary,
        "observations": [item.to_dict() for item in observations],
        "checks": checks,
        "warning": "本报告基于规则推导（状态码判断成功、定价表估算成本），不代表实际账单。",
    }
