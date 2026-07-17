# cobol-migration-toolkit — Roadmap

**Funnel role:** THIS is the product / bottom of funnel (see `../../STRATEGY.md`).
**Model:** open-core. Free OSS core drives adoption; paid tier + hosted SaaS make money.
**License:** Apache-2.0 core; commercial features ship as separate private plugins.

The guiding boundary: **inventory & discovery = free. Deep semantics, AI docs, exports, and hosting = paid.**

---

## OSS core (free — build these in this repo)

### v0.1 — current
- Regex scanner: `PROGRAM-ID`, `COPY`, static `CALL`, paragraphs, line/byte counts, unresolved deps.
- Emits `inventory.json`, `report.md`, `dependencies.dot`. CLI `cobol-migrate scan`.

### v0.2 — trustworthy inventory ✅ (shipped)
- ✅ Fixed-format column handling + continuation lines; free-format detection.
- ✅ Copybook resolution from configurable search paths (`--copybook-path`).
- ✅ `COPY ... REPLACING` awareness (captured and flagged for manual review).
- ✅ Basic metrics: program/copybook counts, fan-in/fan-out, unreferenced units.
- ✅ Versioned `inventory.json` schema (`schema_version: 1`) — pulled forward from v0.4.

### v0.3 — better graphs & UX ✅ (shipped)
- ✅ Call graph vs copybook graph as separate views (`calls.dot`, `copybooks.dot` + combined).
- ✅ Self-contained HTML report (stat tiles + unit table) in addition to Markdown.
- ✅ `--format {json,md,dot,html,all}` selection; `--strict` non-zero exit for CI use.
- ⏭ Clustering by subsystem deferred (needs a subsystem/ownership heuristic) — revisit post-v0.4.

### v0.4 — plugin architecture ✅ (shipped) — unlocks the paid tier
- ✅ `cobol_migrate.analyzers` entry-point interface: installed packages' analyzers auto-register.
- ✅ `Analyzer` protocol + `ScanContext`; results merged into `units[i].analyses`; `--analyzers` selection.
- ✅ Built-in reference analyzer (`paragraph_count`) as a template; failing plugins are isolated.
- ✅ Stable, versioned `inventory.json` schema that paid tools consume/extend (landed in v0.2).
- ➡️ **Cartograph** analyzers (grammar parser, data-flow, embedded SQL/CICS, LLM docs, exports)
  now build as separate private packages against this interface — no further core changes needed.
- ✅ v0.4.1 — `ScanContext.read_source` so analyzers can access unit source text.

### v0.5 — config file ✅ (shipped)
- ✅ `.cobolmigrate.toml` (auto-discovered or `--config`): copybook paths, formats, strict,
  analyzers, extension allowlist override, output. CLI flags override the file.
- ✅ Unknown keys (e.g. `dialect`) pass through to analyzers via `ScanContext.options`.

### v0.6 — graphs & gating ✅ (shipped)
- ✅ Subsystem clustering in DOT graphs (by top-level directory).
- ✅ Embedded dependency graph in the HTML report (inline SVG via Graphviz if present, else DOT source — stays self-contained).
- ✅ `--fail-on METRIC[:MAX]` (repeatable) metric-threshold gating for CI; also a `fail_on` config key.

### v0.7 — inventory analyzers ✅ (shipped)
- ✅ Second plugin type: **inventory analyzers** (`cobol_migrate.inventory_analyzers`) run once over
  the built inventory (so they can aggregate per-unit analyzer output); results land in top-level
  `reports`. Enables estate-level rollups (e.g. Cartograph's effort rollup) with no further core changes.
- ✅ `reports` surfaced in the Markdown and HTML reports; `--analyzers` selects both plugin types.

### v0.8 — schema & filter ✅ (shipped)
- ✅ Published `inventory.json` **JSON Schema** (draft 2020-12) via `cobol-migrate schema`; validated in tests.
- ✅ **Filterable** unit table in the HTML report (inline JS, still self-contained).

### v0.9 — next
- Incremental/cached scans (skip unchanged files by mtime/hash); subsystem clustering in HTML.

---

## Commercial tier — "Cartograph" (paid — separate private packages)
_Working name; pending trademark clearance. Chosen over "Estate" (too generic)._

- **Grammar-based parser** (ANTLR/tree-sitter) replacing regex → real ASTs, accurate paragraph/section
  boundaries, data definitions.
- **Data-flow analysis:** variable read/write tracking, record-layout docs, dead-code detection.
- **Dialect & preprocessor handling:** embedded SQL (DB2), CICS commands, vendor extensions.
- **Dynamic call resolution** and transaction-boundary detection.
- **LLM documentation adapter** (behind a clean interface): plain-English program/paragraph summaries.
- **Exports:** SARIF, OpenAPI candidate specs, and modernization **work items** (Jira/ADO).
- **Effort & complexity scoring:** estimate migration effort per program/subsystem.

## Cartograph dashboard (paid — deployed in-network, not a multi-tenant SaaS)
- Point at an estate **inside the customer's network** → shareable assessment report with graphs,
  metrics, risk & effort. Ships as a container/Helm deployable; air-gap capable.
- **Local-first, source never leaves** — see [`DATA-HANDLING.md`](DATA-HANDLING.md). This is a product
  principle, not a footnote; it's what lets regulated buyers adopt the free CLI in the first place.
- LLM features default to customer-hosted models (no third-party API by default).
- The free CLI report is the lead; the deployed Cartograph report is the sale.

## Content beats
- Publish dependency graphs of public COBOL corpora.
- "What a first-pass COBOL inventory actually tells you (and what it can't)."

## Explicit non-goals for the OSS core
- Guaranteeing semantic accuracy (regex is a discovery aid — say so loudly).
- Bundling the paid analyzers or LLM calls into the free package.
