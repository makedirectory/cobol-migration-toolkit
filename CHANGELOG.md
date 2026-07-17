# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] — schema & filter

### Added
- **Published JSON Schema** for `inventory.json` (draft 2020-12) via a new `cobol-migrate schema`
  command (`--output` to write a file). A test validates real scan output against it.
- **Filterable unit table** in the HTML report — an inline search box filters rows client-side;
  the report stays fully self-contained (no external assets).
- `jsonschema` added as a dev/test dependency.

## [0.7.0] — inventory analyzers

### Added
- **Inventory analyzers** — a second plugin type via the `cobol_migrate.inventory_analyzers`
  entry-point group. An `InventoryAnalyzer` runs once over the built inventory (after per-unit
  analyses are merged) and its result lands in a new top-level `reports` section of `inventory.json`.
  Enables estate-level rollups without further core changes.
- `reports` surfaced in the Markdown and HTML reports; `--analyzers` now selects both plugin types.

### Changed
- `Inventory` gains a `reports` field (defaults to `{}`); `select_analyzers` is generic over both
  analyzer kinds.

## [0.6.0] — graphs & gating

### Added
- **Subsystem clustering** in DOT graphs — source-unit nodes are grouped into `subgraph cluster_*`
  by their top-level directory.
- **Embedded dependency graph** in the HTML report: an inline SVG rendered via Graphviz (`dot`) when
  available, otherwise the DOT source in a `<details>` — always self-contained (no external assets).
- **`--fail-on METRIC[:MAX]`** (repeatable) and a `fail_on` config key: exit non-zero when a metric
  exceeds a threshold (default 0; list metrics compare length). Generalizes `--strict`.

## [0.5.0] — configuration file

### Added
- `.cobolmigrate.toml` project config (new `config` module), auto-discovered in the source
  directory or cwd, or selected with `--config`. Supports `copybook_paths`, `format`, `strict`,
  `analyzers`, `extensions` (file-type allowlist override), and `output`.
- CLI flags override config-file values; unknown keys (e.g. `dialect`) pass through to analyzers
  via `ScanContext.options`.
- `scan_tree`/`index_copybooks` accept an optional extension allowlist.

### Changed
- `--output` now defaults to the config value (or `build`) instead of a hard-coded default.

## [0.4.1]

### Added
- `ScanContext.root` and `ScanContext.read_source(unit, normalized=?)` so analyzer plugins can
  access unit source text (needed by real analyzers, e.g. complexity/grammar-based ones).

## [0.4.0] — plugin architecture

### Added
- Analyzer plugin interface (`plugins` module): `Analyzer` protocol + `ScanContext`, discovered
  via the `cobol_migrate.analyzers` entry-point group. Installed packages' analyzers auto-register.
- Built-in reference analyzer `paragraph_count` as a template for third-party/commercial analyzers.
- `--analyzers {all,none,<name>}` (repeatable) to select which analyzers run.
- Analyzer output merged into `units[i].analyses.<name>`; new top-level `analyzers` list in
  `inventory.json` records which ran. A failing plugin warns and is skipped, never aborting a scan.

### Changed
- `build_inventory(...)` accepts optional analyzer results; `run_scan(...)` discovers and runs analyzers.

## [0.3.0] — better graphs & UX

### Added
- Self-contained styled **HTML report** (`report.html`) with summary stat tiles, unresolved
  banners, and a per-unit table; no external assets.
- `--format {json,md,dot,html,all}` (repeatable) to select which outputs are written.
- `--strict` flag: exit non-zero when any CALL or copybook dependency is unresolved (CI gating).
- Split dependency graphs: `calls.dot` and `copybooks.dot` alongside the combined `dependencies.dot`.

### Changed
- `cli` scan logic extracted into a testable `run_scan(...)` returning an exit code.
- Report writers now each ensure the output directory exists (formats can be emitted independently).

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

[Unreleased]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/makedirectory/cobol-migration-toolkit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/makedirectory/cobol-migration-toolkit/releases/tag/v0.1.0
