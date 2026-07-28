# M0 Closeout Status

> Status date: 2026-07-28
> Target branch: `develop`
> Release branch: `master`
> Milestone status: **CLOSED**
> Release decision: **NO RELEASE**

## 1. Purpose

M0 establishes the trustworthy documentation, threat-model, traceability, governance, and minimum-CI baseline required before high-risk Runtime and recovery work. Closing M0 authorizes later milestone implementation; it does not verify the Alpha requirements or authorize a release.

## 2. Exit Gate status

| M0 Exit Gate | Status | Evidence / remaining boundary |
| --- | --- | --- |
| Every P0/P1 Requirement has Milestone, Test ID, and expected Evidence | PASS | `docs/traceability/alpha-traceability.md`; automated documentation traceability gate |
| No unowned P0/P1 Requirement | PASS | Traceability owner column and automated Requirement/Test mapping checks |
| README contains no public capability commitment outside PRD | PASS for M0 scope | Chinese/English README use factual status tables; repository remains `NO RELEASE` |
| Threat Model and Alpha security configurations reviewed | PASS for M0 documentation | `docs/security/threat-model.md`; ADR-004; `SECURITY.md` |
| License can be distributed under the current manifest | PASS for M0 initial review | Apache-2.0 `LICENSE`, `NOTICE`, and `docs/governance/dependency-license-review.md`; M5 resolved-artifact revalidation remains required |
| Minimum CI automatically executes on new `develop` PRs | PASS | PR #1; `Minimum CI` run 28, conclusion `success` |
| Current existing tests are green | PASS on the M0 Python 3.11/Ubuntu baseline | `docs/testing/m0-ci-validation.md`; full release matrix remains M5 work |
| Documentation links and Requirement/Test mappings pass | PASS | `scripts/check_docs_traceability.py` in the green M0 workflow |
| Development and release branch policy is explicit | PASS as maintainer policy | PR-first development on `develop`; exceptional direct push is permitted only after root-cause analysis and must record technical debt; `master` is the release branch |

## 3. Current branch policy

The repository follows this order of preference:

1. create a feature branch;
2. open a Pull Request with a clear title and description;
3. wait for applicable CI;
4. merge into `develop`;
5. promote only a Release-Gate-verified `develop` commit to `master`.

`develop` no longer requires every change to use a PR at the repository-rule level. Direct push is an exception, not the default. It is permitted only when the PR path is persistently blocked by an environment, dependency, CI, or rule conflict that cannot be resolved in the current execution window.

An exceptional direct-push commit must use a conventional commit subject and include:

```text
<type>(<scope>): <change summary>

## 问题原因
<root cause that prevented the PR path>

## 技术债务
- <remaining issue, or “无”>
```

The absence of enforced PR-only protection means `OSS-001` remains `Partial` until the release-engineering milestone defines and retains the required-check enforcement evidence. This does not reopen M0 because the process, CI entry point, and evidence boundary are now explicit.

## 4. Completed deliverables

- Product, security, test, and roadmap consistency corrected.
- Threat Model and complete P0/P1 traceability established.
- Initial architecture decisions accepted.
- Apache-2.0 attribution, contribution, support, conduct, compatibility, and dependency policies added.
- Minimum Python 3.11 CI implemented and executed.
- Critical Ruff diagnostics, Pyright, current unit tests, package import, tracked-secret scan, and documentation gate verified.
- README claims reduced to current factual state and explicit security limitations.

## 5. M1 execution outcome

M1 was implemented through PR #6–#10 in contract-first order:

1. core contracts and schemas;
2. Workspace containment;
3. opaque durable rollback handles;
4. side-effect-uncertain recovery;
5. permanent three-platform P0 gate and report.

The implementation stack is merged into `develop`. M1 is closed only after the integrated closeout PR reruns the permanent gate against the merged state and synchronizes Traceability, security, Known Unknowns, Code Review, README, and milestone evidence.

No M0 or M1 evidence changes the repository release decision: **NO RELEASE**.