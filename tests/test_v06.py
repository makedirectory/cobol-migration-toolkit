from pathlib import Path

from cobol_migrate.analysis import build_inventory
from cobol_migrate.cli import evaluate_fail_on, run_scan
from cobol_migrate.report import _subsystem, write_dot, write_html
from cobol_migrate.scanner import scan_tree

PROG = """\
       PROGRAM-ID. {name}.
       DATA DIVISION.
       COPY MISSING.
       PROCEDURE DIVISION.
           CALL "OTHERPROG".
           STOP RUN.
"""


def _estate(tmp_path: Path) -> Path:
    # two subsystems (directories) + one unresolved call and copybook
    for sub, name in [("billing", "BILL"), ("accounts", "ACCT")]:
        d = tmp_path / sub
        d.mkdir()
        (d / f"{name}.cbl").write_text(PROG.format(name=name), encoding="utf-8")
    return tmp_path


def test_subsystem_helper():
    assert _subsystem("billing/prog.cbl") == "billing"
    assert _subsystem("prog.cbl") == ""


def test_dot_clusters_by_subsystem(tmp_path):
    units = scan_tree(_estate(tmp_path))
    inv = build_inventory(units, {})
    out = tmp_path / "out"
    write_dot(units, inv, out)
    dot = (out / "dependencies.dot").read_text()
    assert 'subgraph "cluster_billing"' in dot
    assert 'subgraph "cluster_accounts"' in dot
    assert 'label="billing"' in dot


def test_html_embeds_graph_section(tmp_path):
    units = scan_tree(_estate(tmp_path))
    inv = build_inventory(units, {})
    out = tmp_path / "out"
    write_html(units, inv, out)
    doc = (out / "report.html").read_text()
    assert "Dependency graph" in doc
    # self-contained: no external asset references
    assert "http://" not in doc and "https://" not in doc


def test_evaluate_fail_on(tmp_path):
    units = scan_tree(_estate(tmp_path))
    inv = build_inventory(units, {})
    metrics = inv["metrics"]
    # 2 unresolved calls (OTHERPROG once per program → deduped to 1) and 2 unresolved copybooks (MISSING → 1)
    assert evaluate_fail_on(metrics, ["unresolved_call_count"]) == ["unresolved_call_count=1 exceeds 0"]
    assert evaluate_fail_on(metrics, ["unresolved_call_count:5"]) == []  # under threshold
    assert evaluate_fail_on(metrics, ["unreferenced_programs"])  # list metric → length compared
    assert evaluate_fail_on(metrics, ["bogus_metric"]) == ["--fail-on 'bogus_metric': unknown metric"]


def test_run_scan_fail_on_exit_code(tmp_path):
    src = _estate(tmp_path)
    out = tmp_path / "out"
    assert run_scan(src, out, [], ["json"], strict=False, fail_on=["unresolved_call_count"]) == 1
    assert run_scan(src, out, [], ["json"], strict=False, fail_on=["unresolved_call_count:5"]) == 0
