# Contributing to COBOL Migration Toolkit

Thanks for your interest! This project is the open-source core of a COBOL
modernization discovery tool. The core stays free and permissively licensed;
deep-semantics, AI documentation, exports, and hosted features are part of a
separate commercial tier (see [docs/ROADMAP.md](docs/ROADMAP.md)).

Please also read the [Code of Conduct](CODE_OF_CONDUCT.md) and the
[spec](docs/SPEC.md) before large changes.

## Development setup

Requirements: Python 3.11+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

Run the scanner against the examples:

```bash
cobol-migrate scan examples --output build
```

## Before you open a PR

```bash
pytest -q                  # tests
ruff check .               # lint
ruff format --check .      # formatting
mypy src                   # type-check
```

Install `pre-commit install` to run lint/format automatically on commit.

## Guidelines

- Keep the OSS core an honest **discovery aid** — be explicit about accuracy limits.
- Do **not** add the commercial-tier features (grammar parser, embedded SQL/CICS,
  LLM docs, SARIF/work-item export, hosted features) to this repo — they load via
  the plugin interface described in `docs/SPEC.md`.
- Preserve backward compatibility of the `inventory.json` schema; bump
  `schema_version` for breaking changes.
- Add tests (golden fixtures) for any parsing/output change.

## Licensing of contributions

By submitting a contribution, you agree it is licensed under the project's
[Apache License 2.0](LICENSE).
