# Contributing to DeepSeek Runtime

DeepSeek Runtime is in Open-source Alpha hardening. Contributions are welcome when they reduce a documented release blocker, improve verification, or correct factual documentation.

## Source of truth

Read these before changing code:

1. `docs/product/PRD.md` — scope, priority, requirements, acceptance criteria;
2. `docs/security/threat-model.md` — security guarantees and non-guarantees;
3. `docs/architecture/` and `docs/adr/` — technical contracts and decisions;
4. `docs/testing/test-cases.md` — required verification scenarios;
5. `docs/traceability/alpha-traceability.md` — requirement ownership and evidence;
6. `docs/roadmap/open-source-readiness-plan.md` — milestone order and Exit Gates.

A pull request or direct-push exception must not introduce a public capability that is absent from the PRD.

## Branch and pull-request flow

The default and first-priority flow is:

1. start from the latest `develop` branch;
2. create a focused feature branch;
3. open a Pull Request with a clear title and description;
4. wait for applicable CI;
5. merge into `develop`;
6. update Traceability and milestone evidence in the same PR.

Additional rules:

- Do not develop directly on `master`.
- Release changes flow `develop → master → tag` only after every Release Gate passes.
- Hotfixes from `master` must be backported to `develop`.
- Do not use a direct push merely to avoid review or a failing code check.

## Exceptional direct push to `develop`

`develop` permits direct push as an operational fallback, not as the default workflow.

Use it only when the PR path is persistently blocked in the current execution environment, for example:

- CI infrastructure is unavailable;
- test dependencies cannot be installed for an external reason;
- repository rules conflict with the intended branch flow;
- the connected GitHub execution path cannot complete the PR operation after root-cause analysis and reasonable repair attempts.

Before a direct push:

1. identify whether the failure is caused by code, configuration, dependency, environment, or repository rules;
2. fix code/configuration defects when they are within scope;
3. retain any available local or CI evidence;
4. use direct push only when the PR path cannot be completed without blocking the plan.

The commit message must use this structure:

```text
<type>(<scope>): <change summary>

## 问题原因
<why the PR path could not complete and the confirmed root cause>

## 技术债务
- <remaining issue and follow-up status>
```

Use `- 无` only when no known debt remains. Do not omit either section.

Technical debt may additionally be recorded in `docs/TECH_DEBT.md` using:

```text
[YYYY-MM-DD] description | reason it remains | status
```

## Required pull-request content

Describe:

- problem and root cause;
- PRD Requirement ID and roadmap PR/slice ID;
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

For M1 P0-sensitive changes also run:

```bash
python scripts/m1_p0_gate.py --repetitions 20 --output m1-p0-local.json
```

The CI result is the shareable evidence. A local verbal claim is not release evidence.

## Definition of Done

A change is complete only when:

- implementation matches the PRD requirement;
- happy, failure, and adversarial/fault paths are tested where applicable;
- lint, type check, tests, import, secret scan, and traceability checks pass;
- machine-readable errors and schemas are updated when changed;
- Threat Model, SECURITY, ADR, architecture, Known Unknowns, Code Review status, and README are synchronized as needed;
- `docs/traceability/alpha-traceability.md` records actual PR, tests, evidence, status, and blockers;
- default logs and public evidence contain no API key, prompt, response, reasoning, or tool-content plaintext;
- no flaky failure is hidden by rerunning a required test;
- direct-push exceptions record their root cause and technical debt.

## Security reports

Do not publish exploit details or credentials in a public issue. Follow `SECURITY.md`.

## License

Unless explicitly stated otherwise, a contribution intentionally submitted to this project is licensed under Apache-2.0, consistent with the repository license.