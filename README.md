# COBOL Migration Toolkit

[![CI](https://github.com/makedirectory/cobol-migration-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/makedirectory/cobol-migration-toolkit/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

A dependency-analysis and documentation scaffold for COBOL modernization projects.

> **Open-core:** this repository is the free, Apache-2.0 discovery core. Deep grammar-based
> parsing, embedded SQL/CICS handling, AI documentation, SARIF/work-item export, and a hosted
> assessment dashboard are part of a commercial tier — see [`docs/ROADMAP.md`](docs/ROADMAP.md).

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
```

Generated files:

```text
build/inventory.json
build/report.md
build/dependencies.dot
```

Render the graph if Graphviz is installed:

```bash
dot -Tsvg build/dependencies.dot -o build/dependencies.svg
```

Run tests:

```bash
pytest
```

## What the scanner finds

- `PROGRAM-ID`
- `COPY` dependencies
- static `CALL` targets
- paragraph names
- source file sizes and line counts
- unresolved dependencies

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

Need a full modernization assessment of your estate? Make Directory Developers offers mainframe & COBOL modernization services and a hosted assessment tier — [mk-dir.com](https://mk-dir.com) · andrew@mk-dir.com.
