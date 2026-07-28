from __future__ import annotations

import unittest

from deepseek_runtime import (
    ApprovalOutcome,
    ApprovalRequest,
    AuthorizationSession,
    ContractViolation,
    Decision,
    ErrorCode,
    PermissionPolicy,
    PermissionRule,
    RecoveryPolicy,
    Risk,
    ToolSpec,
)


class DenyingApprovalProvider:
    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        return ApprovalOutcome.DENY


def write_spec() -> ToolSpec:
    return ToolSpec(
        "write_sample",
        "Write sample data.",
        {"type": "object", "additionalProperties": False},
        lambda arguments: "executed",
        risk=Risk.WRITE,
        side_effect=True,
        recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
    )


class AuthorizationAuditSemanticsTests(unittest.TestCase):
    def test_policy_denial_has_no_approval_outcome(self) -> None:
        session = AuthorizationSession(policy=PermissionPolicy())

        with self.assertRaises(ContractViolation) as raised:
            session.authorize(write_spec(), {})

        self.assertIs(raised.exception.error.code, ErrorCode.PERMISSION_DENIED)
        self.assertEqual(len(session.events), 1)
        event = session.events[0]
        self.assertIs(event.policy_decision, Decision.DENY)
        self.assertIsNone(event.approval_outcome)

    def test_human_denial_records_deny_outcome(self) -> None:
        session = AuthorizationSession(
            policy=PermissionPolicy(
                [PermissionRule(Risk.WRITE, Decision.ASK, path_glob="*")]
            ),
            approval_provider=DenyingApprovalProvider(),
        )

        with self.assertRaises(ContractViolation) as raised:
            session.authorize(write_spec(), {})

        self.assertIs(raised.exception.error.code, ErrorCode.PERMISSION_DENIED)
        self.assertEqual(len(session.events), 1)
        event = session.events[0]
        self.assertIs(event.policy_decision, Decision.ASK)
        self.assertEqual(event.approval_outcome, ApprovalOutcome.DENY.value)


if __name__ == "__main__":
    unittest.main()
