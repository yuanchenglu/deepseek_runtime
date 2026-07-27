#!/usr/bin/env python3
"""Validate Alpha requirement/test traceability and core Markdown links."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRD = ROOT / "docs/product/PRD.md"
TEST_CASES = ROOT / "docs/testing/test-cases.md"
TRACEABILITY = ROOT / "docs/traceability/alpha-traceability.md"
LINK_SOURCES = (ROOT / "README.md", ROOT / "docs/INDEX.md")

REQUIREMENT_ROW = re.compile(r"^\|\s*([A-Z]+-\d{3})\s*\|\s*(P[012])\s*\|")
TEST_ROW = re.compile(r"^\|\s*(TC-[A-Z]+-\d{3})\s*\|\s*(P[012])\s*\|\s*([^|]+)\|")
DIRECT_REQUIREMENT = re.compile(r"\b([A-Z]+)-(\d{3})\b")
SHORTHAND_REQUIREMENT = re.compile(r"\b([A-Z]+)-(\d{3})/(\d{1,3})\b")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def parse_requirements() -> dict[str, str]:
    requirements: dict[str, str] = {}
    for line in read(PRD).splitlines():
        match = REQUIREMENT_ROW.match(line)
        if match:
            requirement_id, priority = match.groups()
            if requirement_id in requirements:
                raise RuntimeError(f"duplicate requirement: {requirement_id}")
            requirements[requirement_id] = priority
    if not requirements:
        raise RuntimeError("no requirements parsed from PRD")
    return requirements


def extract_requirement_ids(cell: str) -> set[str]:
    ids = {f"{prefix}-{number}" for prefix, number in DIRECT_REQUIREMENT.findall(cell)}
    for prefix, first, second in SHORTHAND_REQUIREMENT.findall(cell):
        ids.add(f"{prefix}-{first}")
        ids.add(f"{prefix}-{int(second):03d}")
    return ids


def parse_tests() -> tuple[dict[str, str], dict[str, list[tuple[str, str]]]]:
    tests: dict[str, str] = {}
    coverage: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for line in read(TEST_CASES).splitlines():
        match = TEST_ROW.match(line)
        if not match:
            continue
        test_id, priority, requirement_cell = match.groups()
        if test_id in tests:
            raise RuntimeError(f"duplicate test case: {test_id}")
        tests[test_id] = priority
        for requirement_id in extract_requirement_ids(requirement_cell):
            coverage[requirement_id].append((test_id, priority))
    if not tests:
        raise RuntimeError("no test cases parsed")
    return tests, coverage


def check_requirement_coverage(requirements: dict[str, str], coverage: dict[str, list[tuple[str, str]]]) -> list[str]:
    errors: list[str] = []
    for requirement_id, priority in sorted(requirements.items()):
        if priority == "P2":
            continue
        mapped = coverage.get(requirement_id, [])
        if not mapped:
            errors.append(f"{requirement_id} ({priority}) has no mapped test")
            continue
        acceptable = [
            (test_id, test_priority)
            for test_id, test_priority in mapped
            if PRIORITY_RANK[test_priority] <= PRIORITY_RANK[priority]
        ]
        if not acceptable:
            formatted = ", ".join(f"{test_id}:{test_priority}" for test_id, test_priority in mapped)
            errors.append(f"{requirement_id} ({priority}) only maps to lower-priority tests: {formatted}")
    return errors


def check_traceability(requirements: dict[str, str]) -> list[str]:
    text = read(TRACEABILITY)
    present = {f"{prefix}-{number}" for prefix, number in DIRECT_REQUIREMENT.findall(text)}
    return [
        f"{requirement_id} missing from alpha traceability"
        for requirement_id, priority in sorted(requirements.items())
        if priority in {"P0", "P1"} and requirement_id not in present
    ]


def check_links(source: Path) -> list[str]:
    errors: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(read(source)):
        target = raw_target.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (source.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{source.relative_to(ROOT)} link escapes repository: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"{source.relative_to(ROOT)} broken link: {raw_target}")
    return errors


def main() -> int:
    try:
        requirements = parse_requirements()
        tests, coverage = parse_tests()
        errors = check_requirement_coverage(requirements, coverage)
        errors.extend(check_traceability(requirements))
        for source in LINK_SOURCES:
            errors.extend(check_links(source))
    except RuntimeError as exc:
        print(f"Traceability gate failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Traceability gate failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    blocking_requirements = sum(priority in {"P0", "P1"} for priority in requirements.values())
    blocking_tests = sum(priority in {"P0", "P1"} for priority in tests.values())
    print(
        "Traceability gate passed: "
        f"{blocking_requirements} blocking requirements, "
        f"{blocking_tests} blocking tests, core links valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
