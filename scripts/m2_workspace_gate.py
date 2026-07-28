from __future__ import annotations

import argparse
import io
import json
import platform
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "tests"
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

TEST_MODULES = ("test_workspace_p1",)


def build_suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module))
    return suite


def _tracebacks(values: list[tuple[unittest.case.TestCase, str]]) -> list[dict[str, str]]:
    return [{"test": test.id(), "traceback": traceback} for test, traceback in values]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M2-E Workspace P1 gate")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(build_suite())
    output = stream.getvalue()
    print(output, end="")

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "gate": "m2-workspace-p1",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "test_modules": list(TEST_MODULES),
        "tests_run": result.testsRun,
        "failures": _tracebacks(result.failures),
        "errors": _tracebacks(result.errors),
        "skipped": [
            {"test": test.id(), "reason": reason}
            for test, reason in result.skipped
        ],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "successful": report["successful"],
                "tests_run": report["tests_run"],
                "failure_count": len(report["failures"]),
                "error_count": len(report["errors"]),
                "skipped_count": len(report["skipped"]),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
