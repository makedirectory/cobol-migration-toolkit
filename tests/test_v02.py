from pathlib import Path

from cobol_migrate.analysis import build_inventory
from cobol_migrate.scanner import (
    detect_format,
    index_copybooks,
    normalize_source,
    scan_file,
    scan_tree,
)

FIXED_PROG = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. FIXEDPROG.
       PROCEDURE DIVISION.
           STOP RUN.
"""

FREE_DIRECTIVE = """\
       >>SOURCE FORMAT FREE
IDENTIFICATION DIVISION.
PROGRAM-ID. FREEPROG.
PROCEDURE DIVISION.
    DISPLAY "HI".  *> inline comment
    STOP RUN.
"""

FREE_HEURISTIC = """\
IDENTIFICATION DIVISION.
PROGRAM-ID. NOSEQ.
PROCEDURE DIVISION.
    DISPLAY "X".
    STOP RUN.
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_detect_fixed_vs_free():
    assert detect_format(FIXED_PROG) == "fixed"
    assert detect_format(FREE_DIRECTIVE) == "free"
    assert detect_format(FREE_HEURISTIC) == "free"


def test_free_format_program_id_and_inline_comment(tmp_path):
    unit = scan_file(_write(tmp_path / "free.cbl", FREE_DIRECTIVE), tmp_path)
    assert unit.source_format == "free"
    assert unit.program_id == "FREEPROG"


def test_fixed_continuation_is_merged():
    raw = (
        "       PROGRAM-ID. CONT.\n"
        "       PROCEDURE DIVISION.\n"
        '           DISPLAY "HELLO\n'
        '      -              "WORLD".\n'
        "           STOP RUN.\n"
    )
    norm = normalize_source(raw, "fixed")
    assert "WORLD" in norm
    # the continuation line must have been folded into the previous logical line
    assert not any(line.lstrip().startswith('"WORLD') for line in norm.splitlines())


def test_copy_replacing_flagged(tmp_path):
    raw = (
        "       PROGRAM-ID. REPL.\n"
        "       DATA DIVISION.\n"
        "       COPY TEMPLATE REPLACING ==:TAG:== BY ==WS==.\n"
        "       PROCEDURE DIVISION.\n"
        "           STOP RUN.\n"
    )
    unit = scan_file(_write(tmp_path / "repl.cbl", raw), tmp_path)
    assert "TEMPLATE" in unit.copybooks
    assert "TEMPLATE" in unit.copy_replacing


def test_copybook_resolution(tmp_path):
    src = tmp_path / "src"
    cpy = tmp_path / "copybooks"
    src.mkdir()
    cpy.mkdir()
    _write(
        src / "PROG.cbl",
        "       PROGRAM-ID. PROG.\n"
        "       DATA DIVISION.\n"
        "       COPY SHARED.\n"
        "       COPY MISSING.\n"
        "       PROCEDURE DIVISION.\n"
        '           CALL "OTHERPROG".\n'
        "           STOP RUN.\n",
    )
    _write(cpy / "SHARED.cpy", "       01 SHARED-REC PIC X(10).\n")

    units = scan_tree(src)
    index = index_copybooks([src, cpy])
    inventory = build_inventory(units, index)

    assert inventory["schema_version"] == 1
    assert inventory["unresolved"]["copybooks"] == ["MISSING"]
    assert "OTHERPROG" in inventory["unresolved"]["calls"]


def test_metrics_fan_in_and_orphans(tmp_path):
    _write(tmp_path / "A.cbl", '       PROGRAM-ID. A.\n       PROCEDURE DIVISION.\n           CALL "B".\n')
    _write(tmp_path / "B.cbl", "       PROGRAM-ID. B.\n       PROCEDURE DIVISION.\n           STOP RUN.\n")
    _write(tmp_path / "C.cbl", "       PROGRAM-ID. C.\n       PROCEDURE DIVISION.\n           STOP RUN.\n")

    inventory = build_inventory(scan_tree(tmp_path), {})
    metrics = inventory["metrics"]

    assert metrics["program_count"] == 3
    assert metrics["unreferenced_programs"] == ["A", "C"]
    assert metrics["max_fan_in"] == 1
