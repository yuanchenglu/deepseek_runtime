"""Runtime lifecycle, budget, and checkpoint-handoff contracts for M2-D."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .contracts import (
    ErrorCode,
    RecoverableCheckpoint,
    RuntimeErrorInfo,
    RuntimeState,
    TransitionRule,
    validate_transition,
)


class ToolErrorPolicy(str, Enum):
    """Decide whether a structured tool error returns to the Provider or stops the run."""

    CONTINUE = "continue"
    TERMINATE = "terminate"


@dataclass(frozen=True)
class RuntimeBudgets:
    """Optional task limits. Unknown usage is never converted to zero."""

    max_steps: int | None = None
    max_tokens: int | None = None
    max_cost_usd: float | None = None
    max_context_tokens: int | None = None
    max_elapsed_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("max_steps", "max_tokens", "max_context_tokens"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value <= 0
            ):
                raise ValueError(f"{name} must be a positive integer or None")
        for name in ("max_cost_usd", "max_elapsed_seconds"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value <= 0
            ):
                raise ValueError(f"{name} must be finite and positive or None")

    def to_dict(self) -> dict[str, int | float | None]:
        return {
            "max_steps": self.max_steps,
            "max_tokens": self.max_tokens,
            "max_cost_usd": self.max_cost_usd,
            "max_context_tokens": self.max_context_tokens,
            "max_elapsed_seconds": self.max_elapsed_seconds,
        }


@dataclass(frozen=True)
class LifecycleEvent:
    """Content-minimized record for one validated RuntimeState transition."""

    sequence: int
    event: str
    source: RuntimeState
    target: RuntimeState
    step: int
    checkpoint_required: bool

    def __post_init__(self) -> None:
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence <= 0:
            raise ValueError("lifecycle event sequence must be a positive integer")
        if not isinstance(self.step, int) or isinstance(self.step, bool) or self.step < 0:
            raise ValueError("lifecycle event step must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event": self.event,
            "source": self.source.value,
            "target": self.target.value,
            "step": self.step,
            "checkpoint_required": self.checkpoint_required,
        }


@dataclass
class LifecycleTrace:
    """Validate and retain the single production Runtime lifecycle."""

    state: RuntimeState = RuntimeState.CREATED
    events: list[LifecycleEvent] = field(default_factory=list)

    def transition(
        self,
        target: RuntimeState,
        *,
        step: int,
        approval_present: bool = False,
        receipt_present: bool = False,
        side_effect: bool = False,
    ) -> TransitionRule:
        if not isinstance(step, int) or isinstance(step, bool) or step < 0:
            raise ValueError("lifecycle transition step must be a non-negative integer")
        source = self.state
        rule = validate_transition(
            source,
            target,
            approval_present=approval_present,
            receipt_present=receipt_present,
            side_effect=side_effect,
        )
        self.state = target
        self.events.append(
            LifecycleEvent(
                sequence=len(self.events) + 1,
                event=rule.event,
                source=source,
                target=target,
                step=step,
                checkpoint_required=rule.checkpoint,
            )
        )
        return rule


class CheckpointSink(Protocol):
    """Host handoff for one private checkpoint snapshot; durability is not implied."""

    def __call__(self, checkpoint: RecoverableCheckpoint) -> None:
        ...


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _nonnegative_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _first_int(usage: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        parsed = _nonnegative_int(usage.get(key))
        if parsed is not None:
            return parsed
    return None


def _request_tokens(usage: Mapping[str, Any]) -> int | None:
    explicit = _first_int(usage, "total_tokens")
    if explicit is not None:
        return explicit
    prompt = _first_int(usage, "prompt_tokens", "input_tokens")
    completion = _first_int(usage, "completion_tokens", "output_tokens")
    if prompt is None or completion is None:
        return None
    return prompt + completion


def _context_tokens(usage: Mapping[str, Any]) -> int | None:
    return _first_int(usage, "prompt_tokens", "input_tokens", "context_tokens")


def _request_cost(usage: Mapping[str, Any]) -> float | None:
    for key in ("estimated_cost_usd", "cost_usd"):
        parsed = _nonnegative_float(usage.get(key))
        if parsed is not None:
            return parsed
    return None


_SAFE_USAGE_INT_KEYS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "input_tokens",
    "output_tokens",
    "context_tokens",
    "prompt_cache_hit_tokens",
    "prompt_cache_miss_tokens",
    "cache_hit_tokens",
    "cached_tokens",
    "reasoning_tokens",
)
_SAFE_USAGE_FLOAT_KEYS = ("estimated_cost_usd", "cost_usd")


def safe_usage_evidence(usage_value: Any) -> dict[str, int | float]:
    """Expose only recognized non-negative numeric usage fields."""
    if not isinstance(usage_value, Mapping):
        return {}
    output: dict[str, int | float] = {}
    for key in _SAFE_USAGE_INT_KEYS:
        value = _nonnegative_int(usage_value.get(key))
        if value is not None:
            output[key] = value
    for key in _SAFE_USAGE_FLOAT_KEYS:
        value = _nonnegative_float(usage_value.get(key))
        if value is not None:
            output[key] = value
    return output


@dataclass
class BudgetTracker:
    """Track only known usage and produce deterministic budget-stop errors."""

    budgets: RuntimeBudgets
    clock: Callable[[], float] = time.monotonic
    started_at: float = field(init=False)
    completed_steps: int = 0
    _total_tokens: int = 0
    _tokens_known: bool = True
    _token_samples: int = 0
    _total_cost_usd: float = 0.0
    _cost_known: bool = True
    _cost_samples: int = 0
    _context_tokens: int | None = None
    _context_known: bool = False

    def __post_init__(self) -> None:
        self.started_at = self.clock()

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, self.clock() - self.started_at)

    def before_provider(self, next_step: int) -> RuntimeErrorInfo | None:
        if self.budgets.max_steps is not None and next_step > self.budgets.max_steps:
            return RuntimeErrorInfo(
                ErrorCode.BUDGET_STEP_EXCEEDED,
                "Runtime step budget was exceeded",
                details={
                    "limit": self.budgets.max_steps,
                    "completed_steps": self.completed_steps,
                },
            )
        return self._time_error()

    def record_provider(self, usage_value: Any, *, step: int) -> None:
        self.completed_steps = step
        if not isinstance(usage_value, Mapping):
            self._tokens_known = False
            self._cost_known = False
            self._context_tokens = None
            self._context_known = False
            return

        tokens = _request_tokens(usage_value)
        self._token_samples += 1
        if tokens is None:
            self._tokens_known = False
        else:
            self._total_tokens += tokens

        cost = _request_cost(usage_value)
        self._cost_samples += 1
        if cost is None:
            self._cost_known = False
        else:
            self._total_cost_usd += cost

        context = _context_tokens(usage_value)
        self._context_tokens = context
        self._context_known = context is not None

    def after_provider(self) -> RuntimeErrorInfo | None:
        if (
            self.budgets.max_tokens is not None
            and self.total_tokens is not None
            and self.total_tokens >= self.budgets.max_tokens
        ):
            return RuntimeErrorInfo(
                ErrorCode.BUDGET_TOKEN_EXCEEDED,
                "Runtime token budget was reached",
                details={"limit": self.budgets.max_tokens, "observed": self.total_tokens},
            )
        if (
            self.budgets.max_cost_usd is not None
            and self.total_cost_usd is not None
            and self.total_cost_usd >= self.budgets.max_cost_usd
        ):
            return RuntimeErrorInfo(
                ErrorCode.BUDGET_COST_EXCEEDED,
                "Runtime cost budget was reached",
                details={
                    "limit": self.budgets.max_cost_usd,
                    "observed": self.total_cost_usd,
                },
            )
        if (
            self.budgets.max_context_tokens is not None
            and self.context_tokens is not None
            and self.context_tokens >= self.budgets.max_context_tokens
        ):
            return RuntimeErrorInfo(
                ErrorCode.BUDGET_CONTEXT_EXCEEDED,
                "Runtime context budget was reached",
                details={
                    "limit": self.budgets.max_context_tokens,
                    "observed": self.context_tokens,
                },
            )
        return self._time_error()

    def after_tool(self) -> RuntimeErrorInfo | None:
        return self._time_error()

    def _time_error(self) -> RuntimeErrorInfo | None:
        limit = self.budgets.max_elapsed_seconds
        elapsed = self.elapsed_seconds
        if limit is not None and elapsed >= limit:
            return RuntimeErrorInfo(
                ErrorCode.BUDGET_TIME_EXCEEDED,
                "Runtime time budget was reached",
                details={"limit": limit, "observed": elapsed},
            )
        return None

    @property
    def total_tokens(self) -> int | None:
        if self._token_samples == 0 or not self._tokens_known:
            return None
        return self._total_tokens

    @property
    def total_cost_usd(self) -> float | None:
        if self._cost_samples == 0 or not self._cost_known:
            return None
        return round(self._total_cost_usd, 12)

    @property
    def context_tokens(self) -> int | None:
        return self._context_tokens if self._context_known else None

    def snapshot(self) -> dict[str, Any]:
        total_tokens = self.total_tokens
        total_cost = self.total_cost_usd
        context_tokens = self.context_tokens
        return {
            "limits": self.budgets.to_dict(),
            "observed": {
                "completed_steps": self.completed_steps,
                "total_tokens": total_tokens,
                "total_tokens_known": total_tokens is not None,
                "cost_usd": total_cost,
                "cost_known": total_cost is not None,
                "context_tokens": context_tokens,
                "context_known": context_tokens is not None,
                "elapsed_ms": int(self.elapsed_seconds * 1000),
            },
        }
