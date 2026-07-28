"""Tool registration, lookup, argument validation, and result normalization."""

from __future__ import annotations

import copy
import json
import math
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .common import ContractViolation, ErrorCode, RuntimeErrorInfo, assert_json_compatible
from .state import RecoveryPolicy

_TOOL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,127}$")
_TOOL_RISKS = {
    "read",
    "write",
    "delete",
    "shell-safe",
    "shell-dangerous",
    "network",
    "git-mutating",
}
ToolHandler = Callable[[dict[str, Any]], Any]


class ToolArgumentError(ContractViolation):
    """Raised when model-supplied arguments violate a registered schema."""


class ToolResultError(ContractViolation):
    """Raised when a handler returns a value that cannot enter the Runtime protocol."""


@dataclass(frozen=True, init=False)
class ToolSpec:
    """Immutable registration contract for one production tool."""

    name: str
    description: str
    handler: ToolHandler = field(repr=False, compare=False)
    risk: str
    side_effect: bool
    timeout_seconds: float
    max_output_bytes: int
    recovery_policy: RecoveryPolicy
    _parameters_json: str = field(repr=False)

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Mapping[str, Any],
        handler: ToolHandler,
        risk: str = "read",
        side_effect: bool = False,
        timeout_seconds: float = 30.0,
        max_output_bytes: int = 100_000,
        recovery_policy: RecoveryPolicy = RecoveryPolicy.PURE,
    ) -> None:
        if not isinstance(name, str) or not _TOOL_NAME_RE.fullmatch(name):
            raise ValueError("invalid tool name")
        if not isinstance(description, str) or not description or len(description) > 1024:
            raise ValueError("tool description must contain 1..1024 characters")
        if not callable(handler):
            raise ValueError("tool handler must be callable")
        if not isinstance(parameters, Mapping):
            raise ValueError("tool parameters must be a JSON Schema object")
        if not isinstance(side_effect, bool):
            raise ValueError("tool side_effect must be a boolean")
        if not isinstance(recovery_policy, RecoveryPolicy):
            raise ValueError("tool recovery_policy must be a RecoveryPolicy")

        schema = copy.deepcopy(dict(parameters))
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ValueError(f"invalid tool parameter schema: {exc.message}") from exc
        if schema.get("type") != "object":
            raise ValueError("tool parameter schema root type must be object")

        if not isinstance(risk, str):
            raise ValueError("tool risk must be a registered risk category")
        normalized_risk = risk.strip().lower()
        if normalized_risk not in _TOOL_RISKS:
            raise ValueError("tool risk must be a registered risk category")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or timeout_seconds <= 0
        ):
            raise ValueError("tool timeout_seconds must be finite and positive")
        if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes <= 0:
            raise ValueError("tool max_output_bytes must be a positive integer")
        if side_effect and normalized_risk == "read":
            raise ValueError("side-effect tools must declare a non-read risk")
        if side_effect and recovery_policy is RecoveryPolicy.PURE:
            raise ValueError("side-effect tools cannot use PURE recovery")
        if not side_effect and recovery_policy is not RecoveryPolicy.PURE:
            raise ValueError("non-side-effect tools must use PURE recovery")

        assert_json_compatible(schema)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "handler", handler)
        object.__setattr__(self, "risk", normalized_risk)
        object.__setattr__(self, "side_effect", side_effect)
        object.__setattr__(self, "timeout_seconds", float(timeout_seconds))
        object.__setattr__(self, "max_output_bytes", max_output_bytes)
        object.__setattr__(self, "recovery_policy", recovery_policy)
        object.__setattr__(
            self,
            "_parameters_json",
            json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    @property
    def parameters(self) -> dict[str, Any]:
        value = json.loads(self._parameters_json)
        if not isinstance(value, dict):
            raise RuntimeError("stored tool schema is not an object")
        return value

    def provider_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate_arguments(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise ToolArgumentError(
                RuntimeErrorInfo(
                    ErrorCode.TOOL_ARGUMENT_INVALID,
                    "tool arguments must be an object",
                    details={"tool": self.name, "instance_type": type(arguments).__name__},
                )
            )
        validator = Draft202012Validator(self.parameters, format_checker=FormatChecker())
        errors = sorted(
            validator.iter_errors(arguments),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
        if errors:
            first = errors[0]
            path = [str(item) for item in first.absolute_path][:16]
            raise ToolArgumentError(
                RuntimeErrorInfo(
                    ErrorCode.TOOL_ARGUMENT_INVALID,
                    "tool arguments do not match the registered schema",
                    details={
                        "tool": self.name,
                        "path": path,
                        "validator": str(first.validator),
                        "error_count": len(errors),
                    },
                )
            )
        return dict(arguments)


def normalize_tool_result(value: Any, *, tool_name: str) -> str:
    """Convert supported handler results to deterministic tool-message text."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ToolResultError(
                RuntimeErrorInfo(
                    ErrorCode.TOOL_RESULT_INVALID,
                    "tool returned non-UTF-8 bytes",
                    details={"tool": tool_name},
                    cause_class=type(exc).__name__,
                )
            ) from exc
    try:
        assert_json_compatible(value)
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ToolResultError(
            RuntimeErrorInfo(
                ErrorCode.TOOL_RESULT_INVALID,
                "tool returned an unsupported result",
                details={"tool": tool_name, "result_type": type(value).__name__},
                cause_class=type(exc).__name__,
            )
        ) from exc


class ToolRegistry(Mapping[str, ToolSpec]):
    """The only supported production collection of executable tools."""

    def __init__(self, specs: Iterable[ToolSpec] = ()) -> None:
        self._specs: dict[str, ToolSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: ToolSpec) -> ToolSpec:
        if not isinstance(spec, ToolSpec):
            raise TypeError("ToolRegistry accepts ToolSpec instances only")
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool name: {spec.name}")
        self._specs[spec.name] = spec
        return spec

    def __getitem__(self, name: str) -> ToolSpec:
        return self._specs[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._specs)

    def __len__(self) -> int:
        return len(self._specs)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def provider_definitions(self) -> list[dict[str, Any]]:
        return [self._specs[name].provider_definition() for name in sorted(self._specs)]

    def resolve(self, name: str) -> ToolSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise ContractViolation(
                RuntimeErrorInfo(
                    ErrorCode.TOOL_NOT_FOUND,
                    "requested tool is not registered",
                    details={"tool": name},
                    cause_class=type(exc).__name__,
                )
            ) from exc

    def execute(self, name: str, arguments: Any) -> Any:
        spec = self.resolve(name)
        validated = spec.validate_arguments(arguments)
        return spec.handler(validated)
