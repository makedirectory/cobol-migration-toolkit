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
  "analyzers": [ "<unit-analyzer name>", ... ],
  "units": [CobolUnit... (+ optional "analyses": { "<name>": {...} })],
  "metrics": { unit_count, program_count, copybook_count, call_edges, copy_edges,
               unresolved_call_count, unresolved_copybook_count,
               unreferenced_programs[], unreferenced_copybooks[],
               copybooks_using_replacing[], max_fan_out, max_fan_in },
  "unresolved": { "copybooks": [...], "calls": [...] },
  "reports": { "<inventory-analyzer name>": {...} } }
```
Paid plugins extend the unit with `data_items[]`, `data_flow`, `complexity`, `summary`, etc.
— they must only **add** fields and bump `schema_version` for any breaking change.

## Pipeline
```
discover files (ext allowlist) → detect fixed/free → normalize (columns + continuations,
  drop *,/ comments) → regex extract → CobolUnit → resolve copybooks (--copybook-path)
  → aggregate metrics → render (json|md|dot|html, selectable via --format)
```
`--strict` returns a non-zero exit code when any CALL or copybook dependency is unresolved, and
`--fail-on METRIC[:MAX]` (repeatable; also a `fail_on` config key) fails when any metric exceeds a
threshold (default 0; list metrics compare their length) — so a scan can gate CI. DOT output is
emitted as a combined graph plus separate call-only and copybook-only views, with source-unit nodes
**clustered by subsystem** (top-level directory). The HTML report embeds the dependency graph as an
inline SVG when Graphviz (`dot`) is available, falling back to embedded DOT source — always
self-contained (no external assets).

## OSS ↔ commercial boundary (plugin architecture — shipped in v0.4)
- Core exposes the entry-point group **`cobol_migrate.analyzers`** (see `plugins.py`).
- Each analyzer implements:
  ```python
  class Analyzer(Protocol):
      name: str
      def analyze(self, unit: CobolUnit, ctx: ScanContext) -> dict[str, object]: ...
  ```
  `ScanContext` carries `units`, `copybook_index`, `root`, and `options`, plus
  `read_source(unit, normalized=?)` for analyzers that need the raw/normalized text. An analyzer's non-empty
  return value is merged into that unit's inventory entry under `units[i].analyses[<name>]`;
  the top-level `analyzers` list records which ran.
- `discover_analyzers()` returns the built-in reference analyzer (`paragraph_count`) plus any
  registered by installed packages. A commercial package registers its own analyzers:
  ```toml
  [project.entry-points."cobol_migrate.analyzers"]
  my_analyzer = "my_pkg.module:MyAnalyzer"
  ```
- **Inventory analyzers** (v0.7) are a second plugin type via the `cobol_migrate.inventory_analyzers`
  group. They run once over the built inventory — so they can aggregate per-unit analyzer output — and
  their result lands in top-level `reports[<name>]`:
  ```python
  class InventoryAnalyzer(Protocol):
      name: str
      def analyze(self, inventory: Inventory, ctx: ScanContext) -> dict[str, object]: ...
  ```
  Ordering: per-unit analyzers run first, then inventory analyzers see the merged `units[i].analyses`.
- If a paid package (e.g. Cartograph) is installed its analyzers auto-register; otherwise the
  core runs with only its built-in. **No core changes, no relicensing** — the moat is the plugin.
- `cobol-migrate scan ... --analyzers {all,none,<name>}` (repeatable) selects which run.
- A failing plugin warns to stderr and is skipped; it never aborts a scan.

## Config
- Flags: `--copybook-path` (repeatable), `--format`, `--output`, `--strict`, `--analyzers`, `--config`.
- `.cobolmigrate.toml` (v0.5): auto-discovered in the source dir or cwd, or via `--config`. Keys:
  `copybook_paths`, `format`, `strict`, `analyzers`, `extensions` (allowlist override), `output`.
  Precedence: **CLI flags override the file; the file overrides built-in defaults.** Config-relative
  `copybook_paths` resolve against the config file's directory. Unknown keys (e.g. `dialect`) pass
  through to analyzers via `ScanContext.options`.

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
