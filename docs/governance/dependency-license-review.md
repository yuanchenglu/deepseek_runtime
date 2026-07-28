# Dependency and License Review

> Review stage: M1 contract dependency update
> Review date: 2026-07-28
> Decision: no known manifest-level license blocker; exact release artifacts must be revalidated in M5/M6.

## 1. Scope and method

This is a repository engineering review, not a legal opinion. It inspects declared dependencies and the metadata resolved in the M1 validation environment. Release-time review must use the exact locked wheel/sdist inputs and preserve a machine-readable inventory.

## 2. Declared dependencies

Current `pyproject.toml` declares:

| Component | Role | Declared range | Shipped Runtime dependency |
| --- | --- | --- | ---: |
| `jsonschema` | Tool argument/schema validation | `>=4.23,<5` | Yes |
| `setuptools` | PEP 517 build backend | `>=68` | Build environment only |
| Ruff | Critical lint gate | CI installation | No |
| Pyright | Type gate | CI installation | No |

`jsonschema` is required by ADR-005 so the same Draft 2020-12 schema can generate Provider definitions and enforce local arguments.

## 3. M1 resolved metadata review

The local validation environment resolved `jsonschema 4.26.0`. Installed package metadata identified the following licenses:

| Package | Relationship | Metadata license |
| --- | --- | --- |
| `jsonschema` | Direct | MIT |
| `attrs` | Transitive | MIT |
| `referencing` | Transitive | MIT |
| `rpds-py` | Transitive | MIT |
| `jsonschema-specifications` | Transitive | MIT |

No manifest-level conflict with Apache-2.0 distribution was identified. This conclusion applies only to the inspected environment and does not replace exact artifact/license-file verification.

## 4. Repository content and attribution

- Repository license: Apache-2.0 (`LICENSE`).
- `NOTICE` records original source lineage and fork modifications.
- No vendored copy of `jsonschema` or its transitive packages is committed.
- Third-party dependencies must be installed from reviewed package artifacts, not copied into the source tree.

## 5. Current risks and required controls

### R1: Dependency ranges are not reproducible release inputs

`jsonschema>=4.23,<5` and `setuptools>=68` can resolve differently over time.

**M5 action:** create reviewed constraints/lock evidence, record exact filenames, versions, hashes and source indexes, then rebuild in a clean environment.

### R2: Transitive graph can change within the accepted range

A compatible direct version may add or replace transitive dependencies.

**M5 action:** generate an exact dependency inventory/SBOM, recheck licenses and vulnerabilities, and fail on unexpected graph changes.

### R3: Metadata alone is insufficient

Package metadata can omit bundled components or secondary notices.

**M5 action:** inspect wheel/sdist license files and artifact contents; include required attribution in release materials.

### R4: Schema formats can execute dependency-provided checks

`FormatChecker` behavior depends on installed extras and registered checkers.

**Implementation rule:** only explicitly enabled formats are security-relevant; schema acceptance cannot silently gain new enforcement from environment-dependent optional extras.

## 6. Acceptance policy

A dependency is acceptable only when:

- identity, source and resolved artifact are unambiguous;
- license permits the intended distribution model;
- required notices are identified;
- new build scripts, binaries and network fetches are reviewed;
- vulnerability and provenance checks pass;
- the introducing PR records alternatives and removal strategy.

Unknown or ambiguous licensing is a `No-Go` condition.

## 7. Current conclusion

The M1 `jsonschema` dependency has an identified technical requirement and no known manifest-level license blocker in the inspected environment.

The repository remains **NO RELEASE** until exact resolved artifacts, hashes, license files, vulnerability results, dependency inventory/SBOM and provenance are verified in M5/M6.
