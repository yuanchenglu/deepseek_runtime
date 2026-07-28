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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _tracebacks(values: list[tuple[unittest.case.TestCase, str]]) -> list[dict[str, str]]:
    return [{"test": test.id(), "traceback": traceback} for test, traceback in values]


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a structured full-unit test report")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(stream.getvalue(), end="")

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "gate": "full-unit-diagnostic",
        "platform": platform.platform(),
        "python": platform.python_version(),
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
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "tests_run": result.testsRun,
                "failure_count": len(result.failures),
                "error_count": len(result.errors),
                "skipped_count": len(result.skipped),
                "successful": result.wasSuccessful(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
