from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from deepseek_runtime import (
    ApprovalOutcome,
    ApprovalRequest,
    Decision,
    DeepSeekRuntime,
    ErrorCode,
    PermissionPolicy,
    PermissionRequest,
    PermissionRule,
    ProviderResult,
    RecoveryPolicy,
    Risk,
    ToolRegistry,
    ToolSpec,
)


PARAMETERS = {
    "type": "object",
    "additionalProperties": True,
}


class SequencedClient:
    def __init__(self, messages: Iterable[dict[str, Any]]) -> None:
        self.messages = list(messages)
        self.payloads: list[dict[str, Any]] = []

    def chat(self, payload: dict[str, Any]) -> ProviderResult:
        self.payloads.append(payload)
        if not self.messages:
            raise AssertionError("fake provider received an unexpected request")
        message = self.messages.pop(0)
        return ProviderResult(
            status=200,
            elapsed_ms=0,
            body={"choices": [{"message": message}], "usage": {}},
            request_fingerprint="policy-test",
            request_payload=payload,
        )


class RecordingApprovalProvider:
    def __init__(self, outcomes: Iterable[ApprovalOutcome]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[ApprovalRequest] = []

    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        self.requests.append(request)
        if not self.outcomes:
            raise AssertionError("approval provider received an unexpected request")
        return self.outcomes.pop(0)


class RaisingApprovalProvider:
    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        raise RuntimeError("private approval failure")


def make_spec(
    risk: Risk,
    handler: Any,
    *,
    name: str = "sample",
) -> ToolSpec:
    side_effect = risk is not Risk.READ
    return ToolSpec(
        name,
        "Policy test tool.",
        PARAMETERS,
        handler,
        risk=risk,
        side_effect=side_effect,
        recovery_policy=(
            RecoveryPolicy.NON_IDEMPOTENT if side_effect else RecoveryPolicy.PURE
        ),
    )


def tool_call(
    arguments: dict[str, Any],
    *,
    name: str = "sample",
    call_id: str = "call-1",
) -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def assistant_tool_message(*calls: dict[str, Any]) -> dict[str, Any]:
    return {"role": "assistant", "content": None, "tool_calls": list(calls)}


def final_message() -> dict[str, Any]:
    return {"role": "assistant", "content": "done"}


def tool_contents(result: Any) -> list[str]:
    return [
        str(message["content"])
        for message in result.messages
        if message.get("role") == "tool"
    ]


def tool_error_code(content: str) -> str:
    return str(json.loads(content)["error"]["code"])


def run_runtime(
    registry: ToolRegistry,
    calls: list[dict[str, Any]],
    *,
    policy: PermissionPolicy | None = None,
    approval_provider: Any = None,
) -> Any:
    client = SequencedClient((assistant_tool_message(*calls), final_message()))
    with tempfile.TemporaryDirectory() as workspace:
        return DeepSeekRuntime(client).run(
            [{"role": "user", "content": "test"}],
            workspace=Path(workspace),
            tools=registry,
            policy=policy,
            approval_provider=approval_provider,
        )


class PermissionPolicyTests(unittest.TestCase):
    def test_tc_sec_001_default_policy_allows_only_read(self) -> None:
        policy = PermissionPolicy()
        expected = {
            Risk.READ: Decision.ALLOW,
            Risk.WRITE: Decision.DENY,
            Risk.DELETE: Decision.DENY,
            Risk.NETWORK: Decision.DENY,
            Risk.SHELL_SAFE: Decision.DENY,
            Risk.SHELL_DANGEROUS: Decision.DENY,
            Risk.GIT_MUTATING: Decision.DENY,
        }

        for risk, decision in expected.items():
            with self.subTest(risk=risk):
                self.assertIs(
                    policy.decide(PermissionRequest(risk=risk, path="")),
                    decision,
                )

    def test_tc_sec_002_last_matching_rule_has_stable_precedence(self) -> None:
        wildcard_deny = PermissionRule(
            risk=Risk.WRITE,
            decision=Decision.DENY,
            path_glob="*",
        )
        specific_allow = PermissionRule(
            risk=Risk.WRITE,
            decision=Decision.ALLOW,
            path_glob="docs/*",
        )
        request = PermissionRequest(risk=Risk.WRITE, path="docs/plan.md")

        self.assertIs(
            PermissionPolicy([wildcard_deny, specific_allow]).decide(request),
            Decision.ALLOW,
        )
        self.assertIs(
            PermissionPolicy([specific_allow, wildcard_deny]).decide(request),
            Decision.DENY,
        )


class RuntimePolicyApprovalTests(unittest.TestCase):
    def test_tc_sec_004_default_non_read_denial_executes_no_handler(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal calls
            calls += 1
            return "executed"

        registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
        result = run_runtime(registry, [tool_call({"path": "docs/a.md"})])

        self.assertTrue(result.ok)
        self.assertEqual(calls, 0)
        self.assertEqual(
            tool_error_code(tool_contents(result)[0]),
            ErrorCode.POLICY_DENIED.value,
        )
        event = result.evidence[0]["authorization_events"][0]
        self.assertEqual(event["policy_decision"], Decision.DENY.value)

    def test_explicit_allow_executes_handler(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal calls
            calls += 1
            return "executed"

        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ALLOW, path_glob="docs/*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
        result = run_runtime(
            registry,
            [tool_call({"path": "docs/a.md"})],
            policy=policy,
        )

        self.assertTrue(result.ok)
        self.assertEqual(calls, 1)
        self.assertEqual(tool_contents(result)[0], "executed")
        self.assertEqual(policy.audit_events[0]["path"], None)
        self.assertTrue(policy.audit_events[0]["path_present"])

    def test_specific_path_rule_does_not_match_missing_path(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal calls
            calls += 1
            return "executed"

        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ALLOW, path_glob="docs/*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
        result = run_runtime(registry, [tool_call({})], policy=policy)

        self.assertEqual(calls, 0)
        self.assertEqual(
            tool_error_code(tool_contents(result)[0]),
            ErrorCode.POLICY_DENIED.value,
        )

    def test_tc_sec_003_approve_once_applies_only_to_current_call(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal calls
            calls += 1
            return "executed"

        provider = RecordingApprovalProvider(
            (ApprovalOutcome.APPROVE_ONCE, ApprovalOutcome.APPROVE_ONCE)
        )
        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
        repeated = tool_call({"path": "docs/a.md"})
        result = run_runtime(
            registry,
            [repeated, {**repeated, "id": "call-2"}],
            policy=policy,
            approval_provider=provider,
        )

        self.assertTrue(result.ok)
        self.assertEqual(calls, 2)
        self.assertEqual(len(provider.requests), 2)

    def test_tc_sec_003_session_approval_reuses_exact_request(self) -> None:
        calls = 0

        def handler(arguments: dict[str, Any]) -> str:
            nonlocal calls
            calls += 1
            return "executed"

        provider = RecordingApprovalProvider((ApprovalOutcome.APPROVE_SESSION,))
        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
        repeated = tool_call({"path": "docs/a.md"})
        result = run_runtime(
            registry,
            [repeated, {**repeated, "id": "call-2"}],
            policy=policy,
            approval_provider=provider,
        )

        self.assertTrue(result.ok)
        self.assertEqual(calls, 2)
        self.assertEqual(len(provider.requests), 1)
        events = result.evidence[0]["authorization_events"]
        self.assertFalse(events[0]["cached_session_approval"])
        self.assertTrue(events[1]["cached_session_approval"])

    def test_session_approval_does_not_cover_different_arguments(self) -> None:
        provider = RecordingApprovalProvider(
            (ApprovalOutcome.APPROVE_SESSION, ApprovalOutcome.APPROVE_ONCE)
        )
        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, lambda arguments: "executed"),))
        result = run_runtime(
            registry,
            [
                tool_call({"path": "docs/a.md"}),
                tool_call({"path": "docs/b.md"}, call_id="call-2"),
            ],
            policy=policy,
            approval_provider=provider,
        )

        self.assertTrue(result.ok)
        self.assertEqual(len(provider.requests), 2)

    def test_tc_sec_003_deny_timeout_and_missing_provider_fail_closed(self) -> None:
        cases = (
            (RecordingApprovalProvider((ApprovalOutcome.DENY,)), ErrorCode.POLICY_DENIED),
            (RecordingApprovalProvider((ApprovalOutcome.TIMEOUT,)), ErrorCode.APPROVAL_TIMEOUT),
            (None, ErrorCode.APPROVAL_UNAVAILABLE),
        )

        for provider, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                calls = 0

                def handler(arguments: dict[str, Any]) -> str:
                    nonlocal calls
                    calls += 1
                    return "executed"

                policy = PermissionPolicy(
                    [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
                )
                registry = ToolRegistry((make_spec(Risk.WRITE, handler),))
                result = run_runtime(
                    registry,
                    [tool_call({"path": "docs/a.md"})],
                    policy=policy,
                    approval_provider=provider,
                )

                self.assertEqual(calls, 0)
                self.assertEqual(
                    tool_error_code(tool_contents(result)[0]),
                    expected_code.value,
                )

    def test_approval_provider_exception_is_unavailable_without_message_leak(self) -> None:
        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, lambda arguments: "executed"),))
        result = run_runtime(
            registry,
            [tool_call({"path": "docs/a.md"})],
            policy=policy,
            approval_provider=RaisingApprovalProvider(),
        )

        content = tool_contents(result)[0]
        self.assertEqual(tool_error_code(content), ErrorCode.APPROVAL_UNAVAILABLE.value)
        self.assertNotIn("private approval failure", content)

    def test_tc_sec_008_summary_evidence_and_audit_do_not_leak_values(self) -> None:
        secrets = (
            "sk-super-secret",
            "file-body-secret",
            "https://user:password@example.com/private",
            "rm -rf / --token hidden-token",
        )
        arguments = {
            "api_key": secrets[0],
            "content": secrets[1],
            "url": secrets[2],
            "command": ["sh", "-c", secrets[3]],
            "path": "private/customer-name.txt",
        }
        provider = RecordingApprovalProvider((ApprovalOutcome.DENY,))
        policy = PermissionPolicy(
            [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
        )
        registry = ToolRegistry((make_spec(Risk.WRITE, lambda values: "executed"),))
        result = run_runtime(
            registry,
            [tool_call(arguments)],
            policy=policy,
            approval_provider=provider,
        )

        self.assertEqual(len(provider.requests), 1)
        safe_surfaces = json.dumps(
            {
                "approval": provider.requests[0].summary,
                "safe_result": result.to_safe_dict(),
                "tool_error": tool_contents(result)[0],
                "policy_audit": policy.audit_events,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        for secret in secrets:
            self.assertNotIn(secret, safe_surfaces)
        self.assertNotIn("private/customer-name.txt", safe_surfaces)
        self.assertEqual(policy.audit_events[0]["path"], None)
        self.assertEqual(policy.audit_events[0]["command"], [])
        self.assertTrue(policy.audit_events[0]["path_present"])
        self.assertTrue(policy.audit_events[0]["command_present"])


if __name__ == "__main__":
    unittest.main()
