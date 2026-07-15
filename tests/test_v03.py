from pathlib import Path

from cobol_migrate.cli import resolve_formats, run_scan

PROG = """\
       PROGRAM-ID. PROG.
       DATA DIVISION.
       COPY MISSING.
       PROCEDURE DIVISION.
           CALL "OTHERPROG".
           STOP RUN.
"""


def _tree(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    (src / "PROG.cbl").write_text(PROG, encoding="utf-8")
    return src


def test_resolve_formats_defaults_to_all():
    assert resolve_formats(None) == ["json", "md", "dot", "html"]
    assert resolve_formats(["all"]) == ["json", "md", "dot", "html"]
    assert resolve_formats(["md", "html"]) == ["md", "html"]


def test_format_selection_only_writes_requested(tmp_path):
    out = tmp_path / "out"
    run_scan(_tree(tmp_path), out, [], ["md"], strict=False)
    assert (out / "report.md").exists()
    assert not (out / "inventory.json").exists()
    assert not (out / "report.html").exists()


def test_graph_split_writes_three_dot_files(tmp_path):
    out = tmp_path / "out"
    run_scan(_tree(tmp_path), out, [], ["dot"], strict=False)
    assert (out / "dependencies.dot").exists()
    assert (out / "calls.dot").exists()
    assert (out / "copybooks.dot").exists()
    # split views contain only their own edge kind
    assert "COPY" not in (out / "calls.dot").read_text()
    assert "CALL" not in (out / "copybooks.dot").read_text()


def test_html_report_is_self_contained(tmp_path):
    out = tmp_path / "out"
    run_scan(_tree(tmp_path), out, [], ["html"], strict=False)
    doc = (out / "report.html").read_text()
    assert doc.startswith("<!doctype html>")
    assert "<style>" in doc and "http://" not in doc and "https://" not in doc
    assert "OTHERPROG" in doc  # unresolved CALL surfaced


def test_strict_exit_code(tmp_path):
    src = _tree(tmp_path)
    out = tmp_path / "out"
    # PROG has an unresolved CALL and copybook → strict should fail
    assert run_scan(src, out, [], ["json"], strict=True) == 1
    assert run_scan(src, out, [], ["json"], strict=False) == 0
