# Contributing to DeepSeek Runtime

DeepSeek Runtime is in Open-source Alpha hardening. Contributions are welcome when they reduce a documented release blocker, improve verification, or correct factual documentation.

## Source of truth

Read these before changing code:

1. `docs/product/PRD.md` — scope, priority, requirements, acceptance criteria;
2. `docs/security/threat-model.md` — security guarantees and non-guarantees;
3. `docs/architecture/` and `docs/adr/` — technical contracts and decisions;
4. `docs/testing/test-cases.md` — required verification scenarios;
5. `docs/traceability/alpha-traceability.md` — requirement ownership and evidence.

A pull request must not introduce a public capability that is absent from the PRD.

## Branch and pull-request flow

- Create work from the latest `develop` branch.
- Use a focused branch and a reviewable pull request.
- Do not develop directly on `master`.
- Release changes flow `develop → master → tag` only after every Release Gate passes.
- Hotfixes from `master` must be backported to `develop`.

## Required pull-request content

Describe:

- problem and root cause;
- PRD Requirement ID and roadmap PR ID;
- design and rejected alternatives;
- security, recovery, compatibility, and rollback impact;
- automated tests and evidence;
- documentation and traceability updates.

Large state/schema changes require the relevant ADR or contract update before implementation.

## Local checks

Use Python 3.11 or newer:

```bash
python -m pip install -e .
python -m pip install ruff pyright
python -m ruff check src tests scripts --select E9,F63,F7,F82
pyright src/deepseek_runtime --pythonversion 3.11 --level error
python -m unittest discover -s tests -v
python scripts/check_tracked_secrets.py
python scripts/check_docs_traceability.py
```

The CI result is the shareable evidence. A local verbal claim is not release evidence.

## Definition of Done

A change is complete only when:

- implementation matches the PRD requirement;
- happy, failure, and adversarial/fault paths are tested where applicable;
- lint, type check, tests, import, secret scan, and traceability checks pass;
- machine-readable errors and schemas are updated when changed;
- Threat Model, ADR, architecture, Known Unknowns, and README are synchronized as needed;
- `docs/traceability/alpha-traceability.md` records PR, tests, evidence, status, and blockers;
- default logs and evidence contain no API key, prompt, response, reasoning, or tool-content plaintext;
- no flaky failure is hidden by rerunning a required test.

## Security reports

Do not publish exploit details or credentials in a public issue. Follow `SECURITY.md`.

## License

Unless explicitly stated otherwise, a contribution intentionally submitted to this project is licensed under Apache-2.0, consistent with the repository license.
