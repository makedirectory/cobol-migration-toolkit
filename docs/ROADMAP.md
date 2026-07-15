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

### v0.2 — trustworthy inventory
- Fixed-format column handling + continuation lines; free-format detection.
- Copybook resolution from configurable search paths (`--copybook-path`).
- `COPY ... REPLACING` awareness (at least flag it).
- Basic metrics: program count, fan-in/fan-out, orphan/unreferenced units.

### v0.3 — better graphs & UX
- Call graph vs copybook graph as separate views; clustering by subsystem.
- HTML report (self-contained) in addition to Markdown.
- `--format json|md|dot|html`, exit codes for CI use.

### v0.4 — plugin architecture (unlocks the paid tier)
- Define entry-point plugin interface so commercial analyzers load if installed (see SPEC).
- Stable `inventory.json` schema (versioned) that paid tools consume/extend.

---

## Commercial tier (paid — separate private packages)

- **Grammar-based parser** (ANTLR/tree-sitter) replacing regex → real ASTs, accurate paragraph/section
  boundaries, data definitions.
- **Data-flow analysis:** variable read/write tracking, record-layout docs, dead-code detection.
- **Dialect & preprocessor handling:** embedded SQL (DB2), CICS commands, vendor extensions.
- **Dynamic call resolution** and transaction-boundary detection.
- **LLM documentation adapter** (behind a clean interface): plain-English program/paragraph summaries.
- **Exports:** SARIF, OpenAPI candidate specs, and modernization **work items** (Jira/ADO).
- **Effort & complexity scoring:** estimate migration effort per program/subsystem.

## Hosted SaaS (paid — the assessment dashboard)
- Point at / upload an estate → shareable assessment report with graphs, metrics, risk & effort.
- Data-handling stance must be explicit (on-prem/self-host option for regulated buyers).
- The free CLI report is the lead; the hosted report is the sale.

## Content beats
- Publish dependency graphs of public COBOL corpora.
- "What a first-pass COBOL inventory actually tells you (and what it can't)."

## Explicit non-goals for the OSS core
- Guaranteeing semantic accuracy (regex is a discovery aid — say so loudly).
- Bundling the paid analyzers or LLM calls into the free package.
