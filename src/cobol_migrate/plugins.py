"""Analyzer plugin interface.

The OSS core scans and inventories. Deeper analysis (grammar-based parsing, data-flow,
LLM documentation, effort scoring — the commercial "Cartograph" tier) plugs in here as
**analyzers**, discovered at runtime via the ``cobol_migrate.analyzers`` entry-point group.
If a commercial package is installed its analyzers register automatically; otherwise the
core runs with only its built-in reference analyzer. No core changes, no relicensing.

There are two kinds of analyzer:

- **unit analyzers** (``cobol_migrate.analyzers``) run per ``CobolUnit``; results merge into
  ``units[i].analyses``.
- **inventory analyzers** (``cobol_migrate.inventory_analyzers``) run once over the whole built
  inventory (so they can aggregate per-unit analyzer output); results land in top-level ``reports``.

An external package registers analyzers in its own ``pyproject.toml``::

    [project.entry-points."cobol_migrate.analyzers"]
    my_analyzer = "my_pkg.module:MyAnalyzer"

    [project.entry-points."cobol_migrate.inventory_analyzers"]
    my_rollup = "my_pkg.module:MyRollup"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from .scanner import CobolUnit, normalize_source

if TYPE_CHECKING:
    from .analysis import Inventory

ENTRY_POINT_GROUP = "cobol_migrate.analyzers"
INVENTORY_ENTRY_POINT_GROUP = "cobol_migrate.inventory_analyzers"

# {unit path: {analyzer name: result dict}}
AnalysisResults = dict[str, dict[str, dict[str, object]]]


@runtime_checkable
class _Named(Protocol):
    name: str


_A = TypeVar("_A", bound=_Named)


@dataclass
class ScanContext:
    """Read-only context handed to every analyzer.

    ``root`` is the scanned source tree; analyzers that need the raw text (e.g. a
    grammar-based or complexity analyzer) read it via :meth:`read_source`.
    """

    units: list[CobolUnit]
    copybook_index: dict[str, str]
    root: Path | None = None
    options: dict[str, object] = field(default_factory=dict)

    def read_source(self, unit: CobolUnit, *, normalized: bool = False) -> str:
        """Return the source of ``unit`` (raw, or column/comment-normalized)."""
        if self.root is None:
            raise ValueError("ScanContext.root is not set; cannot read unit source")
        raw = (self.root / unit.path).read_text(encoding="utf-8", errors="replace")
        return normalize_source(raw, unit.source_format) if normalized else raw


@runtime_checkable
class Analyzer(Protocol):
    name: str

    def analyze(self, unit: CobolUnit, ctx: ScanContext) -> dict[str, object]:
        """Return extra facts about ``unit``; merged into the unit's inventory entry."""
        ...


class ParagraphCountAnalyzer:
    """Built-in reference analyzer — a minimal, obviously-free example of the contract."""

    name = "paragraph_count"

    def analyze(self, unit: CobolUnit, ctx: ScanContext) -> dict[str, object]:
        return {"count": len(unit.paragraphs)}


BUILTIN_ANALYZERS: list[Analyzer] = [ParagraphCountAnalyzer()]


def discover_analyzers() -> list[Analyzer]:
    """Built-in analyzers plus any registered via the entry-point group, sorted by name."""
    found: list[Analyzer] = list(BUILTIN_ANALYZERS)
    seen = {a.name for a in found}
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        try:
            obj = ep.load()
            instance = obj() if isinstance(obj, type) else obj
        except Exception as exc:  # defensive: a broken plugin must not abort a scan
            print(f"warning: failed to load analyzer '{ep.name}': {exc}", file=sys.stderr)
            continue
        if instance.name not in seen:
            seen.add(instance.name)
            found.append(instance)
    return sorted(found, key=lambda a: a.name)


def select_analyzers(analyzers: list[_A], selected: list[str] | None) -> list[_A]:
    """Filter analyzers by name; works for both unit and inventory analyzers.

    ``None``/``all`` selects everything; ``none`` selects nothing; otherwise by name.
    """
    if selected == ["none"]:
        return []
    if not selected or "all" in selected:
        return analyzers
    return [a for a in analyzers if a.name in selected]


def run_analyzers(analyzers: list[Analyzer], ctx: ScanContext) -> AnalysisResults:
    results: AnalysisResults = {}
    for unit in ctx.units:
        for analyzer in analyzers:
            try:
                out = analyzer.analyze(unit, ctx)
            except Exception as exc:  # a plugin failing on one unit must not abort the scan
                print(
                    f"warning: analyzer '{analyzer.name}' failed on {unit.path}: {exc}",
                    file=sys.stderr,
                )
                continue
            if out:
                results.setdefault(unit.path, {})[analyzer.name] = out
    return results


@runtime_checkable
class InventoryAnalyzer(Protocol):
    name: str

    def analyze(self, inventory: Inventory, ctx: ScanContext) -> dict[str, object]:
        """Return an estate-level report over the whole inventory; lands in ``reports[name]``."""
        ...


def discover_inventory_analyzers() -> list[InventoryAnalyzer]:
    """Inventory analyzers registered via the entry-point group, sorted by name (none built in)."""
    found: list[InventoryAnalyzer] = []
    seen: set[str] = set()
    for ep in entry_points(group=INVENTORY_ENTRY_POINT_GROUP):
        try:
            obj = ep.load()
            instance = obj() if isinstance(obj, type) else obj
        except Exception as exc:  # defensive: a broken plugin must not abort a scan
            print(f"warning: failed to load inventory analyzer '{ep.name}': {exc}", file=sys.stderr)
            continue
        if instance.name not in seen:
            seen.add(instance.name)
            found.append(instance)
    return sorted(found, key=lambda a: a.name)


def run_inventory_analyzers(
    analyzers: list[InventoryAnalyzer], inventory: Inventory, ctx: ScanContext
) -> dict[str, dict[str, object]]:
    reports: dict[str, dict[str, object]] = {}
    for analyzer in analyzers:
        try:
            out = analyzer.analyze(inventory, ctx)
        except Exception as exc:  # a plugin failing must not abort the scan
            print(f"warning: inventory analyzer '{analyzer.name}' failed: {exc}", file=sys.stderr)
            continue
        if out:
            reports[analyzer.name] = out
    return reports
