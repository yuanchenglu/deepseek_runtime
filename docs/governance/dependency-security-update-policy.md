# Dependency and Security Update Policy

> Status: M0 baseline
> Applies to: runtime, build, CI, documentation, release, and example dependencies

## 1. Principles

- Minimize dependencies; add one only when it closes a documented requirement more safely or reliably than repository-owned code.
- Treat dependency identity, license, provenance, vulnerability status, and update behavior as part of the implementation.
- Never accept an update solely because a bot opened it or a version number is newer.
- Security updates must not silently weaken compatibility, recovery, privacy, or Release Gates.

## 2. Adding a dependency

The introducing pull request must record:

- PRD Requirement and technical need;
- package, source repository, maintainer, and resolved version range;
- direct/transitive role and whether it enters wheel/sdist;
- license and attribution obligations;
- security history and current advisory scan;
- maintenance activity and release cadence;
- size, platform, performance, and supply-chain impact;
- rejected standard-library or existing-dependency alternatives;
- removal/migration strategy.

Dependencies with unclear provenance or licensing are rejected until resolved.

## 3. Version policy

- Release builds use reviewed, reproducible dependency resolution.
- Broad unbounded ranges are not acceptable for release evidence.
- Runtime and build dependencies require compatible lower-bound tests where a range is supported.
- CI tool versions are pinned or constrained once their output becomes a required gate.
- Hash-locked artifacts are preferred where the package manager and workflow support them.

## 4. Automated updates

Automated dependency pull requests may be enabled, but each update still requires:

- changelog and security-advisory review;
- license/provenance recheck when metadata or ownership changes;
- full affected test and artifact gates;
- explicit review of new transitive dependencies;
- no unexplained generated or lockfile changes.

Major versions and security-sensitive libraries require a maintainer review even when CI is green.

## 5. Vulnerability response

When a relevant vulnerability is reported:

1. determine whether the vulnerable component and code path are present in shipped artifacts;
2. classify impact using `SECURITY.md` severity guidance;
3. test upgrade, mitigation, or removal options;
4. publish a fix through the documented branch/release process;
5. update advisories, release notes, manifests, SBOM/inventory, and support status;
6. backport when a supported tagged version remains affected.

An advisory affecting only a development tool is still assessed for CI secret exposure, artifact tampering, or untrusted-input execution.

## 6. Review cadence

- Every dependency-changing PR: full review of the changed dependency graph.
- Scheduled maintenance: at least monthly while a tagged Alpha is supported.
- Release Candidate: fresh license, vulnerability, provenance, and resolved-version inventory.
- Emergency: immediate review for actively exploited or S0/S1 relevant advisories.

## 7. No-Go conditions

Pause merge or release when:

- license or source provenance is ambiguous;
- a critical/high vulnerability is reachable and unmitigated;
- an update adds unexpected packages, build scripts, binaries, or network fetches;
- artifact contents cannot be tied to reviewed manifests and locks;
- required checks pass only by disabling warnings, tests, or security controls.
