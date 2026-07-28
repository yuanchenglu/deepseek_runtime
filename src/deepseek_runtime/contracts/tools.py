"""Tool registration and argument-validation contract."""

from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .common import ContractViolation, ErrorCode, RuntimeErrorInfo, assert_json_compatible
from .state import RecoveryPolicy

_TOOL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,127}$")
ToolHandler = Callable[[dict[str, Any]], Any]


class ToolArgumentError(ContractViolation):
    pass


@dataclass(frozen=True, init=False)
class ToolSpec:
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
        if not _TOOL_NAME_RE.fullmatch(name):
            raise ValueError("invalid tool name")
        if not description or len(description) > 1024:
            raise ValueError("tool description must contain 1..1024 characters")
        if not isinstance(parameters, Mapping):
            raise ValueError("tool parameters must be a JSON Schema object")
        schema = copy.deepcopy(dict(parameters))
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ValueError(f"invalid tool parameter schema: {exc.message}") from exc
        if schema.get("type") != "object":
            raise ValueError("tool parameter schema root type must be object")
        if not risk or len(risk) > 64:
            raise ValueError("tool risk must contain 1..64 characters")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("tool timeout_seconds must be finite and positive")
        if max_output_bytes <= 0:
            raise ValueError("tool max_output_bytes must be positive")
        if side_effect and recovery_policy is RecoveryPolicy.PURE:
            raise ValueError("side-effect tools cannot use PURE recovery")
        if not side_effect and recovery_policy is not RecoveryPolicy.PURE:
            raise ValueError("non-side-effect tools must use PURE recovery")
        assert_json_compatible(schema)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "handler", handler)
        object.__setattr__(self, "risk", risk)
        object.__setattr__(self, "side_effect", side_effect)
        object.__setattr__(self, "timeout_seconds", timeout_seconds)
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
