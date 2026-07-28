from __future__ import annotations

import argparse
import io
import json
import platform
import sys
import unittest
from pathlib import Path


PATTERNS = (
    "test_execution_adapters.py",
    "test_execution_adapter_limits.py",
    "test_execution_adapter_privacy.py",
    "test_execution_runtime.py",
    "test_workspace_execution_adapter.py",
)


def build_suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for pattern in PATTERNS:
        suite.addTests(loader.discover("tests", pattern=pattern))
    return suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M2-C ExecutionAdapter gate")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(build_suite())
    log = stream.getvalue()
    print(log, end="")

    evidence = {
        "gate": "m2-execution-adapter",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "patterns": list(PATTERNS),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
    }
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
