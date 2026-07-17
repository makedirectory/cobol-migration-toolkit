from pathlib import Path

from cobol_migrate.analysis import build_inventory
from cobol_migrate.cli import run_scan
from cobol_migrate.plugins import (
    ScanContext,
    discover_inventory_analyzers,
    run_inventory_analyzers,
    select_analyzers,
)
from cobol_migrate.scanner import scan_tree

PROG = """\
       PROGRAM-ID. P.
       PROCEDURE DIVISION.
           STOP RUN.
"""


class _Rollup:
    """A test inventory analyzer: counts programs across the whole inventory."""

    name = "rollup"

    def analyze(self, inventory, ctx):
        programs = [u for u in inventory["units"] if u["kind"] == "program"]
        return {"program_count": len(programs)}


class _Empty:
    name = "empty"

    def analyze(self, inventory, ctx):
        return {}


def _inv(tmp_path: Path):
    (tmp_path / "P.cbl").write_text(PROG, encoding="utf-8")
    units = scan_tree(tmp_path)
    inventory = build_inventory(units, {})
    return units, inventory, ScanContext(units=units, copybook_index={}, root=tmp_path)


def test_reports_key_defaults_empty(tmp_path):
    _, inventory, _ = _inv(tmp_path)
    assert inventory["reports"] == {}


def test_run_inventory_analyzers_merges_reports(tmp_path):
    _, inventory, ctx = _inv(tmp_path)
    reports = run_inventory_analyzers([_Rollup(), _Empty()], inventory, ctx)
    assert reports == {"rollup": {"program_count": 1}}  # empty result is not recorded


def test_select_works_for_inventory_analyzers():
    analyzers = [_Rollup(), _Empty()]
    assert select_analyzers(analyzers, ["none"]) == []
    assert [a.name for a in select_analyzers(analyzers, None)] == ["rollup", "empty"]
    assert [a.name for a in select_analyzers(analyzers, ["rollup"])] == ["rollup"]


def test_discover_inventory_analyzers_does_not_crash():
    # No inventory analyzers ship in the core; discovery must return a (possibly empty) list.
    assert isinstance(discover_inventory_analyzers(), list)


def test_run_scan_attaches_reports_key(tmp_path):
    (tmp_path / "P.cbl").write_text(PROG, encoding="utf-8")
    out = tmp_path / "out"
    assert run_scan(tmp_path, out, [], ["json"], strict=False) == 0
    import json

    data = json.loads((out / "inventory.json").read_text())
    assert data["reports"] == {}  # no inventory analyzers installed in the core
