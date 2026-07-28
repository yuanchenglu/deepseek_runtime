from __future__ import annotations

import argparse
import io
import json
import os
import platform
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "tests"
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))


@dataclass(frozen=True)
class GateCase:
    test_id: str
    tests: tuple[str, ...]
    allow_all_skipped: bool = False


def gate_cases() -> tuple[GateCase, ...]:
    ws_003 = (
        "test_workspace_security.WorkspaceSecurityTests.test_windows_junction_is_not_traversed"
        if os.name == "nt"
        else "test_workspace_security.WorkspaceSecurityTests.test_external_directory_symlink_is_never_traversed"
    )
    return (
        GateCase(
            "TC-WS-001",
            (
                "test_workspace_security.WorkspaceSecurityTests."
                "test_traversal_and_absolute_external_paths_are_rejected_repeatedly",
            ),
        ),
        GateCase(
            "TC-WS-002",
            (
                "test_workspace_security.WorkspaceSecurityTests."
                "test_external_file_symlink_is_never_read_or_searched",
            ),
            allow_all_skipped=os.name == "nt",
        ),
        GateCase("TC-WS-003", (ws_003,)),
        GateCase(
            "TC-CHG-001",
            (
                "test_change_journal_security.ChangeJournalSecurityTests."
                "test_forged_handle_and_payload_are_rejected_repeatedly",
            ),
        ),
        GateCase(
            "TC-CHG-002",
            (
                "test_change_journal_security.ChangeJournalSecurityTests."
                "test_malicious_journal_path_cannot_target_outside_workspace",
            ),
        ),
        GateCase(
            "TC-CHG-011",
            (
                "test_change_journal_security.ChangeJournalSecurityTests."
                "test_apply_returns_opaque_handle_and_restart_manager_can_rollback",
                "test_change_journal_security.ChangeJournalSecurityTests."
                "test_cross_workspace_handle_is_rejected",
                "test_change_journal_security.ChangeJournalSecurityTests."
                "test_expired_handle_is_rejected",
            ),
        ),
        GateCase(
            "TC-SES-007",
            (
                "test_side_effect_recovery.SideEffectRecoveryTests."
                "test_crash_after_effect_before_result_checkpoint_never_auto_retries",
            ),
        ),
    )


def run_case(case: GateCase, repetition: int) -> dict[str, Any]:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in case.tests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    status = "passed"
    if result.failures or result.errors:
        status = "failed"
    elif result.testsRun and len(result.skipped) == result.testsRun:
        status = "not-applicable" if case.allow_all_skipped else "failed"

    return {
        "test_id": case.test_id,
        "repetition": repetition,
        "tests": list(case.tests),
        "status": status,
        "tests_run": result.testsRun,
        "skipped": [reason for _, reason in result.skipped],
        "failures": [text for _, text in result.failures],
        "errors": [text for _, text in result.errors],
        "output": stream.getvalue(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M1 P0 test manifest without rerun masking.")
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")

    attempts: list[dict[str, Any]] = []
    for repetition in range(1, args.repetitions + 1):
        for case in gate_cases():
            attempts.append(run_case(case, repetition))

    failures = [attempt for attempt in attempts if attempt["status"] == "failed"]
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "repetitions": args.repetitions,
        "manifest": [
            {
                "test_id": case.test_id,
                "tests": list(case.tests),
                "allow_all_skipped": case.allow_all_skipped,
            }
            for case in gate_cases()
        ],
        "attempt_count": len(attempts),
        "passed_count": sum(attempt["status"] == "passed" for attempt in attempts),
        "not_applicable_count": sum(attempt["status"] == "not-applicable" for attempt in attempts),
        "failed_count": len(failures),
        "attempts": attempts,
        "conclusion": "success" if not failures else "failure",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "conclusion": report["conclusion"],
                "attempt_count": report["attempt_count"],
                "passed_count": report["passed_count"],
                "not_applicable_count": report["not_applicable_count"],
                "failed_count": report["failed_count"],
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
