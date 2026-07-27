# Dependency and License Review

> Review stage: M0 initial audit
> Review date: 2026-07-27
> Repository baseline: `develop@375c9ec`
> Decision: no known dependency-license blocker in the current manifest; release-time revalidation remains mandatory.

## 1. Scope and method

This review inspects the repository-controlled dependency declarations and distinguishes:

1. runtime dependencies shipped to users;
2. build-system dependencies;
3. CI/development tools;
4. bundled or copied third-party source/assets.

The M0 review is an initial distribution-risk screen, not a legal opinion. M5 must produce a resolved dependency inventory from the actual wheel/sdist build environment and repeat the license check against pinned artifacts.

## 2. Current declared dependencies

The current `pyproject.toml` declares:

- no `[project.dependencies]` runtime packages;
- `setuptools>=68` as the PEP 517 build-system requirement;
- no optional-dependency groups.

The M0 workflow installs `ruff` and `pyright` as CI-only quality tools. They are not declared Runtime dependencies and are not intended to be included in the wheel or sdist.

| Component | Role | Shipped as Runtime dependency | M0 disposition |
| --- | --- | ---: | --- |
| Python standard library | Runtime implementation | No separate bundled package | Accept; governed by the selected Python distribution |
| `setuptools>=68` | Build backend | Build environment only | Accept provisionally; resolve exact version and license metadata during artifact build |
| Ruff | CI lint tool | No | Accept as development tooling; pin and revalidate before reproducible release workflows |
| Pyright | CI type checker | No | Accept as development tooling; pin and revalidate before reproducible release workflows |

## 3. Repository content and attribution

- Repository license: Apache-2.0 (`LICENSE`).
- Attribution notice: `NOTICE` records the original `7colorai/deepseek_runtime` source lineage and subsequent fork modifications.
- No vendored dependency directory, generated third-party bundle, binary library, model weight, dataset, or frontend asset package is declared by the current build manifest.
- External project names and trademarks are descriptive references only; `NOTICE` does not grant trademark rights.

## 4. Current risks

### R1: Build and CI versions are not pinned

`setuptools>=68`, Ruff, and Pyright may resolve to different versions over time. This affects reproducibility, behavior, vulnerability posture, and the exact license inventory.

**Required action:** M5 release workflows must use reviewed pins or a reproducible lock/constraint mechanism and preserve the resolved inventory as evidence.

### R2: Manifest-only review cannot detect copied snippets or untracked build inputs

A legal/source provenance audit cannot rely only on `pyproject.toml`.

**Required action:** every PR must identify newly copied third-party code/assets; release construction must use Git-tracked allowlists and produce an artifact file manifest.

### R3: Optional future dependencies may expand obligations

JSON Schema validation, checkpoint encryption, SBOM generation, and platform adapters may add dependencies later.

**Required action:** dependency additions require license/provenance review in the introducing PR. Copyleft, source-available, non-commercial, field-of-use, or unclear licenses require explicit maintainer/legal approval before merge.

## 5. Acceptance policy

A dependency is acceptable only when:

- its identity and source are unambiguous;
- its license permits the intended use and Apache-2.0 distribution model;
- required notices, source offers, or attribution are identified and included;
- no conflicting restriction is hidden in package metadata, bundled assets, or secondary licenses;
- the resolved artifact is scanned for known vulnerabilities and unexpected files;
- the decision is recorded in the PR and release evidence.

Unknown or ambiguous licensing is a `No-Go` condition, not an item to defer after publication.

## 6. M0 conclusion

The current repository has no declared third-party Runtime dependency and now contains Apache-2.0 license and attribution files. No current manifest-level license blocker was identified.

This conclusion is limited to M0. It does not authorize release until exact build inputs, resolved versions, artifact contents, SBOM/dependency inventory, notices, vulnerability results, and provenance are verified in M5/M6.
