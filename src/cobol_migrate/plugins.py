"""Analyzer plugin interface.

The OSS core scans and inventories. Deeper analysis (grammar-based parsing, data-flow,
LLM documentation, effort scoring — the commercial "Cartograph" tier) plugs in here as
**analyzers**, discovered at runtime via the ``cobol_migrate.analyzers`` entry-point group.
If a commercial package is installed its analyzers register automatically; otherwise the
core runs with only its built-in reference analyzer. No core changes, no relicensing.

An external package registers analyzers in its own ``pyproject.toml``::

    [project.entry-points."cobol_migrate.analyzers"]
    my_analyzer = "my_pkg.module:MyAnalyzer"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from .scanner import CobolUnit

ENTRY_POINT_GROUP = "cobol_migrate.analyzers"

# {unit path: {analyzer name: result dict}}
AnalysisResults = dict[str, dict[str, dict[str, object]]]


@dataclass
class ScanContext:
    """Read-only context handed to every analyzer."""

    units: list[CobolUnit]
    copybook_index: dict[str, str]
    options: dict[str, object] = field(default_factory=dict)


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


def select_analyzers(analyzers: list[Analyzer], selected: list[str] | None) -> list[Analyzer]:
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
