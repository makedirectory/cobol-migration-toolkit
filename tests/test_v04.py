from pathlib import Path

from cobol_migrate.analysis import build_inventory
from cobol_migrate.plugins import (
    BUILTIN_ANALYZERS,
    ParagraphCountAnalyzer,
    ScanContext,
    discover_analyzers,
    run_analyzers,
    select_analyzers,
)
from cobol_migrate.scanner import CobolUnit, scan_tree

PROG = """\
       PROGRAM-ID. PROG.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY "HI".
       SECOND-PARA.
           STOP RUN.
"""


class _TagAnalyzer:
    name = "tag"

    def analyze(self, unit, ctx):
        return {"tagged": True}


class _BoomAnalyzer:
    name = "boom"

    def analyze(self, unit, ctx):
        raise RuntimeError("nope")


def _units(tmp_path: Path) -> list[CobolUnit]:
    (tmp_path / "PROG.cbl").write_text(PROG, encoding="utf-8")
    return scan_tree(tmp_path)


def test_builtin_paragraph_count(tmp_path):
    units = _units(tmp_path)
    ctx = ScanContext(units=units, copybook_index={})
    results = run_analyzers([ParagraphCountAnalyzer()], ctx)
    assert results[units[0].path]["paragraph_count"] == {"count": 2}


def test_discover_includes_builtin():
    names = [a.name for a in discover_analyzers()]
    assert "paragraph_count" in names
    # discovery is stable/sorted and includes every built-in
    assert names == sorted(names)
    for builtin in BUILTIN_ANALYZERS:
        assert builtin.name in names


def test_select_analyzers():
    analyzers = [ParagraphCountAnalyzer(), _TagAnalyzer()]
    assert [a.name for a in select_analyzers(analyzers, None)] == ["paragraph_count", "tag"]
    assert select_analyzers(analyzers, ["none"]) == []
    assert [a.name for a in select_analyzers(analyzers, ["tag"])] == ["tag"]


def test_failing_analyzer_does_not_abort(tmp_path, capsys):
    units = _units(tmp_path)
    ctx = ScanContext(units=units, copybook_index={})
    results = run_analyzers([_BoomAnalyzer(), _TagAnalyzer()], ctx)
    # the good analyzer still produced output; the bad one warned and was skipped
    assert results[units[0].path] == {"tag": {"tagged": True}}
    assert "analyzer 'boom' failed" in capsys.readouterr().err


def test_analyses_merged_into_inventory(tmp_path):
    units = _units(tmp_path)
    ctx = ScanContext(units=units, copybook_index={})
    analyses = run_analyzers([_TagAnalyzer()], ctx)
    inventory = build_inventory(units, {}, analyses, ["tag"])
    assert inventory["analyzers"] == ["tag"]
    assert inventory["units"][0]["analyses"] == {"tag": {"tagged": True}}


def test_inventory_without_analyzers_omits_key(tmp_path):
    units = _units(tmp_path)
    inventory = build_inventory(units, {})
    assert inventory["analyzers"] == []
    assert "analyses" not in inventory["units"][0]


def test_scancontext_read_source(tmp_path):
    units = _units(tmp_path)
    ctx = ScanContext(units=units, copybook_index={}, root=tmp_path)
    raw = ctx.read_source(units[0])
    assert "PROGRAM-ID. PROG." in raw
    # normalized form strips the fixed-format sequence/indicator columns
    assert "MAIN-PARA." in ctx.read_source(units[0], normalized=True)


def test_scancontext_read_source_requires_root(tmp_path):
    units = _units(tmp_path)
    ctx = ScanContext(units=units, copybook_index={})
    try:
        ctx.read_source(units[0])
    except ValueError as exc:
        assert "root is not set" in str(exc)
    else:
        raise AssertionError("expected ValueError when root is unset")
