# COBOL Migration Toolkit

A dependency-analysis and documentation scaffold for COBOL modernization projects.

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
