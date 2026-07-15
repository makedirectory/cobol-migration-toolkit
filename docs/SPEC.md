# cobol-migration-toolkit — Technical Spec

## Purpose
Scan COBOL/copybook sources and produce a first-pass **inventory and dependency map** for
modernization discovery. Conservative by design; the OSS core is a discovery aid, not authoritative
semantics.

## Data model (`CobolUnit`, versioned schema — `schema_version: 1` since v0.2)
```
path, kind (program|copybook), source_format (fixed|free), program_id,
copybooks[], copy_replacing[], calls[], paragraphs[],
line_count, byte_count
```
`inventory.json` =
```
{ "schema_version": 1,
  "units": [CobolUnit...],
  "metrics": { unit_count, program_count, copybook_count, call_edges, copy_edges,
               unresolved_call_count, unresolved_copybook_count,
               unreferenced_programs[], unreferenced_copybooks[],
               copybooks_using_replacing[], max_fan_out, max_fan_in },
  "unresolved": { "copybooks": [...], "calls": [...] } }
```
Paid plugins extend the unit with `data_items[]`, `data_flow`, `complexity`, `summary`, etc.
— they must only **add** fields and bump `schema_version` for any breaking change.

## Pipeline
```
discover files (ext allowlist) → detect fixed/free → normalize (columns + continuations,
  drop *,/ comments) → regex extract → CobolUnit → resolve copybooks (--copybook-path)
  → aggregate metrics → render (json|md|dot; html in v0.3)
```

## OSS ↔ commercial boundary (v0.4 plugin architecture)
- Core exposes a Python **entry-point group**, e.g. `cobol_migrate.analyzers`.
- Each analyzer implements:
  ```python
  class Analyzer(Protocol):
      name: str
      def analyze(self, unit: CobolUnit, ctx: ScanContext) -> dict: ...  # merged into output
  ```
- If a paid package (e.g. `cobol-migrate-pro`) is installed, its analyzers auto-register; otherwise the
  core runs alone. **No core code changes, no relicensing** — the moat is the plugin, not the license.
- `cobol-migrate scan ... --analyzers all|<name>` selects which run.

## Config
- `--copybook-path` (repeatable), `--format`, `--output`, extension allowlist override.
- Search-path & dialect config file (`.cobolmigrate.toml`) from v0.2.

## Output formats
- `inventory.json` (machine, stable schema), `report.md`, `dependencies.dot`, `report.html` (v0.3).
- CI-friendly exit codes (v0.3): nonzero on unresolved deps if `--strict`.

## Accuracy & known limits (state these in every report header)
- Regex misses dynamic `CALL`, `COPY REPLACING`, embedded SQL/CICS, vendor extensions, generated code.
- Paragraph regex is heuristic (columns 1–11); free-format & continuations improve in v0.2.

## Testing strategy
- Fixture COBOL/copybooks with known expected inventory (golden JSON).
- Property tests on the normalizer (column stripping, comment handling).
- Schema-compat test: paid-plugin output must validate against the versioned core schema.

## Non-goals (OSS core)
Semantic correctness guarantees, AST-level parsing, LLM calls, hosted features — all reserved for
the commercial tier / SaaS.
