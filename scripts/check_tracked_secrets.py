#!/usr/bin/env python3
"""Fail CI when tracked text files contain high-confidence secret material.

This is the M0 baseline scanner. It intentionally favors a small set of
high-confidence signatures to avoid training contributors to ignore noisy
security failures. M5 may replace or supplement it with a dedicated scanner.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]


PATTERNS = (
    SecretPattern("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    SecretPattern("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    SecretPattern("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    SecretPattern("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    SecretPattern("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    SecretPattern("provider-api-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    SecretPattern(
        "credential-assignment",
        re.compile(
            r"(?i)\b(?:deepseek_api_key|api[_-]?key|access[_-]?token|client[_-]?secret|password)\b"
            r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{24,})"
        ),
    ),
)

SAFE_MARKERS = (
    "sk-test-do-not-use",
    "sk-your-key-here",
    "example",
    "placeholder",
    "changeme",
    "${{ secrets.",
    "<redacted>",
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        print(f"error: cannot read tracked file {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
        raise
    if len(data) > MAX_TEXT_BYTES or b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    findings: list[tuple[Path, int, str]] = []
    for path in tracked_files():
        text = read_text(path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if any(marker.lower() in lowered for marker in SAFE_MARKERS):
                continue
            for pattern in PATTERNS:
                if pattern.regex.search(line):
                    findings.append((path.relative_to(ROOT), line_number, pattern.name))

    if findings:
        print("Tracked secret scan failed:", file=sys.stderr)
        for path, line_number, name in findings:
            print(f"  {path}:{line_number}: {name}", file=sys.stderr)
        print("Remove the credential from Git history and rotate it before retrying.", file=sys.stderr)
        return 1

    print(f"Tracked secret scan passed: {len(tracked_files())} tracked files inspected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
