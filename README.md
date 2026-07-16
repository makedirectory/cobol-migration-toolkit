# COBOL Migration Toolkit

[![CI](https://github.com/makedirectory/cobol-migration-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/makedirectory/cobol-migration-toolkit/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status: beta](https://img.shields.io/badge/status-beta-orange)

> **Beta — in active development.** Interfaces may still change before 1.0. We're actively
> looking for feedback: please [open an issue](https://github.com/makedirectory/cobol-migration-toolkit/issues)
> with what worked, what didn't, and what your COBOL estate needs.

A dependency-analysis and documentation scaffold for COBOL modernization projects.

> **Open-core:** this repository is the free, Apache-2.0 discovery core. Deep grammar-based
> parsing, embedded SQL/CICS handling, AI documentation, SARIF/work-item export, and an assessment
> dashboard are part of **Cartograph**, the commercial tier — see [`docs/ROADMAP.md`](docs/ROADMAP.md).
>
> **Your COBOL never leaves your network.** The toolkit runs entirely locally with no telemetry, and
> Cartograph deploys *inside* your environment rather than ingesting your source — see
> [`docs/DATA-HANDLING.md`](docs/DATA-HANDLING.md).

It scans COBOL and copybook files, extracts a useful first-pass inventory, and emits:

- JSON metadata
- Markdown documentation
- Graphviz DOT dependency graphs

The parser is intentionally conservative and regex-based. It is useful as a discovery tool and as a foundation for a proper grammar-based parser later.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cobol-migrate scan examples --output build

# resolve COPY members from extra directories (repeatable):
cobol-migrate scan src --copybook-path copybooks --copybook-path shared/cpy --output build

# choose output formats (default: all) and fail CI on unresolved deps:
cobol-migrate scan src --format html --format json --output build
cobol-migrate scan src --strict --output build   # exit 1 if anything is unresolved
```

Generated files (subset selectable with `--format {json,md,dot,html,all}`):

```text
build/inventory.json    # versioned schema: units + metrics + unresolved deps
build/report.md         # summary metrics, unresolved list, per-unit detail
build/report.html       # self-contained styled report (stat tiles + unit table)
build/dependencies.dot  # combined call/copy graph; unresolved targets red
build/calls.dot         # call graph only
build/copybooks.dot     # copybook graph only
```

Render the graph if Graphviz is installed:

```bash
dot -Tsvg build/dependencies.dot -o build/dependencies.svg
```

Run tests:

```bash
pytest
```

## Configuration (`.cobolmigrate.toml`)

Keep project settings in a file instead of long command lines. The toolkit auto-discovers a
`.cobolmigrate.toml` in the scanned source directory (or the current directory), or point at one
with `--config`. **CLI flags override the file; the file supplies defaults.**

```toml
# .cobolmigrate.toml
copybook_paths = ["copybooks", "shared/cpy"]   # resolved relative to this file
format = ["json", "html"]
strict = true
analyzers = ["all"]
extensions = [".cbl", ".cob", ".cpy"]           # override the file-type allowlist
output = "build"
dialect = "ibm"                                 # unknown keys pass through to analyzers
```

## Analyzer plugins

Deeper analysis plugs into the core as **analyzers** discovered via the
`cobol_migrate.analyzers` entry-point group. The core ships one built-in reference analyzer
(`paragraph_count`); installed packages (e.g. the commercial **Cartograph** tier) register their
own and run automatically — no core changes required.

```bash
cobol-migrate scan src --analyzers all           # default: every discovered analyzer
cobol-migrate scan src --analyzers none          # inventory only
cobol-migrate scan src --analyzers paragraph_count
```

Analyzer output is merged into each unit under `units[i].analyses.<name>` in `inventory.json`.
Write your own by implementing the `Analyzer` protocol and registering it:

```toml
[project.entry-points."cobol_migrate.analyzers"]
my_analyzer = "my_pkg.module:MyAnalyzer"
```

See [`docs/SPEC.md`](docs/SPEC.md) for the `Analyzer`/`ScanContext` contract.

## What the scanner finds

- `PROGRAM-ID`
- `COPY` dependencies (incl. `COPY ... REPLACING`, flagged for manual review)
- static `CALL` targets
- paragraph names
- source format (fixed vs free) and fixed-format continuation handling
- source file sizes and line counts
- copybook resolution against `--copybook-path` search paths
- metrics: fan-in/fan-out, unreferenced programs/copybooks, unresolved dependencies

## Suggested roadmap

1. Replace regex extraction with an ANTLR or tree-sitter grammar.
2. Add fixed-format COBOL column handling and continuation rules.
3. Resolve copybooks from configurable search paths.
4. Parse data definitions and build record-layout documentation.
5. Track variable reads/writes and produce data-flow graphs.
6. Detect dynamic calls and transaction boundaries.
7. Add an optional LLM documentation adapter behind a clean interface.
8. Export SARIF, OpenAPI candidate specs, or modernization work items.

## Safety and accuracy

Treat generated output as an inventory aid, not authoritative program semantics. Real COBOL estates include vendor extensions, preprocessors, embedded SQL, CICS statements, generated code, and local conventions.

## Roadmap & design

See [`docs/ROADMAP.md`](docs/ROADMAP.md) (incl. the open-core boundary) and [`docs/SPEC.md`](docs/SPEC.md).

## Part of the COBOL Modernization Starters

- **[cobol-rest-bridge](https://github.com/makedirectory/cobol-rest-bridge)** — expose COBOL through REST
- **[cobol-migration-toolkit](https://github.com/makedirectory/cobol-migration-toolkit)** — inventory & dependency analysis (this repo)
- **[cobol-to-rust](https://github.com/makedirectory/cobol-to-rust)** — a COBOL-to-Rust transpiler scaffold

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities per [SECURITY.md](SECURITY.md).

## License & commercial support

Licensed under the [Apache License 2.0](LICENSE). © 2026 Make Directory Developers, LLC.

Need a full modernization assessment of your estate? Make Directory Developers offers mainframe & COBOL modernization services and **Cartograph**, an in-network assessment tier — [mk-dir.com](https://mk-dir.com) · andrew@mk-dir.com.
