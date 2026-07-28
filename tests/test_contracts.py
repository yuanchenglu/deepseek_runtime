from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

from deepseek_runtime.contracts import (
    ChangeJournalEntry,
    ContractViolation,
    ErrorCode,
    JournalFileRecord,
    PublishableEvidence,
    RecoverableCheckpoint,
    RecoveryPolicy,
    RollbackHandle,
    RuntimeErrorInfo,
    RuntimeState,
    ToolArgumentError,
    ToolCallCheckpoint,
    ToolSpec,
    transition_manifest,
    validate_transition,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "docs" / "schemas"


class ContractTests(unittest.TestCase):
    def test_error_contract_redacts_details(self) -> None:
        error = RuntimeErrorInfo(
            ErrorCode.TOOL_ARGUMENT_INVALID,
            "invalid arguments",
            details={"path": ["account"], "content": "secret", "api_key": "sk-test"},
            cause_class="ValidationError",
        )
        value = error.to_dict()
        self.assertEqual(value["code"], "TOOL_ARGUMENT_INVALID")
        self.assertNotIn("content", value["details"])
        self.assertNotIn("api_key", value["details"])
        self.assertTrue(value["details"]["content_redacted"])

    def test_transition_contract_enforces_approval_and_receipt(self) -> None:
        with self.assertRaises(ContractViolation):
            validate_transition(RuntimeState.APPROVAL_PENDING, RuntimeState.TOOL_RUNNING)
        validate_transition(
            RuntimeState.APPROVAL_PENDING,
            RuntimeState.TOOL_RUNNING,
            approval_present=True,
        )
        with self.assertRaises(ContractViolation):
            validate_transition(
                RuntimeState.TOOL_RUNNING,
                RuntimeState.TOOL_SUCCEEDED,
                side_effect=True,
            )
        validate_transition(
            RuntimeState.TOOL_RUNNING,
            RuntimeState.TOOL_SUCCEEDED,
            side_effect=True,
            receipt_present=True,
        )
        with self.assertRaises(ContractViolation):
            validate_transition(RuntimeState.CREATED, RuntimeState.COMPLETED)

    def test_transition_manifest_matches_normative_file(self) -> None:
        manifest = transition_manifest()
        self.assertTrue(manifest)
        self.assertEqual(
            manifest,
            sorted(manifest, key=lambda item: (item["source"], item["target"])),
        )
        file_value = json.loads(
            (ROOT / "docs" / "contracts" / "runtime-state-transitions.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(file_value["schema_version"], "1.0")
        self.assertEqual(file_value["transitions"], manifest)

    def test_recovery_policy_for_running_side_effects(self) -> None:
        self.assertEqual(
            RecoveryPolicy.PURE.recovery_state_for_running(),
            RuntimeState.TOOL_REQUESTED,
        )
        self.assertEqual(
            RecoveryPolicy.RETRYABLE_WITH_KEY.recovery_state_for_running(),
            RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
        )
        self.assertEqual(
            RecoveryPolicy.RETRYABLE_WITH_KEY.recovery_state_for_running(
                has_idempotency_key=True
            ),
            RuntimeState.TOOL_REQUESTED,
        )
        self.assertEqual(
            RecoveryPolicy.NON_IDEMPOTENT.recovery_state_for_running(),
            RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
        )

    def test_tool_spec_validates_schema_and_arguments(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        }
        tool = ToolSpec(
            name="read_file",
            description="Read a workspace file",
            parameters=schema,
            handler=lambda value: value["path"],
        )
        self.assertEqual(tool.validate_arguments({"path": "README.md"})["path"], "README.md")
        with self.assertRaises(ToolArgumentError) as raised:
            tool.validate_arguments({"path": 3, "content": "secret"})
        self.assertEqual(raised.exception.error.code, ErrorCode.TOOL_ARGUMENT_INVALID)
        self.assertNotIn("secret", json.dumps(raised.exception.error.to_dict()))
        schema["properties"]["path"]["type"] = "integer"
        self.assertEqual(tool.parameters["properties"]["path"]["type"], "string")
        provider = tool.provider_definition()
        provider["function"]["parameters"]["properties"]["path"]["type"] = "integer"
        self.assertEqual(tool.parameters["properties"]["path"]["type"], "string")

    def test_side_effect_tool_requires_non_pure_recovery(self) -> None:
        schema = {"type": "object", "properties": {}}
        with self.assertRaises(ValueError):
            ToolSpec(
                name="write",
                description="write",
                parameters=schema,
                handler=lambda value: value,
                side_effect=True,
                recovery_policy=RecoveryPolicy.PURE,
            )
        ToolSpec(
            name="write",
            description="write",
            parameters=schema,
            handler=lambda value: value,
            risk="write",
            side_effect=True,
            recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
        )

    def test_checkpoint_roundtrip_keeps_private_data_and_excludes_evidence(self) -> None:
        call = ToolCallCheckpoint(
            call_id="call-1",
            name="write_file",
            arguments={"path": "a.txt", "content": "private"},
            state=RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
            recovery_policy=RecoveryPolicy.NON_IDEMPOTENT,
            side_effect=True,
            attempt_count=1,
            approval={"decision": "allow"},
            receipt={"request_id": "external-1"},
        )
        checkpoint = RecoverableCheckpoint(
            session_id="session-1",
            runtime_state=RuntimeState.TOOL_SIDE_EFFECT_UNCERTAIN,
            step=3,
            messages=[{"role": "user", "content": "private prompt"}],
            provider_continuation={"reasoning_content": "private continuation"},
            tool_calls=[call],
            budgets={"max_steps": 8, "used_steps": 3},
        )
        value = checkpoint.to_dict()
        self.assertIn("messages", value)
        self.assertNotIn("evidence", value)
        restored = RecoverableCheckpoint.from_dict(value)
        self.assertEqual(restored.to_dict(), value)

    def test_checkpoint_future_version_is_structured_error(self) -> None:
        with self.assertRaises(ContractViolation) as raised:
            RecoverableCheckpoint.from_dict(
                {
                    "schema_version": "99.0",
                    "session_id": "session-1",
                    "runtime_state": "CREATED",
                }
            )
        self.assertEqual(
            raised.exception.error.code,
            ErrorCode.CHECKPOINT_VERSION_UNSUPPORTED,
        )

    def test_publishable_evidence_rejects_recoverable_fields(self) -> None:
        PublishableEvidence(
            run_id="run-1",
            runtime_state=RuntimeState.COMPLETED,
            request_structure=({"content_sha256": "a" * 64, "content_bytes": 4},),
            response_structure=({"has_content": True, "content_bytes": 2},),
        )
        with self.assertRaises(ValueError):
            PublishableEvidence(
                run_id="run-2",
                runtime_state=RuntimeState.COMPLETED,
                metadata={"messages": [{"content": "private"}]},
            )

    def test_rollback_handle_is_opaque_and_journal_is_private(self) -> None:
        handle = RollbackHandle.issue()
        public = handle.to_dict()
        self.assertEqual(set(public), {"schema_version", "handle_id"})
        self.assertNotIn("path", json.dumps(public))
        record = JournalFileRecord(
            relative_path="src/a.txt",
            original_sha256="a" * 64,
            post_sha256="b" * 64,
            original_content_b64="cHJpdmF0ZQ==",
            original_mode=0o644,
        )
        entry = ChangeJournalEntry(
            handle_id=handle.handle_id,
            workspace_id="workspace-1",
            change_set_id="change-1",
            files=[record],
            created_at_unix=100,
            expires_at_unix=200,
        )
        self.assertEqual(
            ChangeJournalEntry.from_dict(entry.to_dict()).to_dict(),
            entry.to_dict(),
        )
        with self.assertRaises(ValueError):
            JournalFileRecord(
                relative_path="../outside.txt",
                original_sha256=None,
                post_sha256="b" * 64,
                original_content_b64=None,
            )

    def test_json_schemas_validate_contract_outputs(self) -> None:
        schemas = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in SCHEMA_ROOT.glob("*.schema.json")
        }
        self.assertEqual(len(schemas), 4)
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)

        error = RuntimeErrorInfo(ErrorCode.INTERNAL_ERROR, "failed").to_dict()
        Draft202012Validator(schemas["error-v1.schema.json"]).validate(error)

        checkpoint = RecoverableCheckpoint(session_id="s1").to_dict()
        checkpoint_resolver = RefResolver.from_schema(
            schemas["recoverable-checkpoint-v1.schema.json"],
            store={schema["$id"]: schema for schema in schemas.values()},
        )
        Draft202012Validator(
            schemas["recoverable-checkpoint-v1.schema.json"],
            resolver=checkpoint_resolver,
        ).validate(checkpoint)

        evidence = PublishableEvidence(
            run_id="r1", runtime_state=RuntimeState.CREATED
        ).to_dict()
        evidence_resolver = RefResolver.from_schema(
            schemas["publishable-evidence-v1.schema.json"],
            store={schema["$id"]: schema for schema in schemas.values()},
        )
        Draft202012Validator(
            schemas["publishable-evidence-v1.schema.json"],
            resolver=evidence_resolver,
        ).validate(evidence)

        handle = RollbackHandle.issue()
        journal = ChangeJournalEntry(
            handle_id=handle.handle_id,
            workspace_id="workspace-1",
            change_set_id="change-1",
            files=[],
            created_at_unix=1,
            expires_at_unix=2,
        ).to_dict()
        Draft202012Validator(schemas["change-journal-entry-v1.schema.json"]).validate(
            journal
        )


if __name__ == "__main__":
    unittest.main()
