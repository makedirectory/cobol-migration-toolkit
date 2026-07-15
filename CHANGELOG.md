# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — trustworthy inventory

### Added
- Fixed vs free source-format detection (`>>SOURCE FORMAT` directive + heuristic) and
  fixed-format continuation-line handling.
- `--copybook-path` (repeatable) to resolve `COPY` members from external search paths.
- `COPY ... REPLACING` detection, flagged per-unit and in the report for manual review.
- Aggregate metrics: program/copybook counts, CALL/COPY edges, fan-in/fan-out,
  unreferenced programs & copybooks, and unresolved calls/copybooks.
- Versioned `inventory.json` (`schema_version: 1`) with `units`, `metrics`, and
  `unresolved` sections; Markdown summary and DOT graph now highlight unresolved targets.
- New `analysis` module; `CobolUnit` gains `source_format` and `copy_replacing` fields.
- Open-source scaffolding: `LICENSE` (Apache-2.0), `NOTICE`, `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, issue/PR templates, `CODEOWNERS`, Dependabot,
  pre-commit, `docs/ROADMAP.md`, `docs/SPEC.md`, `docs/DATA-HANDLING.md`.

### Changed
- `report` writers now take the aggregated inventory document instead of a raw unit list.

## [0.1.0]

### Added
- Regex-based scanner for `PROGRAM-ID`, `COPY`, static `CALL`, and paragraphs.
- `inventory.json`, `report.md`, and `dependencies.dot` output.
- `cobol-migrate scan` CLI, tests, and CI.

[Unreleased]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/makedirectory/cobol-migration-toolkit/releases/tag/v0.1.0
