# Build Progress — cobol-migration-toolkit

**Last updated:** 2026-07-15 · **Mode:** Clean-slate (beta) · **Latest:** v0.5.0

> Tracks milestone **state** for this repo. For **how** we work (build cycle, review gate, layering,
> non-negotiables), see the shared **`PROCESS.md`** in the workspace root.
>
> **Legend:** ⬜ Not started · 🔄 In progress · ✅ Complete · ⚠️ Blocked · — N/A
> Columns follow the build cycle: **Impl · Tests · Docs · Reviewed** (PR + CI green).

## Current snapshot

The free open-core is at **v0.5.0** and functionally complete for first-pass discovery: fixed/free
format handling, copybook resolution, metrics, a versioned `inventory.json`, HTML/MD/DOT reports,
`--strict`, an analyzer **plugin architecture** (v0.4) that the paid Cartograph tier builds against,
and a `.cobolmigrate.toml` config (v0.5). CI runs ruff + mypy + pytest on Python 3.11/3.12.

### Active / next

| ID | Milestone | Impl | Tests | Docs | Reviewed | Status |
|----|-----------|:----:|:-----:|:----:|:--------:|:------:|
| v0.6 | Subsystem clustering, HTML embedded graph, `--fail-on` thresholds | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## Shipped

| ID | Milestone | Impl | Tests | Docs | Reviewed | Status |
|----|-----------|:----:|:-----:|:----:|:--------:|:------:|
| v0.1 | Regex scanner; JSON/MD/DOT output; CLI | ✅ | ✅ | ✅ | ✅ | ✅ |
| — | OSS scaffolding (Apache-2.0, CI, templates, docs) | ✅ | — | ✅ | ✅ | ✅ |
| v0.2 | Formats + continuations; copybook resolution; REPLACING; metrics; versioned schema | ✅ | ✅ | ✅ | ✅ #5 | ✅ |
| v0.3 | HTML report; `--format`; `--strict`; split call/copybook graphs | ✅ | ✅ | ✅ | ✅ #6 | ✅ |
| v0.4 | Analyzer plugin architecture (entry points); built-in reference analyzer | ✅ | ✅ | ✅ | ✅ #7 | ✅ |
| v0.4.1 | `ScanContext.read_source` for analyzer source access | ✅ | ✅ | ✅ | ✅ #8 | ✅ |
| v0.5 | `.cobolmigrate.toml` config (paths/formats/analyzers/extensions/output) | ✅ | ✅ | ✅ | ✅ #9 | ✅ |

### Milestone notes

> **2026-07-15 — v0.4: plugin architecture.**
> **Scope:** `cobol_migrate.analyzers` entry-point interface; `Analyzer` protocol + `ScanContext`;
> results merged into `units[i].analyses`; `--analyzers` selection; built-in `paragraph_count`.
> **Verification:** ruff + mypy clean; 18 tests; verified end-to-end with a real editable install so
> entry-point discovery fires. **Review:** PR #7, CI green (3.11/3.12). **Deferred:** subsystem clustering → v0.6.

> **2026-07-15 — v0.5: config file.**
> **Scope:** `config` module; auto-discovered `.cobolmigrate.toml` (or `--config`); CLI overrides file;
> unknown keys pass through to `ScanContext.options`. **Verification:** 25 tests; ruff + mypy clean;
> config-driven scan verified end-to-end. **Review:** PR #9, CI green. **Deferred:** none.

## Decision log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-07-15 | Pull versioned `inventory.json` schema forward to v0.2 | Give paid analyzers a stable contract early |
| 2026-07-15 | Pin `ruff==0.8.6` / `mypy==1.11.2` | CI drifted from local/pre-commit and broke `ruff format --check` |
| 2026-07-15 | `ScanContext.read_source` added in v0.4.1 | Real analyzers (e.g. Cartograph complexity) need source text |

---

*Companion: shared `PROCESS.md` (workspace root).*
